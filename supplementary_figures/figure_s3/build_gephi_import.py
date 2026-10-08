from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE.parent / "source_data"
NODE_SOURCE = SOURCE_DIR / "figure1c_target_nodes.csv"
EDGE_SOURCE = SOURCE_DIR / "figure1c_full_edges.csv"

SDG_COLORS = {
    "S02": "#B89B58",
    "S03": "#6F9870",
    "S06": "#5B9AAC",
    "S07": "#C5AA58",
    "S09": "#C47B61",
    "S10": "#AD6F88",
    "S11": "#C38F55",
    "S12": "#9C8258",
    "S13": "#5F8068",
    "S15": "#7FA064",
    "S16": "#4E7C96",
    "S17": "#526C83",
}

PRESENCE_COLORS = {
    "Shared nonzero": "#746A82",
    "NSF only": "#7890A3",
    "NSFC only": "#B78484",
}

STABILITY_STYLES = {
    "Not retained": ("#CBD2D8", 0.16),
    "Shared": ("#746A82", 0.88),
    "NSF-specific": ("#607E96", 0.88),
    "NSFC-specific": ("#AD7072", 0.88),
    "Other stable": ("#858B91", 0.62),
}


def _rgba(hex_color: str, alpha: float = 1.0) -> dict[str, int | float]:
    value = hex_color.lstrip("#")
    return {
        "r": int(value[0:2], 16),
        "g": int(value[2:4], 16),
        "b": int(value[4:6], 16),
        "a": float(alpha),
    }


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pooled_edges(full_edges: pd.DataFrame) -> pd.DataFrame:
    keys = ["target_a", "target_b"]
    base = (
        full_edges[keys + ["stability_class"]]
        .drop_duplicates(keys)
        .rename(columns={"target_a": "source", "target_b": "target"})
    )
    for agency in ("NSF", "NSFC"):
        suffix = agency.lower()
        subset = full_edges.loc[
            full_edges["agency"].eq(agency),
            keys + ["strength", "observed", "stable", "bh_q", "permutation_z"],
        ].rename(
            columns={
                "target_a": "source",
                "target_b": "target",
                "strength": f"strength_{suffix}",
                "observed": f"observed_{suffix}",
                "stable": f"stable_{suffix}",
                "bh_q": f"bh_q_{suffix}",
                "permutation_z": f"permutation_z_{suffix}",
            }
        )
        base = base.merge(subset, on=["source", "target"], how="outer")

    for column in (
        "strength_nsf",
        "strength_nsfc",
        "observed_nsf",
        "observed_nsfc",
        "permutation_z_nsf",
        "permutation_z_nsfc",
    ):
        base[column] = pd.to_numeric(base[column], errors="coerce").fillna(0.0)
    for column in ("stable_nsf", "stable_nsfc"):
        base[column] = base[column].map(lambda value: False if pd.isna(value) else bool(value))
    for column in ("bh_q_nsf", "bh_q_nsfc"):
        base[column] = pd.to_numeric(base[column], errors="coerce").fillna(1.0)

    base["present_nsf"] = base["observed_nsf"].gt(0)
    base["present_nsfc"] = base["observed_nsfc"].gt(0)
    base["presence_class"] = np.select(
        [
            base["present_nsf"] & base["present_nsfc"],
            base["present_nsf"],
            base["present_nsfc"],
        ],
        ["Shared nonzero", "NSF only", "NSFC only"],
        default="Invalid",
    )
    base["pooled_strength"] = (base["strength_nsf"] + base["strength_nsfc"]) / 2.0
    base["pooled_observed"] = base["observed_nsf"] + base["observed_nsfc"]
    base["weight"] = base["pooled_strength"]
    base["presence_color"] = base["presence_class"].map(PRESENCE_COLORS)
    base["edge_color"] = base["stability_class"].map(
        {category: style[0] for category, style in STABILITY_STYLES.items()}
    )
    base["edge_alpha"] = base["stability_class"].map(
        {category: style[1] for category, style in STABILITY_STYLES.items()}
    )
    visual_columns = ["presence_color", "edge_color", "edge_alpha"]
    if base[visual_columns].isna().any().any():
        missing = base.loc[base[visual_columns].isna().any(axis=1), [
            "source",
            "target",
            "presence_class",
            "stability_class",
        ]]
        raise AssertionError(
            "Missing Gephi visual mapping for edge categories: "
            f"{missing.to_dict(orient='records')[:5]}"
        )
    base["edge_id"] = [f"e{idx:04d}" for idx in range(len(base))]
    return base.sort_values(["source", "target"], kind="stable").reset_index(drop=True)


