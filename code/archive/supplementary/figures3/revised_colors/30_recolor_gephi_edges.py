"""Recolour Figure 1c edges in the saved Gephi project and source tables.

The graph layout, nodes, edge weights and all non-colour fields are retained.
Run from any directory with: python recolor_gephi_edges.py
"""

from __future__ import annotations

import bisect
import csv
import json
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent
PROJECT_IN = SOURCE / "sdg-制作.gephi"
PROJECT_OUT = OUT / "sdg-制作_颜色休整后.gephi"
CSV_IN = SOURCE / "gephi_edges.csv"
CSV_OUT = OUT / "gephi_edges_颜色休整后.csv"
GEXF_IN = SOURCE / "figure1c_pooled_union.gexf"
GEXF_OUT = OUT / "figure1c_pooled_union_颜色休整后.gexf"

# Exact hexadecimal swatches in figure1a/figure1a_sdg_target_ring.py.
NSF_DARK = "#003366"
NSF_MID = "#7F99B2"
NSFC_DARK = "#8B0000"
NSFC_MID = "#C57F7F"
GRAY = "#CBD2D8"

BASE_NS = "http://www.gexf.net/1.2draft"
VIZ_NS = "http://www.gexf.net/1.2draft/viz"
ET.register_namespace("", BASE_NS)
ET.register_namespace("viz", VIZ_NS)
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def edge_style(row: dict[str, str]) -> tuple[str, float, str]:
    category = row["stability_class"]
    if category == "Not retained":
        return GRAY, 0.16, "background"
    if category == "NSF-specific":
        assert row["stable_nsf"] == "True" and row["stable_nsfc"] == "False"
        return NSF_DARK, 0.88, "NSF-specific"
    if category == "NSFC-specific":
        assert row["stable_nsf"] == "False" and row["stable_nsfc"] == "True"
        return NSFC_DARK, 0.88, "NSFC-specific"
    if category == "Other stable":
        if row["stable_nsf"] == "True" and row["stable_nsfc"] == "False":
            return NSF_MID, 0.62, "Other stable: NSF"
        if row["stable_nsf"] == "False" and row["stable_nsfc"] == "True":
            return NSFC_MID, 0.62, "Other stable: NSFC"
        raise ValueError(f"Ambiguous stable flag for {row['edge_id']}")
    if category == "Shared":
        assert row["stable_nsf"] == "True" and row["stable_nsfc"] == "True"
        if float(row["strength_nsf"]) >= float(row["strength_nsfc"]):
            return NSF_DARK, 0.88, "Shared: NSF stronger"
        return NSFC_DARK, 0.88, "Shared: NSFC stronger"
    raise ValueError(f"Unknown stability class: {category}")


def argb(color: str, alpha: float) -> int:
    a = round(255 * alpha)
    unsigned = (a << 24) | int(color[1:], 16)
    return unsigned - (1 << 32) if unsigned >= (1 << 31) else unsigned


def packed_int(value: int) -> bytes:
    tag = 15 if value < 0 else 16  # GraphStore INTEGER_PACK_NEG / INTEGER_PACK.
    value = abs(value)
    out = bytearray([tag])
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def unpack_int(buf: bytes, start: int) -> tuple[int, int]:
    tag = buf[start]
    if tag not in (15, 16):
        raise ValueError(f"Unexpected GraphStore integer marker at {start}: {tag}")
    value = shift = 0
    pos = start + 1
    while True:
        byte = buf[pos]
        pos += 1
        value |= (byte & 127) << shift
        if not byte & 128:
            break
        shift += 7
    return (-value if tag == 15 else value), pos


def load_rows() -> tuple[list[str], list[dict[str, str]], dict[str, dict[str, str]]]:
    with CSV_IN.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    assert len(rows) == 803
    assert Counter(r["stability_class"] for r in rows) == {
        "Not retained": 741,
        "Shared": 22,
        "Other stable": 19,
        "NSF-specific": 12,
        "NSFC-specific": 9,
    }
    return fieldnames, rows, {r["edge_id"]: r for r in rows}


def write_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            updated = dict(row)
            color, alpha, _ = edge_style(row)
            updated["edge_color"] = color
            updated["edge_alpha"] = str(alpha)
            writer.writerow(updated)
    shutil.copy2(SOURCE / "gephi_nodes.csv", OUT / "gephi_nodes.csv")


def write_gexf(by_id: dict[str, dict[str, str]]) -> None:
    tree = ET.parse(GEXF_IN)
    seen = set()
    for edge in tree.findall(f".//{{{BASE_NS}}}edge"):
        edge_id = edge.attrib["id"]
        row = by_id[edge_id]
        color, alpha, _ = edge_style(row)
        viz = edge.find(f"{{{VIZ_NS}}}color")
        assert viz is not None
        rgb = bytes.fromhex(color[1:])
        viz.attrib.update(r=str(rgb[0]), g=str(rgb[1]), b=str(rgb[2]), a=str(alpha))
        values = {a.attrib["for"]: a for a in edge.findall(f".//{{{BASE_NS}}}attvalue")}
        assert values["27"].attrib["value"] == row["edge_color"]
        assert float(values["28"].attrib["value"]) == float(row["edge_alpha"])
        values["27"].set("value", color)
        values["28"].set("value", str(alpha))
        seen.add(edge_id)
    assert seen == set(by_id)
    tree.write(GEXF_OUT, encoding="utf-8", xml_declaration=True)


