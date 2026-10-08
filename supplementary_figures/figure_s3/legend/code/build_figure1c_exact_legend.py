from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from PIL import Image


HERE = Path(__file__).resolve().parent
OUTPUT_ROOT = HERE.parent
SOURCE_DIR = OUTPUT_ROOT.parent
DATA_DIR = OUTPUT_ROOT / 'data'
FIGURE_DIR = OUTPUT_ROOT / 'figures'
QA_DIR = OUTPUT_ROOT / 'checks'

LATEST_DIR = SOURCE_DIR / 'revised_colors'
NODE_CSV = LATEST_DIR / "gephi_nodes.csv"
EDGE_CSV = LATEST_DIR / 'gephi_edges_revised_colors.csv'
SOURCE_GEXF = LATEST_DIR / 'figure1c_pooled_union_revised_colors.gexf'
SOURCE_GEPHI = LATEST_DIR / 'sdg-_production_revised_colors.gephi'
SOURCE_SVG = LATEST_DIR / 'sdg_stable_combinations_figure1c.svg'
SOURCE_PNG = LATEST_DIR / 'sdg_stable_combinations_figure1c.png'
ANALYSIS_CODE = SOURCE_DIR.parents[2] / "figure1bc_common.py"
SINGLE_SDG_DIR = SOURCE_DIR.parent / "单个SDG网络"

EXPECTED_NODES = 121
EXPECTED_EDGES = 803
EXPECTED_EDGE_CLASSES = {
    "Shared": 22,
    "NSF-specific": 12,
    "NSFC-specific": 9,
    "Other stable": 19,
    "Not retained": 741,
}
EDGE_CLASS_ORDER = ["NSF dark", "NSFC dark", "NSF light", "NSFC light", "Not retained"]
SDG_ORDER = [2, 3, 6, 7, 9, 10, 11, 12, 13, 15, 16, 17]
EDGE_DISPLAY_LABELS = {
    "NSF dark": "NSF-specific or shared, NSF stronger",
    "NSFC dark": "NSFC-specific or shared, NSFC stronger",
    "NSF light": "Other stable in NSF",
    "NSFC light": "Other stable in NSFC",
    "Not retained": "Not retained",
}


def visual_group(row):
    category = row["stability_class"]
    if category == "Not retained":
        return category
    if category == "Shared":
        agency = "NSF" if float(row["strength_nsf"]) >= float(row["strength_nsfc"]) else "NSFC"
        return agency + " dark"
    if category in ("NSF-specific", "NSFC-specific"):
        return category.split("-")[0] + " dark"
    if category == "Other stable":
        if (row["stable_nsf"] == "True") == (row["stable_nsfc"] == "True"):
            raise AssertionError("Other stable must be stable in exactly one agency")
        return ("NSF" if row["stable_nsf"] == "True" else "NSFC") + " light"
    raise ValueError(category)

MM_TO_INCH = 1.0 / 25.4
FIGURE_WIDTH_MM = 180.0
FIGURE_HEIGHT_MM = 66.0
WHITE_PREFIX = FIGURE_DIR / "Figure1c_legend_exact_white"
TRANSPARENT_PREFIX = FIGURE_DIR / "Figure1c_legend_exact_transparent"
COMBINED_PREVIEW = FIGURE_DIR / "Figure1c_with_exact_legend_preview.png"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quantile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    location = (len(ordered) - 1) * proportion
    lower = int(math.floor(location))
    upper = int(math.ceil(location))
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    max_residual = max(abs((slope * x + intercept) - y) for x, y in zip(xs, ys))
    return slope, intercept, max_residual


def class_code(value: str) -> str:
    if not value.startswith("id_"):
        raise ValueError(f"Unexpected SVG class token: {value}")
    return value[3:]


def parse_svg() -> tuple[dict[str, dict[str, object]], dict[frozenset[str], dict[str, object]], set[str], dict[str, object]]:
    root = ET.parse(SOURCE_SVG).getroot()
    namespace = root.tag.split("}")[0].lstrip("{")
    ns = {"s": namespace}

    circles: dict[str, dict[str, object]] = {}
    for circle in root.findall(".//s:g[@id='nodes']/s:circle", ns):
        code = class_code(circle.attrib["class"])
        circles[code] = {
            "fill": circle.attrib["fill"].upper(),
            "stroke": circle.attrib["stroke"].upper(),
            "radius": float(circle.attrib["r"]),
            "fill_opacity": float(circle.attrib["fill-opacity"]),
            "stroke_opacity": float(circle.attrib["stroke-opacity"]),
            "stroke_width": float(circle.attrib["stroke-width"]),
        }

    edges: dict[frozenset[str], dict[str, object]] = {}
    for path in root.findall(".//s:g[@id='edges']/s:path", ns):
        codes = [class_code(token) for token in path.attrib["class"].split()]
        if len(codes) != 2:
            raise AssertionError(f"Unexpected SVG edge class: {path.attrib['class']}")
        key = frozenset(codes)
        edges[key] = {
            "stroke": path.attrib["stroke"].upper(),
            "stroke_width": float(path.attrib["stroke-width"]),
            "stroke_opacity": float(path.attrib["stroke-opacity"]),
            "curved": "A " in path.attrib.get("d", ""),
        }

    visible_labels = {
        class_code(text.attrib["class"])
        for text in root.findall(".//s:g[@id='node-labels']/s:text", ns)
    }
    metadata = {
        "svg_width": float(root.attrib["width"]),
        "svg_height": float(root.attrib["height"]),
        "svg_viewbox": root.attrib["viewBox"],
        "node_count": len(circles),
        "edge_count": len(edges),
        "visible_label_count": len(visible_labels),
    }
    return circles, edges, visible_labels, metadata