def build_gephi_package(
    *,
    write_outputs: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, nx.Graph]:
    nodes = pd.read_csv(NODE_SOURCE, dtype={"target_code": str})
    full_edges = pd.read_csv(
        EDGE_SOURCE,
        dtype={"target_a": str, "target_b": str, "agency": str},
        low_memory=False,
    )
    edges = _pooled_edges(full_edges)

    nodes["pooled_share_pct"] = (
        nodes["target_share_pct_nsf"] + nodes["target_share_pct_nsfc"]
    ) / 2.0
    nodes["total_fractional_count"] = (
        nodes["fractional_count_nsf"] + nodes["fractional_count_nsfc"]
    )
    nodes["color_hex"] = nodes["sdg_code"].map(SDG_COLORS)
    maximum = max(float(nodes["pooled_share_pct"].max()), 1e-12)
    nodes["gephi_size"] = 8.0 + 32.0 * np.sqrt(nodes["pooled_share_pct"] / maximum)

    graph = nx.Graph(
        name="Figure 1c pooled NSF-NSFC Target co-occurrence network",
        mode="static",
        defaultedgetype="undirected",
    )
    for row in nodes.itertuples(index=False):
        graph.add_node(
            row.target_code,
            label=row.target_code,
            target_label_zh=str(row.target_label_zh),
            sdg_code=row.sdg_code,
            sdg_number=int(row.sdg_number),
            sdg_label_en=row.sdg_label_en,
            target_order=int(row.target_order),
            fractional_count_nsf=float(row.fractional_count_nsf),
            fractional_count_nsfc=float(row.fractional_count_nsfc),
            target_share_pct_nsf=float(row.target_share_pct_nsf),
            target_share_pct_nsfc=float(row.target_share_pct_nsfc),
            pooled_share_pct=float(row.pooled_share_pct),
            total_fractional_count=float(row.total_fractional_count),
            color_hex=row.color_hex,
            viz={
                "color": _rgba(row.color_hex),
                "size": float(row.gephi_size),
                "shape": "disc",
            },
        )

    for row in edges.itertuples(index=False):
        graph.add_edge(
            row.source,
            row.target,
            id=row.edge_id,
            weight=float(row.weight),
            pooled_strength=float(row.pooled_strength),
            pooled_observed=float(row.pooled_observed),
            strength_nsf=float(row.strength_nsf),
            strength_nsfc=float(row.strength_nsfc),
            observed_nsf=float(row.observed_nsf),
            observed_nsfc=float(row.observed_nsfc),
            present_nsf=bool(row.present_nsf),
            present_nsfc=bool(row.present_nsfc),
            presence_class=row.presence_class,
            stability_class=str(row.stability_class),
            stable_nsf=bool(row.stable_nsf),
            stable_nsfc=bool(row.stable_nsfc),
            presence_color=row.presence_color,
            edge_color=row.edge_color,
            edge_alpha=float(row.edge_alpha),
            viz={"color": _rgba(row.edge_color, row.edge_alpha)},
        )

    degree = dict(graph.degree())
    weighted_degree = dict(graph.degree(weight="weight"))
    nodes["pooled_degree"] = nodes["target_code"].map(degree).astype(int)
    nodes["pooled_weighted_degree"] = nodes["target_code"].map(weighted_degree).astype(float)
    nx.set_node_attributes(graph, degree, "pooled_degree")
    nx.set_node_attributes(graph, weighted_degree, "pooled_weighted_degree")

    if graph.number_of_nodes() != 121 or graph.number_of_edges() != 803:
        raise AssertionError(
            f"Gephi graph contract failed: {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges"
        )
    presence = edges["presence_class"].value_counts().to_dict()
    if presence != {"NSF only": 345, "Shared nonzero": 301, "NSFC only": 157}:
        raise AssertionError(f"Unexpected presence classes: {presence}")
    stability = edges["stability_class"].value_counts().to_dict()

    if write_outputs:
        output_gexf = HERE / "figure1c_pooled_union.gexf"
        output_nodes = HERE / "gephi_nodes.csv"
        output_edges = HERE / "gephi_edges.csv"
        nx.write_gexf(graph, output_gexf, encoding="utf-8", prettyprint=True, version="1.2draft")
        nodes.to_csv(output_nodes, index=False, encoding="utf-8-sig")
        edges.to_csv(output_edges, index=False, encoding="utf-8-sig")
        report = HERE / "gephi_import_qa.txt"
        report.write_text(
            "\n".join(
                [
                    "Figure 1c Gephi import package QA",
                    "=" * 38,
                    f"Nodes: {graph.number_of_nodes()}",
                    f"Union edges: {graph.number_of_edges()}",
                    f"Shared nonzero edges: {presence['Shared nonzero']}",
                    f"NSF-only edges: {presence['NSF only']}",
                    f"NSFC-only edges: {presence['NSFC only']}",
                    "Visual style: Nature-aligned muted palette, stability-led edge hierarchy",
                    f"Not-retained background edges: {stability['Not retained']}",
                    f"Shared stable edges: {stability['Shared']}",
                    f"NSF-specific stable edges: {stability['NSF-specific']}",
                    f"NSFC-specific stable edges: {stability['NSFC-specific']}",
                    f"Other stable edges: {stability['Other stable']}",
                    f"Node source SHA-256: {_sha256(NODE_SOURCE)}",
                    f"Edge source SHA-256: {_sha256(EDGE_SOURCE)}",
                    f"GEXF SHA-256: {_sha256(output_gexf)}",
                ]
            ),
            encoding="utf-8",
        )
    return nodes, edges, graph


def main() -> None:
    nodes, edges, graph = build_gephi_package(write_outputs=True)
    print(f"Gephi package written to: {HERE}")
    print(f"Nodes={len(nodes)}, edges={len(edges)}, graph={graph.number_of_nodes()}/{graph.number_of_edges()}")


if __name__ == "__main__":
    main()
