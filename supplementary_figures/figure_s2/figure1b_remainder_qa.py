from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parent
REMAINDER = ROOT / "figure1b剩余"
CSV_ROUNDING_TOLERANCE = 1e-6


def main() -> None:
    main_table = pd.read_csv(ROOT / "figure1b_semantic_composition_main.csv")
    remaining = pd.read_csv(REMAINDER / "figure1b_remaining_categories_source_data.csv")

    other = (
        main_table.loc[main_table["main_display_group"].eq("Other")]
        .groupby(["agency", "year", "dimension"], as_index=False)["share_pct"]
        .sum()
        .rename(columns={"share_pct": "other_share"})
    )
    decomposed = (
        remaining.groupby(["agency", "year", "dimension"], as_index=False)["share_pct"]
        .sum()
        .rename(columns={"share_pct": "decomposed_share"})
    )
    comparison = other.merge(
        decomposed,
        on=["agency", "year", "dimension"],
        how="outer",
        validate="one_to_one",
    ).fillna(0.0)
    max_delta = float((comparison["other_share"] - comparison["decomposed_share"]).abs().max())

    preview = Image.open(REMAINDER / "figure1b_remaining_combined_preview.png")
    tiff = Image.open(REMAINDER / "figure1b_remaining_combined.tiff")
    svg = (REMAINDER / "figure1b_remaining_combined.svg").read_text(encoding="utf-8")
    tiff_dpi = tiff.info.get("dpi", (0.0, 0.0))

    print(f"Other equality max absolute difference: {max_delta:.12g}")
    print(f"Compared agency-year-dimension cells: {len(comparison)}")
    print(f"Combined PNG: {preview.size}")
    print(f"Combined TIFF: {tiff.size}; dpi={tiff_dpi}")
    print(f"Combined SVG text elements: {svg.count('<text')}")

    if max_delta >= CSV_ROUNDING_TOLERANCE:
        raise AssertionError("Remaining-category shares do not reproduce Other")
    if svg.count("<text") == 0:
        raise AssertionError("SVG text is not editable")
    if min(tiff_dpi) < 599:
        raise AssertionError("TIFF is below 600 dpi")


if __name__ == "__main__":
    main()