def parse_gephi_project() -> dict[str, object]:
    with ZipFile(SOURCE_GEPHI) as archive:
        appearance_ui = ET.fromstring(archive.read("Workspace_1_appearanceuimodel_xml"))
        preview = ET.fromstring(archive.read("Workspace_1_previewmodel_xml"))
        viz = ET.fromstring(archive.read("Workspace_1_vizmodel_xml"))
        layout = ET.fromstring(archive.read("Workspace_1_layoutmodel_xml"))

    properties: dict[str, object] = {}
    for saved in appearance_ui.findall("savedproperty"):
        function = saved.attrib.get("function", "")
        if function == "node_RankingNodeSizeTransformer_column_9":
            for prop in saved.findall("property"):
                properties[f"node_size_{prop.attrib['key']}"] = float(prop.attrib["value"])

    for prop in preview.findall("previewproperty"):
        properties[f"preview_{prop.attrib['name']}"] = prop.text
    for value in preview.findall("previewsimplevalue"):
        properties[f"preview_{value.attrib['name']}"] = value.text
    for child in viz:
        if "value" in child.attrib:
            properties[f"viz_{child.tag}"] = child.attrib["value"]

    selected_layout = layout.find("selectedlayoutbuilder")
    properties["selected_layout"] = selected_layout.attrib.get("class", "") if selected_layout is not None else ""
    force_atlas = {}
    noverlap = {}
    for prop in layout.findall(".//property"):
        layout_name = prop.attrib.get("layout", "")
        key = prop.attrib.get("property", "")
        if "forceAtlas2" in layout_name:
            force_atlas[key] = prop.text
        elif "noverlap" in layout_name.lower():
            noverlap[key] = prop.text
    properties["forceatlas2_parameters"] = force_atlas
    properties["noverlap_parameters"] = noverlap
    return properties


def parse_analysis_settings() -> dict[str, object]:
    source = ANALYSIS_CODE.read_text(encoding="utf-8")
    patterns = {
        "pair_permutations": r"pair_permutations:\s*int\s*=\s*(\d+)",
        "pair_bootstrap": r"pair_bootstrap:\s*int\s*=\s*(\d+)",
        "alpha": r"alpha:\s*float\s*=\s*([0-9.]+)",
        "min_stable_cooccurrence": r"min_stable_cooccurrence:\s*int\s*=\s*(\d+)",
    }
    result: dict[str, object] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, source)
        if not match:
            raise AssertionError(f"Could not recover analysis setting: {key}")
        value = match.group(1)
        result[key] = float(value) if key == "alpha" else int(value)
    required_fragments = [
        'pairs["permutation_z_nsf"] > 0',
        'pairs["permutation_z_nsfc"] > 0',
        'pairs["bootstrap_ci_low_nsf"] > 0',
        'pairs["bootstrap_ci_low_nsfc"] > 0',
        'pairs["bootstrap_difference_ci_low_nsf_minus_nsfc"] > 0',
        'pairs["bootstrap_difference_ci_high_nsf_minus_nsfc"] < 0',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in source]
    if missing:
        raise AssertionError(f"Stability logic fragments missing: {missing}")
    result["stability_logic_verified"] = True
    return result


def verify_cosine_strength() -> dict[str, object]:
    checked: dict[tuple[str, str, str], float] = {}
    errors: list[float] = []
    files = sorted(SINGLE_SDG_DIR.glob("SDG*/figure1c_s*_edges.csv"))
    for path in files:
        for row in read_csv(path):
            n_a = float(row["n_a"])
            n_b = float(row["n_b"])
            observed = float(row["observed"])
            actual = float(row["strength"])
            expected = observed / math.sqrt(n_a * n_b) if n_a > 0 and n_b > 0 else 0.0
            errors.append(abs(actual - expected))
            key = (row["agency"], row["target_a"], row["target_b"])
            checked[key] = actual
    if not errors:
        raise AssertionError("No single-SDG edge rows were available for cosine-strength verification")
    maximum_error = max(errors)
    if maximum_error > 1e-12:
        raise AssertionError(f"Cosine-strength verification failed: max error={maximum_error}")
    return {
        "files_checked": len(files),
        "rows_checked": len(errors),
        "unique_agency_edges_checked": len(checked),
        "maximum_absolute_error": maximum_error,
        "formula": "observed_cooccurrence / sqrt(n_a * n_b)",
    }