def patch_graphstore(data: bytes, by_id: dict[str, dict[str, str]]) -> bytes:
    # Each edge stores adjacent presence_color and edge_color strings, followed
    # by edge_alpha, then a 0xD7 edge-properties marker and packed ARGB int.
    pattern = re.compile(rb"\x67\x07(#[0-9A-F]{6})\x67\x07(#[0-9A-F]{6})\x34(.{8})\xd7", re.S)
    matches = list(pattern.finditer(data))
    ids = list(re.finditer(rb"\x67\x05(e\d{4})", data))
    positions = [m.start() for m in ids]
    assert len(matches) == len(by_id) == 803
    edits: list[tuple[int, int, bytes]] = []
    seen = set()
    for match in matches:
        id_index = bisect.bisect_left(positions, match.start()) - 1
        edge_id = ids[id_index].group(1).decode("ascii")
        assert edge_id not in seen
        row = by_id[edge_id]
        assert match.group(1).decode() == row["presence_color"]
        assert match.group(2).decode() == row["edge_color"]
        assert struct.unpack(">d", match.group(3))[0] == float(row["edge_alpha"])
        color, alpha, _ = edge_style(row)
        old_int, end = unpack_int(data, match.end())
        # All source GraphStore visuals were opaque-ish class swatches, unlike
        # their attributes. Verify they have 0xEB alpha before replacing them.
        assert ((old_int & 0xFFFFFFFF) >> 24) == 0xEB
        edits.append((match.start(2), match.end(2), color.encode("ascii")))
        edits.append((match.end(), end, packed_int(argb(color, alpha))))
        seen.add(edge_id)
    assert seen == set(by_id)
    result = bytearray(data)
    for start, end, replacement in sorted(edits, reverse=True):
        result[start:end] = replacement
    return bytes(result)


def patch_appearance(data: bytes) -> bytes:
    root = ET.fromstring(data)
    partitions = root.find("./partitions[@for='edge']")
    assert partitions is not None
    color_part = partitions.find("./partition[@column='27']")
    class_part = partitions.find("./partition[@column='23']")
    assert color_part is not None and class_part is not None
    color_part[:] = []
    for color, alpha in (
        (GRAY, 0.16),
        (NSF_DARK, 0.88),
        (NSFC_DARK, 0.88),
        (NSF_MID, 0.62),
        (NSFC_MID, 0.62),
    ):
        ET.SubElement(color_part, "color", {"for": color, "rgba": str(argb(color, alpha))})
    # A single Gephi class swatch cannot express an NSF/NSFC split. Provide a
    # muted midpoint for these two fallback class swatches; edge_color is the
    # accurate partition and per-edge colours above are the saved visual state.
    midpoint = "#A28C99"
    class_colors = {
        "Not retained": (GRAY, 0.16),
        "NSF-specific": (NSF_DARK, 0.88),
        "NSFC-specific": (NSFC_DARK, 0.88),
        "Shared": (midpoint, 0.88),
        "Other stable": (midpoint, 0.62),
    }
    class_part[:] = []
    for name, (color, alpha) in class_colors.items():
        ET.SubElement(class_part, "color", {"for": name, "rgba": str(argb(color, alpha))})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_project(by_id: dict[str, dict[str, str]]) -> None:
    with zipfile.ZipFile(PROJECT_IN) as source, zipfile.ZipFile(PROJECT_OUT, "w") as target:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "Workspace_1_graphstore_bytes":
                data = patch_graphstore(data, by_id)
            elif entry.filename == "Workspace_1_appearancemodel_xml":
                data = patch_appearance(data)
            target.writestr(entry, data)


def main() -> None:
    fieldnames, rows, by_id = load_rows()
    write_csv(fieldnames, rows)
    write_gexf(by_id)
    write_project(by_id)
    counts = Counter(edge_style(row)[2] for row in rows)
    with zipfile.ZipFile(PROJECT_OUT) as project:
        assert project.testzip() is None
        assert len(project.namelist()) == 13
    report = {
        "source_project": str(PROJECT_IN),
        "output_project": str(PROJECT_OUT),
        "nodes": 121,
        "edges": len(rows),
        "edge_groups": dict(sorted(counts.items())),
        "colors": {
            "background": [GRAY, 0.16],
            "NSF dark": [NSF_DARK, 0.88],
            "NSFC dark": [NSFC_DARK, 0.88],
            "NSF mid": [NSF_MID, 0.62],
            "NSFC mid": [NSFC_MID, 0.62],
        },
        "shared_rule": "Dark hue follows the larger of strength_nsf and strength_nsfc; original class retained.",
        "other_stable_rule": "Mid hue follows the sole True stable flag.",
    }
    (OUT / "配色复核.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
