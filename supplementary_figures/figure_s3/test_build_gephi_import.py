from __future__ import annotations

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_gephi_import import build_gephi_package  # noqa: E402


EXPECTED_SDG_COLORS = {
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

EXPECTED_STABILITY_STYLE = {
    "Not retained": ("#CBD2D8", 0.16),
    "Shared": ("#746A82", 0.88),
    "NSF-specific": ("#607E96", 0.88),
    "NSFC-specific": ("#AD7072", 0.88),
    "Other stable": ("#858B91", 0.62),
}


class GephiPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.edges, cls.graph = build_gephi_package(write_outputs=False)

    def test_graph_contract(self):
        self.assertEqual(len(self.nodes), 121)
        self.assertEqual(self.nodes["target_code"].nunique(), 121)
        self.assertEqual(len(self.edges), 803)
        self.assertEqual(self.graph.number_of_nodes(), 121)
        self.assertEqual(self.graph.number_of_edges(), 803)

    def test_presence_contract(self):
        counts = self.edges["presence_class"].value_counts().to_dict()
        self.assertEqual(counts["Shared nonzero"], 301)
        self.assertEqual(counts["NSF only"], 345)
        self.assertEqual(counts["NSFC only"], 157)

    def test_weights_are_valid(self):
        self.assertTrue(np.isfinite(self.edges["weight"]).all())
        self.assertTrue((self.edges["weight"] > 0).all())
        self.assertTrue(self.edges["weight"].between(0, 1).all())

    def test_endpoints_exist(self):
        nodes = set(self.nodes["target_code"])
        self.assertTrue(set(self.edges["source"]).issubset(nodes))
        self.assertTrue(set(self.edges["target"]).issubset(nodes))
        self.assertFalse((self.edges["source"] == self.edges["target"]).any())

    def test_nature_node_palette(self):
        observed = self.nodes.groupby("sdg_code")["color_hex"].first().to_dict()
        self.assertEqual(observed, EXPECTED_SDG_COLORS)

    def test_stability_led_edge_style(self):
        for category, (color, alpha) in EXPECTED_STABILITY_STYLE.items():
            subset = self.edges.loc[self.edges["stability_class"].eq(category)]
            self.assertFalse(subset.empty)
            self.assertEqual(set(subset["edge_color"]), {color})
            self.assertTrue(np.allclose(subset["edge_alpha"], alpha))

    def test_presence_color_is_preserved_as_alternate_style(self):
        expected = {
            "Shared nonzero": "#746A82",
            "NSF only": "#7890A3",
            "NSFC only": "#B78484",
        }
        observed = (
            self.edges.groupby("presence_class")["presence_color"].first().to_dict()
        )
        self.assertEqual(observed, expected)

    def test_graph_viz_alpha_matches_edge_table(self):
        alpha_by_id = {
            row.edge_id: float(row.edge_alpha)
            for row in self.edges.itertuples(index=False)
        }
        for _, _, attributes in self.graph.edges(data=True):
            self.assertAlmostEqual(
                float(attributes["viz"]["color"]["a"]),
                alpha_by_id[attributes["id"]],
            )

    def test_gexf_serializes_edge_rgba(self):
        namespaces = {
            "gexf": "http://www.gexf.net/1.2draft",
            "viz": "http://www.gexf.net/1.2draft/viz",
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "palette_roundtrip.gexf"
            nx.write_gexf(
                self.graph,
                output,
                encoding="utf-8",
                prettyprint=True,
                version="1.2draft",
            )
            root = ET.parse(output).getroot()

        edge_colors = root.findall(".//gexf:edge/viz:color", namespaces)
        self.assertEqual(len(edge_colors), 803)
        observed_alphas = {round(float(element.attrib["a"]), 2) for element in edge_colors}
        self.assertEqual(observed_alphas, {0.16, 0.62, 0.88})


if __name__ == "__main__":
    unittest.main()