def collect_audit() -> dict[str, object]:
    node_rows = read_csv(NODE_CSV)
    edge_rows = read_csv(EDGE_CSV)
    svg_nodes, svg_edges, visible_labels, svg_metadata = parse_svg()
    project = parse_gephi_project()
    analysis = parse_analysis_settings()
    cosine_check = verify_cosine_strength()

    node_codes = {row["target_code"] for row in node_rows}
    if len(node_rows) != EXPECTED_NODES or len(node_codes) != EXPECTED_NODES:
        raise AssertionError(f"Expected {EXPECTED_NODES} unique nodes, found {len(node_rows)}/{len(node_codes)}")
    if set(svg_nodes) != node_codes:
        raise AssertionError("SVG node identities do not match gephi_nodes.csv")
    if len(edge_rows) != EXPECTED_EDGES or len(svg_edges) != EXPECTED_EDGES:
        raise AssertionError(f"Expected {EXPECTED_EDGES} edges, found {len(edge_rows)}/{len(svg_edges)}")

    nodes_by_sdg: dict[int, list[dict[str, str]]] = defaultdict(list)
    source_colors_by_sdg: dict[int, set[str]] = defaultdict(set)
    actual_fills_by_sdg: dict[int, set[str]] = defaultdict(set)
    actual_strokes_by_sdg: dict[int, set[str]] = defaultdict(set)
    share_values: list[float] = []
    radius_values: list[float] = []
    for row in node_rows:
        code = row["target_code"]
        sdg = int(row["sdg_number"])
        nodes_by_sdg[sdg].append(row)
        source_colors_by_sdg[sdg].add(row["color_hex"].upper())
        actual_fills_by_sdg[sdg].add(str(svg_nodes[code]["fill"]))
        actual_strokes_by_sdg[sdg].add(str(svg_nodes[code]["stroke"]))
        share_values.append(float(row["pooled_share_pct"]))
        radius_values.append(float(svg_nodes[code]["radius"]))
    if sorted(nodes_by_sdg) != SDG_ORDER:
        raise AssertionError(f"Unexpected SDG order: {sorted(nodes_by_sdg)}")
    for sdg in SDG_ORDER:
        if len(source_colors_by_sdg[sdg]) != 1 or len(actual_fills_by_sdg[sdg]) != 1 or len(actual_strokes_by_sdg[sdg]) != 1:
            raise AssertionError(f"SDG {sdg} has inconsistent colors")

    node_slope, node_intercept, node_residual = linear_fit(share_values, radius_values)
    if node_residual > 1e-3:
        raise AssertionError(f"Node-size mapping is not linear: residual={node_residual}")

    edge_classes = Counter(row["stability_class"] for row in edge_rows)
    if dict(edge_classes) != EXPECTED_EDGE_CLASSES:
        raise AssertionError(f"Unexpected edge-class counts: {dict(edge_classes)}")

    svg_edge_keys = set(svg_edges)
    edge_keys = {frozenset((row["source"], row["target"])) for row in edge_rows}
    if svg_edge_keys != edge_keys:
        raise AssertionError("SVG edge identities do not match gephi_edges.csv")

    edge_weights: list[float] = []
    edge_widths: list[float] = []
    colors_by_class: dict[str, set[str]] = defaultdict(set)
    opacities_by_class: dict[str, set[float]] = defaultdict(set)
    weights_by_class: dict[str, list[float]] = defaultdict(list)
    widths_by_class: dict[str, list[float]] = defaultdict(list)
    for row in edge_rows:
        key = frozenset((row["source"], row["target"]))
        visual = svg_edges[key]
        weight = float(row["weight"])
        width = float(visual["stroke_width"])
        category = visual_group(row)
        if category != "Not retained" and str(visual["stroke"]).upper() != row["edge_color"].upper():
            raise AssertionError("Current SVG stable edge colour differs from recoloured CSV")
        expected_weight = (float(row["strength_nsf"]) + float(row["strength_nsfc"])) / 2.0
        if abs(weight - expected_weight) > 1e-12:
            raise AssertionError(f"Edge weight arithmetic mismatch for {row['source']}–{row['target']}")
        edge_weights.append(weight)
        edge_widths.append(width)
        colors_by_class[category].add(str(visual["stroke"]))
        opacities_by_class[category].add(float(visual["stroke_opacity"]))
        weights_by_class[category].append(weight)
        widths_by_class[category].append(width)
    for category in EDGE_CLASS_ORDER:
        if len(colors_by_class[category]) != 1 or len(opacities_by_class[category]) != 1:
            raise AssertionError(f"Edge category {category} has inconsistent visual encoding")

    edge_slope, edge_intercept, edge_residual = linear_fit(edge_weights, edge_widths)
    if edge_residual > 1e-3 or abs(edge_intercept) > 1e-3:
        raise AssertionError(
            f"Edge-width mapping is not proportional: slope={edge_slope}, intercept={edge_intercept}, residual={edge_residual}"
        )

    missing_labels = sorted(node_codes - visible_labels, key=lambda code: node_codes_sort_key(code))
    shared_gray_sdgs = [sdg for sdg in SDG_ORDER if next(iter(actual_fills_by_sdg[sdg])) == "#C0C0C0"]

    node_encoding_rows: list[dict[str, object]] = []
    for sdg in SDG_ORDER:
        source_color = next(iter(source_colors_by_sdg[sdg]))
        current_fill = next(iter(actual_fills_by_sdg[sdg]))
        node_encoding_rows.append(
            {
                "sdg_number": sdg,
                "sdg_label_en": nodes_by_sdg[sdg][0]["sdg_label_en"],
                "node_count": len(nodes_by_sdg[sdg]),
                "current_export_fill": current_fill,
                "current_export_border": next(iter(actual_strokes_by_sdg[sdg])),
                "source_csv_color_hex": source_color,
                "current_matches_source": current_fill == source_color,
                "shares_neutral_grey_in_current_export": sdg in shared_gray_sdgs,
            }
        )

    edge_encoding_rows: list[dict[str, object]] = []
    for category in EDGE_CLASS_ORDER:
        weights = weights_by_class[category]
        widths = widths_by_class[category]
        edge_encoding_rows.append(
            {
                "visual_group": category,
                "display_label": EDGE_DISPLAY_LABELS[category],
                "edge_count": len(weights),
                "current_export_color": next(iter(colors_by_class[category])),
                "current_export_opacity": next(iter(opacities_by_class[category])),
                "weight_min": min(weights),
                "weight_q25": quantile(weights, 0.25),
                "weight_median": quantile(weights, 0.50),
                "weight_q75": quantile(weights, 0.75),
                "weight_max": max(weights),
                "svg_width_min": min(widths),
                "svg_width_median": quantile(widths, 0.50),
                "svg_width_max": max(widths),
            }
        )

    maximum_share = max(share_values)
    size_references = [0.0, 5.0, 10.0, maximum_share]
    node_size_reference_rows = [
        {
            "mean_fractional_target_share_pct": value,
            "svg_radius": node_slope * value + node_intercept,
            "gephi_visual_size_note": "linear radius mapping; minimum visual size retained at zero share",
        }
        for value in size_references
    ]
    edge_reference_values = [0.05, 0.15, 0.30, 0.50]
    edge_width_reference_rows = [
        {
            "mean_cosine_cooccurrence_strength": value,
            "svg_stroke_width": edge_slope * value + edge_intercept,
            "legend_linewidth_pt": 12.0 * value,
        }
        for value in edge_reference_values
    ]

    hashes = {
        path.name: sha256(path)
        for path in [NODE_CSV, EDGE_CSV, SOURCE_GEXF, SOURCE_GEPHI, SOURCE_SVG, SOURCE_PNG, ANALYSIS_CODE]
    }
    return {
        "node_rows": node_rows,
        "edge_rows": edge_rows,
        "node_encoding_rows": node_encoding_rows,
        "edge_encoding_rows": edge_encoding_rows,
        "node_size_reference_rows": node_size_reference_rows,
        "edge_width_reference_rows": edge_width_reference_rows,
        "svg_metadata": svg_metadata,
        "project": project,
        "analysis": analysis,
        "cosine_check": cosine_check,
        "node_size_mapping": {
            "field": "pooled_share_pct",
            "formula": "(target_share_pct_nsf + target_share_pct_nsfc) / 2",
            "svg_radius_slope": node_slope,
            "svg_radius_intercept": node_intercept,
            "maximum_absolute_residual": node_residual,
            "minimum_share_pct": min(share_values),
            "maximum_share_pct": maximum_share,
            "maximum_target": max(node_rows, key=lambda row: float(row["pooled_share_pct"]))["target_code"],
        },
        "edge_width_mapping": {
            "field": "weight",
            "formula": "(strength_nsf + strength_nsfc) / 2",
            "agency_strength_formula": "observed_cooccurrence / sqrt(n_a * n_b)",
            "svg_width_slope": edge_slope,
            "svg_width_intercept": edge_intercept,
            "maximum_absolute_residual": edge_residual,
            "minimum_weight": min(edge_weights),
            "maximum_weight": max(edge_weights),
        },
        "visible_label_count": len(visible_labels),
        "hidden_label_count": len(missing_labels),
        "hidden_labels": missing_labels,
        "shared_gray_sdgs": shared_gray_sdgs,
        "original_stability_counts": dict(edge_classes),
        "source_directory": str(LATEST_DIR),
        "hashes": hashes,
    }


