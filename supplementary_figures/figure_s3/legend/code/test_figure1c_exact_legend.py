from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures'
DATA_DIR = ROOT / 'data'
SOURCE_DIR = ROOT.parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    expected_figures = [
        "Figure1c_legend_exact_white.svg",
        "Figure1c_legend_exact_white.pdf",
        "Figure1c_legend_exact_white.png",
        "Figure1c_legend_exact_white.tiff",
        "Figure1c_legend_exact_transparent.svg",
        "Figure1c_legend_exact_transparent.pdf",
        "Figure1c_legend_exact_transparent.png",
        "Figure1c_with_exact_legend_preview.png",
    ]
    for name in expected_figures:
        path = FIG_DIR / name
        check(path.is_file() and path.stat().st_size > 10_000, f"Missing or undersized figure: {name}")

    summary_path = DATA_DIR / "Figure1c_exact_mapping_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    check(summary["svg_metadata"]["node_count"] == 121, "Node count is not 121")
    check(summary["svg_metadata"]["edge_count"] == 803, "Edge count is not 803")
    check(summary["svg_metadata"]["visible_label_count"] == 110, "Visible-label count is not 110")

    node_rows = read_csv(DATA_DIR / "Figure1c_node_visual_encoding.csv")
    edge_rows = read_csv(DATA_DIR / "Figure1c_edge_visual_encoding.csv")
    check(sum(int(row["node_count"]) for row in node_rows) == 121, "Node-class counts do not sum to 121")
    check(sum(int(row["edge_count"]) for row in edge_rows) == 803, "Edge-class counts do not sum to 803")
    observed_edges = {row["visual_group"]: int(row["edge_count"]) for row in edge_rows}
    check(
        observed_edges
        == {
            "NSF dark": 26,
            "NSFC dark": 17,
            "NSF light": 8,
            "NSFC light": 11,
            "Not retained": 741,
        },
        f"Unexpected edge classes: {observed_edges}",
    )

    svg_path = FIG_DIR / "Figure1c_legend_exact_white.svg"
    svg_root = ET.parse(svg_path).getroot()
    svg_text = svg_path.read_text(encoding="utf-8")
    text_nodes = [element for element in svg_root.iter() if element.tag.endswith("text")]
    check(len(text_nodes) >= 30, "SVG text was not preserved as editable text")
    check(all(c in svg_text.lower() for c in ["#003366", "#8b0000", "#7f99b2", "#c57f7f", "#d1d1d1"]), "Exact edge colours are absent")
    check("�" not in svg_text and "□" not in svg_text, "Replacement/missing glyph found in SVG")

    with Image.open(FIG_DIR / "Figure1c_legend_exact_white.png") as image:
        check(image.width >= 4200 and image.height >= 1500, "White PNG is below the intended 600-dpi canvas")
        check(min(image.info.get("dpi", (0, 0))) >= 599, "White PNG does not report 600 dpi")
    with Image.open(FIG_DIR / "Figure1c_legend_exact_white.tiff") as image:
        check(image.width >= 4200 and image.height >= 1500, "TIFF is below the intended 600-dpi canvas")
        check(min(image.info.get("dpi", (0, 0))) >= 599, "TIFF does not report 600 dpi")
    with Image.open(FIG_DIR / "Figure1c_legend_exact_transparent.png") as image:
        check(image.mode == "RGBA", "Transparent PNG is not RGBA")
        alpha_min, alpha_max = image.getchannel("A").getextrema()
        check(alpha_min == 0 and alpha_max == 255, "Transparent PNG alpha channel is incomplete")
    with Image.open(FIG_DIR / "Figure1c_with_exact_legend_preview.png") as image:
        check(image.width >= 1000 and image.height > image.width, "Combined preview dimensions are unexpected")

    for source_name, expected_hash in summary["hashes"].items():
        source_path = (
            SOURCE_DIR.parents[2] / source_name
            if source_name == "figure1bc_common.py"
            else SOURCE_DIR / 'revised_colors' / source_name
        )
        check(source_path.is_file(), f"Source file missing: {source_name}")
        check(sha256(source_path) == expected_hash, f"Source file changed after audit: {source_name}")

    pdf_bytes = (FIG_DIR / "Figure1c_legend_exact_white.pdf").read_bytes()
    check(pdf_bytes.startswith(b"%PDF"), "White PDF does not have a PDF header")
    print("PASS: 121 nodes; 803 edges; exact colour/count mappings verified.")
    print("PASS: SVG editable text, 600-dpi PNG/TIFF, transparency and combined preview verified.")
    print("PASS: audited source hashes remain unchanged.")


if __name__ == "__main__":
    main()