def node_codes_sort_key(code: str) -> tuple[int, float, str]:
    goal, _, suffix = code.partition(".")
    try:
        suffix_number = float(suffix)
    except ValueError:
        suffix_number = 999.0
    return int(goal), suffix_number, suffix


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.0,
            "axes.linewidth": 0.7,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def add_curved_line(ax: plt.Axes, x0: float, x1: float, y: float, color: str, linewidth: float, alpha: float) -> None:
    patch = FancyArrowPatch(
        (x0, y),
        (x1, y),
        transform=ax.transAxes,
        connectionstyle="arc3,rad=0.18",
        arrowstyle="-",
        linewidth=linewidth,
        color=color,
        alpha=alpha,
        capstyle="round",
        joinstyle="round",
        clip_on=False,
    )
    ax.add_patch(patch)


def draw_legend(audit: dict[str, object]) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(FIGURE_WIDTH_MM * MM_TO_INCH, FIGURE_HEIGHT_MM * MM_TO_INCH))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    text_color = "#263238"
    muted = "#66717A"
    divider = "#D6DCE1"

    ax.text(0.022, 0.945, "Figure 1c | Target co-occurrence network", fontsize=8.2, weight="bold", color=text_color, va="top")
    ax.plot([0.022, 0.978], [0.895, 0.895], color="#9AA4AC", lw=0.65, transform=ax.transAxes)
    ax.plot([0.485, 0.485], [0.195, 0.875], color=divider, lw=0.55, transform=ax.transAxes)

    # Nodes: identity and parent-SDG mapping.
    ax.text(0.024, 0.85, "Nodes", fontsize=7.2, weight="bold", color=text_color, va="top")
    ax.scatter([0.047], [0.782], s=[125], c=["#00BD94"], edgecolors=["#005E4A"], linewidths=0.35, transform=ax.transAxes, zorder=4)
    ax.text(0.047, 0.782, "11.3", fontsize=5.0, ha="center", va="center", color=text_color, transform=ax.transAxes, zorder=5)
    ax.text(0.076, 0.782, "Target node; label = Target code", fontsize=6.2, color=text_color, va="center")
    ax.text(0.024, 0.72, "Fill: parent SDG", fontsize=6.2, weight="bold", color=muted, va="center")

    node_encodings = {int(row["sdg_number"]): row for row in audit["node_encoding_rows"]}
    grid_x = [0.046, 0.157, 0.268, 0.379]
    grid_y = [0.645, 0.565, 0.485]
    for index, sdg in enumerate(SDG_ORDER):
        x = grid_x[index % 4]
        y = grid_y[index // 4]
        row = node_encodings[sdg]
        ax.scatter(
            [x],
            [y],
            s=[52],
            c=[row["current_export_fill"]],
            edgecolors=[row["current_export_border"]],
            linewidths=0.3,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(x + 0.014, y, f"SDG {sdg}", fontsize=5.7, color=text_color, va="center", ha="left")

    ax.text(0.024, 0.39, "Size: mean fractional Target share (%)", fontsize=6.2, weight="bold", color=muted, va="center")
    ax.text(0.024, 0.355, "Arithmetic mean of NSF and NSFC shares; linear radius scale", fontsize=5.2, color=muted, va="center")
    size_rows = audit["node_size_reference_rows"]
    min_radius = min(float(row["svg_radius"]) for row in size_rows)
    max_radius = max(float(row["svg_radius"]) for row in size_rows)
    size_x = [0.065, 0.165, 0.285, 0.415]
    for x, row in zip(size_x, size_rows):
        radius = float(row["svg_radius"])
        diameter_pt = 26.5 * radius / max_radius
        ax.scatter(
            [x],
            [0.286],
            s=[diameter_pt**2],
            c=["#EEF1F4"],
            edgecolors=["#59636B"],
            linewidths=0.45,
            transform=ax.transAxes,
            zorder=4,
        )
        value = float(row["mean_fractional_target_share_pct"])
        label = f"{value:.1f}%" if value else "0%"
        ax.text(x, 0.198, label, fontsize=5.6, color=text_color, va="center", ha="center")

    # Edges: class and strength.
    ax.text(0.515, 0.85, "Undirected co-occurrence edges", fontsize=7.2, weight="bold", color=text_color, va="top")
    ax.text(0.515, 0.79, "Colour: stable-edge grouping", fontsize=6.2, weight="bold", color=muted, va="center")
    edge_encodings = {str(row["visual_group"]): row for row in audit["edge_encoding_rows"]}
    ax.text(0.785, 0.735, "NSF", fontsize=6.1, weight="bold", color=text_color, ha="center")
    ax.text(0.925, 0.735, "NSFC", fontsize=6.1, weight="bold", color=text_color, ha="center")
    ax.text(0.515, 0.67, "Specific or shared*", fontsize=6.1, color=text_color, va="center")
    ax.text(0.515, 0.57, "Other stable†", fontsize=6.1, color=text_color, va="center")
    for category, x, y in [("NSF dark", .785, .67), ("NSFC dark", .925, .67),
                            ("NSF light", .785, .57), ("NSFC light", .925, .57)]:
        row = edge_encodings[category]
        add_curved_line(ax, x-.036, x+.036, y, str(row["current_export_color"]),
                        2.15, float(row["current_export_opacity"]))
    row = edge_encodings["Not retained"]
    ax.text(.515, .475, "Not retained", fontsize=6.1, color=text_color, va="center")
    add_curved_line(ax, .749, .821, .475, str(row["current_export_color"]), 2.15,
                    float(row["current_export_opacity"]))

    ax.text(0.515, 0.405, "Width: mean cosine co-occurrence strength, w", fontsize=6.2, weight="bold", color=muted, va="center")
    ax.text(0.515, 0.367, "Arithmetic mean of NSF and NSFC strengths", fontsize=5.2, color=muted, va="center")
    width_rows = audit["edge_width_reference_rows"]
    strength_x = [0.535, 0.655, 0.785, 0.915]
    for x, row in zip(strength_x, width_rows):
        value = float(row["mean_cosine_cooccurrence_strength"])
        add_curved_line(ax, x - 0.035, x + 0.035, 0.275, "#59636B", 12.0 * value, 0.92156863)
        ax.text(x, 0.215, f"w = {value:.2f}", fontsize=5.55, color=text_color, ha="center", va="center")

    ax.plot([0.022, 0.978], [0.165, 0.165], color=divider, lw=0.55, transform=ax.transAxes)
    ax.text(.024, .125, "* Agency-specific stable edges, or edges stable in both agencies coloured by the agency with higher co-occurrence strength.",
            fontsize=5.4, color=text_color, va="center")
    ax.text(.024, .078, "† Stable in one agency, without an established between-agency difference. Shared-edge colour alone does not indicate a significant difference.",
            fontsize=5.25, color=muted, va="center")
    ax.text(.024, .034, "SDGs 6, 7, 9 and 13 share grey; use the Target-code prefix to distinguish them.",
            fontsize=5.4, color=muted, va="center")
    return fig


def save_figure(fig: plt.Figure) -> list[Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for extension in ("svg", "pdf"):
        path = WHITE_PREFIX.with_suffix(f".{extension}")
        fig.savefig(path, facecolor="white", transparent=False)
        outputs.append(path)
    white_png = WHITE_PREFIX.with_suffix(".png")
    fig.savefig(white_png, dpi=600, facecolor="white", transparent=False)
    outputs.append(white_png)
    white_tiff = WHITE_PREFIX.with_suffix(".tiff")
    fig.savefig(white_tiff, dpi=600, facecolor="white", transparent=False, pil_kwargs={"compression": "tiff_lzw"})
    outputs.append(white_tiff)

    for extension in ("svg", "pdf"):
        path = TRANSPARENT_PREFIX.with_suffix(f".{extension}")
        fig.savefig(path, transparent=True)
        outputs.append(path)
    transparent_png = TRANSPARENT_PREFIX.with_suffix(".png")
    fig.savefig(transparent_png, dpi=600, transparent=True)
    outputs.append(transparent_png)
    return outputs


def build_combined_preview() -> Path:
    with Image.open(SOURCE_PNG) as network_image, Image.open(WHITE_PREFIX.with_suffix(".png")) as legend_image:
        network = network_image.convert("RGB")
        legend = legend_image.convert("RGB")
        legend_height = round(network.width * legend.height / legend.width)
        legend = legend.resize((network.width, legend_height), Image.Resampling.LANCZOS)
        separator = 8
        canvas = Image.new("RGB", (network.width, network.height + separator + legend.height), "white")
        canvas.paste(network, (0, 0))
        for y in range(network.height, network.height + separator):
            shade = 238 + round(12 * (y - network.height) / max(separator - 1, 1))
            for x in range(network.width):
                canvas.putpixel((x, y), (shade, shade, shade))
        canvas.paste(legend, (0, network.height + separator))
        canvas.save(COMBINED_PREVIEW, dpi=(300, 300), optimize=True)
    return COMBINED_PREVIEW


def export_data(audit: dict[str, object]) -> list[Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    node_path = DATA_DIR / "Figure1c_node_visual_encoding.csv"
    write_csv(
        node_path,
        audit["node_encoding_rows"],
        [
            "sdg_number",
            "sdg_label_en",
            "node_count",
            "current_export_fill",
            "current_export_border",
            "source_csv_color_hex",
            "current_matches_source",
            "shares_neutral_grey_in_current_export",
        ],
    )
    edge_path = DATA_DIR / "Figure1c_edge_visual_encoding.csv"
    write_csv(
        edge_path,
        audit["edge_encoding_rows"],
        [
            "visual_group",
            "display_label",
            "edge_count",
            "current_export_color",
            "current_export_opacity",
            "weight_min",
            "weight_q25",
            "weight_median",
            "weight_q75",
            "weight_max",
            "svg_width_min",
            "svg_width_median",
            "svg_width_max",
        ],
    )
    node_size_path = DATA_DIR / "Figure1c_node_size_reference.csv"
    write_csv(
        node_size_path,
        audit["node_size_reference_rows"],
        ["mean_fractional_target_share_pct", "svg_radius", "gephi_visual_size_note"],
    )
    edge_width_path = DATA_DIR / "Figure1c_edge_width_reference.csv"
    write_csv(
        edge_width_path,
        audit["edge_width_reference_rows"],
        ["mean_cosine_cooccurrence_strength", "svg_stroke_width", "legend_linewidth_pt"],
    )
    summary_path = DATA_DIR / "Figure1c_exact_mapping_summary.json"
    serializable = {
        key: value
        for key, value in audit.items()
        if key not in {"node_rows", "edge_rows", "node_encoding_rows", "edge_encoding_rows", "node_size_reference_rows", "edge_width_reference_rows"}
    }
    summary_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return [node_path, edge_path, node_size_path, edge_width_path, summary_path]


def image_dimensions(path: Path) -> tuple[int, int, str]:
    with Image.open(path) as image:
        return image.width, image.height, image.mode


def write_qa_report(audit: dict[str, object], outputs: list[Path], data_outputs: list[Path]) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    output_hashes = {path.name: sha256(path) for path in outputs + data_outputs if path.exists()}
    raster_lines = []
    for path in outputs:
        if path.suffix.lower() in {".png", ".tiff", ".tif"}:
            width, height, mode = image_dimensions(path)
            raster_lines.append(f"- `{path.name}`: {width} × {height} px, mode={mode}, {path.stat().st_size:,} bytes")

    node_map = audit["node_size_mapping"]
    edge_map = audit["edge_width_mapping"]
    analysis = audit["analysis"]
    log_metric = "log" + "2 (O/E)"
    report = f"""# Figure 1c 现图精确匹配图例 QA

## Overall assessment
**映射已核验。** 图例中的颜色、数量、尺度和统计术语均已从实际导出 SVG、Gephi 保存参数、CSV 与分析代码交叉复核。当前主图有 4 个 SDG 共用灰色，图例已显式披露。

## Source integrity
- 使用 `revised_colors` 目录的最新 SVG、PNG、Gephi 与 CSV。
- 背景边在当前 SVG 中为 #D1D1D1、opacity=1；与 CSV 预设不同，图例按实际导出显示。
- 统计类别与视觉分组分开保存。深色包含特异边和按强度较高方着色的共同稳定边。
- Target 节点：{audit['svg_metadata']['node_count']}（要求 {EXPECTED_NODES}）。
- 无向边：{audit['svg_metadata']['edge_count']}（要求 {EXPECTED_EDGES}）。
- SVG 可见标签：{audit['visible_label_count']}；因 Gephi 避让隐藏：{audit['hidden_label_count']}。
- 隐藏标签：{', '.join(audit['hidden_labels']) if audit['hidden_labels'] else 'None'}。
- 全部边类别合计：{sum(int(row['edge_count']) for row in audit['edge_encoding_rows'])}。
- 稳定边合计：{sum(int(row['edge_count']) for row in audit['edge_encoding_rows'] if row['visual_group'] != 'Not retained')}。
- 实际共享灰色的 SDG：{', '.join('SDG ' + str(value) for value in audit['shared_gray_sdgs'])}。

## Calculation spot-checks
- 节点大小字段：`pooled_share_pct = (target_share_pct_nsf + target_share_pct_nsfc) / 2`。
- 节点 SVG 半径：`r = {node_map['svg_radius_slope']:.9f} × share + {node_map['svg_radius_intercept']:.9f}`；最大残差 {node_map['maximum_absolute_residual']:.3g}。
- 最大节点：Target {node_map['maximum_target']}，{node_map['maximum_share_pct']:.9f}% 。
- 边强度：`strength = observed / sqrt(n_a × n_b)`；核对 {audit['cosine_check']['rows_checked']} 行，最大绝对误差 {audit['cosine_check']['maximum_absolute_error']:.3g}。
- 边宽字段：`weight = (strength_nsf + strength_nsfc) / 2`。
- SVG 边宽：`stroke_width = {edge_map['svg_width_slope']:.9f} × weight + {edge_map['svg_width_intercept']:.3g}`；最大残差 {edge_map['maximum_absolute_residual']:.3g}。

## Stability definition recovered from analysis code
- 最小观察共现：{analysis['min_stable_cooccurrence']}。
- BH 校正阈值：q < {analysis['alpha']}。
- 置换次数：{analysis['pair_permutations']:,}；要求 permutation z > 0。
- Bootstrap 次数：{analysis['pair_bootstrap']:,}；要求 `{log_metric}` 95% CI 下限 > 0。
- NSF/NSFC 特异类别还要求两国差异 bootstrap 95% CI 完全位于零的一侧。

## Actual edge-colour classes
"""
    for row in audit["edge_encoding_rows"]:
        report += f"- `{row['visual_group']}`: {row['current_export_color']}, opacity={float(row['current_export_opacity']):.6f}, n={row['edge_count']}。\n"
    report += "\n## Raster outputs\n" + "\n".join(raster_lines)
    report += "\n\n## Required caveat\n- 当前 SVG 中 SDG 6、7、9、13 共同使用 `#C0C0C0`；读者需借助 Target 编码前缀区分。若将来需要 12 个 SDG 的独立颜色，必须重新导出主网络并同步重建图例。\n"
    report += "\n## Output SHA-256\n"
    for name, digest in sorted(output_hashes.items()):
        report += f"- `{name}`: `{digest}`\n"

    qa_path = QA_DIR / 'Figure1c_legend_QA.md'
    qa_path.write_text(report, encoding="utf-8")
    return qa_path


def write_delivery_note(audit: dict[str, object], outputs: list[Path], data_outputs: list[Path], qa_path: Path) -> Path:
    note = f"""# Figure 1c 图例delivery_notes

## 交付内容
本目录提供与当前 Gephi 网络导出逐项匹配的英文正式图例。原始 `.gephi`、PNG、PDF 与 SVG 未被修改或覆盖。

### 正式图例
- `图/{WHITE_PREFIX.name}.svg`：可编辑矢量版。
- `图/{WHITE_PREFIX.name}.pdf`：投稿/排版矢量版。
- `图/{WHITE_PREFIX.name}.png`：600 dpi 白底版。
- `图/{WHITE_PREFIX.name}.tiff`：600 dpi LZW 压缩版。
- `图/{TRANSPARENT_PREFIX.name}.svg/.pdf/.png`：透明背景版。
- `图/{COMBINED_PREVIEW.name}`：原网络图加图例的组合preview，不替代原始主图。

### 数据与审计
- `数据/Figure1c_node_visual_encoding.csv`：12 个 SDG 的实际节点色值与数量。
- `数据/Figure1c_edge_visual_encoding.csv`：5 个视觉分组的实际颜色、数量和强度范围。
- `数据/Figure1c_node_size_reference.csv`：节点大小参照值。
- `数据/Figure1c_edge_width_reference.csv`：边宽参照值。
- `数据/Figure1c_exact_mapping_summary.json`：完整机器可读映射与源文件哈希。
- `核查/{qa_path.name}`：数值、视觉和格式复核报告。

## 图例中的精确定义
- 节点表示 SDG Target，文字为 Target 编码。
- 节点大小是 NSF 与 NSFC 分数计数 Target 占比的算术平均，不是按两国项目量加权的合并占比。
- 边表示同一项目中的无向 Target 共现。
- 边宽是两国余弦共现强度的算术平均。
- 当前主图保留全部 {EXPECTED_EDGES} 条边，并以深浅蓝红色区分更新后的稳定连线分组。深色包含特异边和共同稳定边，共同稳定边按强度较高方着色；浅色表示仅在一方稳定、但未确立国家特异性的连线。

## 当前图面的必要限制
SDG 6、7、9、13 在当前 Gephi 导出中共同使用灰色 `#C0C0C0`。正式图例没有为它们虚构不同颜色，而是notes依靠 Target 编码前缀区分。
"""
    path = QA_DIR / 'Figure1c_legend_delivery_notes.md'
    path.write_text(note, encoding="utf-8")
    return path


def main() -> None:
    for directory in (DATA_DIR, FIGURE_DIR, QA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    audit = collect_audit()
    data_outputs = export_data(audit)
    fig = draw_legend(audit)
    outputs = save_figure(fig)
    plt.close(fig)
    outputs.append(build_combined_preview())
    qa_path = write_qa_report(audit, outputs, data_outputs)
    delivery_path = write_delivery_note(audit, outputs, data_outputs, qa_path)
    print(f"Nodes: {audit['svg_metadata']['node_count']}")
    print(f"Edges: {audit['svg_metadata']['edge_count']}")
    print(f"Visible labels: {audit['visible_label_count']}")
    print(f"Shared grey SDGs: {audit['shared_gray_sdgs']}")
    print(f"Figure outputs: {len(outputs)}")
    print(f"Data outputs: {len(data_outputs)}")
    print(f"QA: {qa_path}")
    print(f"Delivery note: {delivery_path}")


if __name__ == "__main__":
    main()
