from __future__ import annotations

import json
import math
import platform
import sys
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, PercentFormatter
from PIL import Image


CODE_ROOT = Path(__file__).resolve().parent
SOLUTION_ROOT = CODE_ROOT.parent
FIGURE5E_ROOT = SOLUTION_ROOT.parent
FIGURE5_ROOT = FIGURE5E_ROOT.parent
FIGURE_ROOT = FIGURE5_ROOT.parent
WORKSPACE_ROOT = FIGURE_ROOT.parents[1]
CONTROL_CODE = FIGURE_ROOT / "figure2-figure5制作总控" / 'code'
SDSN_ROOT = WORKSPACE_ROOT / "辅助数据" / "预处理" / "D-SDSN"

DATA_DIR = SOLUTION_ROOT / 'data'
FIGURE_DIR = SOLUTION_ROOT / 'outputs'
QA_DIR = SOLUTION_ROOT / "QA"

FIGURE4B_FORMAL = (
    FIGURE_ROOT
    / "figure4"
    / "figure4b"
    / "配对CLR偏离诊断与稳定性分类"
    / "方案B_配对森林—跨国差值轨道版"
    / 'data'
    / "Figure4b_B_country_estimates.csv"
)
FIGURE4C_FORMAL = (
    FIGURE_ROOT
    / "figure4"
    / "figure4c"
    / "正式版_双国方向化Aitchison贡献剖面"
    / 'data'
    / "figure4c_count_only_diagnostic_contributions.csv"
)
FIGURE3D_CITY = (
    FIGURE_ROOT
    / "figure3"
    / "figure3d"
    / "方案A_累积城市排名轨迹与Gini叠加"
    / 'data'
    / "Figure3d_城市SDG供给.csv"
)

if str(CONTROL_CODE) not in sys.path:
    sys.path.insert(0, str(CONTROL_CODE))

from figure_common import (  # noqa: E402
    A_ORDER,
    SDG_ORDER,
    AnalysisSettings,
    build_balance_features,
    entropy_balance_to_reference,
    fractional_matrix,
    load_projects,
)


SEED = 20260827
N_BOOTSTRAP = 2_000
ANALYSIS_START = 2015
ANALYSIS_END = 2025
EPSILON = 1e-12
ADVANCED_ACTIONS = frozenset(A_ORDER[2:])
AGENCY_ORDER = ("NSF", "NSFC")

NSF_COLOR = "#7F99B2"
NSFC_COLOR = "#C57F7F"
AGENCY_COLORS = {"NSF": NSF_COLOR, "NSFC": NSFC_COLOR}
TEXT_COLOR = "#1F2933"
MUTED_TEXT = "#6E7982"
GRID_COLOR = "#DCE3E7"
FRAME_COLOR = "#657680"
RING_COLOR = "#36444E"


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.0,
            "axes.labelsize": 8.2,
            "axes.titlesize": 10.0,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "legend.fontsize": 6.5,
            "axes.linewidth": 0.85,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def close_composition(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not np.isfinite(array).all() or (array < 0).any():
        raise ValueError("Composition must be a finite, non-negative vector")
    array = np.maximum(array, EPSILON)
    return array / array.sum()


def clr(values: Sequence[float]) -> np.ndarray:
    composition = close_composition(values)
    logged = np.log(composition)
    return logged - logged.mean()


def classify_mismatch(value: float) -> str:
    if value < -0.5:
        return "Relatively lower"
    if value > 0.5:
        return "Relatively higher"
    return "Near alignment"


def load_challenge(agency: str) -> pd.DataFrame:
    path = SDSN_ROOT / f"{agency}.csv"
    raw = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    selected = raw.loc[
        raw["funding_year"].between(ANALYSIS_START, ANALYSIS_END)
        & raw["sdg_goal"].isin([int(code[1:]) for code in SDG_ORDER])
    ].copy()
    goal = selected[
        [
            "funding_year",
            "sdg_goal",
            "goal_name_en",
            "d0_goal_challenge_lag_mean",
            "d0_source_years",
            "analysis_ready_goal_at_least_2_lags",
        ]
    ].drop_duplicates(["funding_year", "sdg_goal"])
    expected = (ANALYSIS_END - ANALYSIS_START + 1) * len(SDG_ORDER)
    if len(goal) != expected:
        raise ValueError(f"{agency}: incomplete SDSN grid {len(goal)} != {expected}")
    if not goal["analysis_ready_goal_at_least_2_lags"].eq(1).all():
        raise ValueError(f"{agency}: non-ready SDSN goal-year values")
    goal["sdg"] = goal["sdg_goal"].map(lambda value: f"S{int(value):02d}")
    return goal


def challenge_matrix_for_records(projects: pd.DataFrame, challenge: pd.DataFrame) -> np.ndarray:
    pivot = challenge.pivot(index="funding_year", columns="sdg", values="d0_goal_challenge_lag_mean")
    pivot = pivot.reindex(columns=SDG_ORDER)
    missing_years = sorted(set(projects["award_year"]) - set(pivot.index))
    if missing_years:
        raise ValueError(f"Missing SDSN years: {missing_years}")
    matrix = pivot.loc[projects["award_year"]].to_numpy(dtype=float)
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError("SDSN matrix contains invalid values")
    return matrix / matrix.sum(axis=1, keepdims=True)


def aggregate_family_matrices(
    data: pd.DataFrame,
    challenge: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    conserved = pd.to_numeric(data["project_family_weight"], errors="raise").to_numpy(float)
    supply_record = fractional_matrix(data["sdg_codes"], SDG_ORDER, row_weights=conserved)
    if (supply_record.sum(axis=1) <= 0).any():
        raise ValueError("A project record lacks a valid study SDG")
    challenge_record = challenge_matrix_for_records(data, challenge) * conserved[:, None]
    advanced = data["action_codes"].map(lambda codes: bool(set(codes) & ADVANCED_ACTIONS)).to_numpy(float)
    action_record = supply_record * advanced[:, None]

    families = sorted(data["project_family_id"].astype(str).unique().tolist())
    family_index = {family: idx for idx, family in enumerate(families)}
    row_index = data["project_family_id"].astype(str).map(family_index).to_numpy(int)
    supply_family = np.zeros((len(families), len(SDG_ORDER)), dtype=float)
    challenge_family = np.zeros_like(supply_family)
    action_family = np.zeros_like(supply_family)
    np.add.at(supply_family, row_index, supply_record)
    np.add.at(challenge_family, row_index, challenge_record)
    np.add.at(action_family, row_index, action_record)

    family_weight_sum = (
        data.assign(project_family_id=data["project_family_id"].astype(str))
        .groupby("project_family_id", observed=True)["project_family_weight"]
        .sum()
        .reindex(families)
        .to_numpy(float)
    )
    if not np.allclose(family_weight_sum, 1.0, atol=1e-10):
        raise ValueError("Project-family weights do not close to one")
    if not np.allclose(supply_family.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("Family supply vectors do not close to one")
    if not np.allclose(challenge_family.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("Family challenge vectors do not close to one")
    if (action_family < -1e-12).any() or (action_family - supply_family > 1e-12).any():
        raise ValueError("Action numerator lies outside its supply denominator")
    return supply_family, challenge_family, action_family, families


def point_estimates(
    agency: str,
    supply_family: np.ndarray,
    challenge_family: np.ndarray,
    action_family: np.ndarray,
) -> pd.DataFrame:
    supply = close_composition(supply_family.mean(axis=0))
    challenge = close_composition(challenge_family.mean(axis=0))
    mismatch = clr(supply) - clr(challenge)
    denominator = supply_family.sum(axis=0)
    action_share = np.divide(
        action_family.sum(axis=0),
        denominator,
        out=np.full(len(SDG_ORDER), np.nan),
        where=denominator > 0,
    )
    squared = np.square(mismatch)
    contribution_share = squared / squared.sum()
    return pd.DataFrame(
        {
            "agency": agency,
            "sdg": SDG_ORDER,
            "project_family_support": denominator,
            "supply_share": supply,
            "challenge_share": challenge,
            "clr_mismatch": mismatch,
            "advanced_action_share": action_share,
            "aitchison_contribution_share": contribution_share,
        }
    )


def bootstrap_joint(
    agency: str,
    supply_family: np.ndarray,
    challenge_family: np.ndarray,
    action_family: np.ndarray,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n_families, n_sdgs = supply_family.shape
    probabilities = np.full(n_families, 1.0 / n_families)
    parts: list[pd.DataFrame] = []
    for start in range(0, N_BOOTSTRAP, 100):
        stop = min(start + 100, N_BOOTSTRAP)
        counts = rng.multinomial(n_families, probabilities, size=stop - start)
        supply_raw = np.einsum("ij,jk->ik", counts, supply_family, optimize=False)
        challenge_raw = np.einsum("ij,jk->ik", counts, challenge_family, optimize=False)
        action_raw = np.einsum("ij,jk->ik", counts, action_family, optimize=False)

        action_share = np.divide(
            action_raw,
            supply_raw,
            out=np.full_like(action_raw, np.nan, dtype=float),
            where=supply_raw > 0,
        )
        supply = np.maximum(supply_raw / n_families, EPSILON)
        challenge = np.maximum(challenge_raw / n_families, EPSILON)
        supply /= supply.sum(axis=1, keepdims=True)
        challenge /= challenge.sum(axis=1, keepdims=True)
        clr_supply = np.log(supply) - np.log(supply).mean(axis=1, keepdims=True)
        clr_challenge = np.log(challenge) - np.log(challenge).mean(axis=1, keepdims=True)
        mismatch = clr_supply - clr_challenge
        squared = np.square(mismatch)
        contribution = squared / squared.sum(axis=1, keepdims=True)

        rows = stop - start
        parts.append(
            pd.DataFrame(
                {
                    "agency": agency,
                    "bootstrap_id": np.repeat(np.arange(start + 1, stop + 1), n_sdgs),
                    "sdg": np.tile(SDG_ORDER, rows),
                    "clr_mismatch": mismatch.reshape(-1),
                    "advanced_action_share": action_share.reshape(-1),
                    "aitchison_contribution_share": contribution.reshape(-1),
                    "resampling_unit": "project_family_id",
                    "n_project_families": n_families,
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def summarize_intervals(draws: pd.DataFrame) -> pd.DataFrame:
    grouped = draws.groupby(["agency", "sdg"], observed=True)
    rows = []
    for keys, part in grouped:
        agency, sdg = keys
        rows.append(
            {
                "agency": agency,
                "sdg": sdg,
                "clr_ci_low": float(part["clr_mismatch"].quantile(0.025)),
                "clr_ci_high": float(part["clr_mismatch"].quantile(0.975)),
                "action_ci_low": float(part["advanced_action_share"].quantile(0.025)),
                "action_ci_high": float(part["advanced_action_share"].quantile(0.975)),
                "bootstrap_valid_n": int(part["advanced_action_share"].notna().sum()),
            }
        )
    return pd.DataFrame(rows)


def recompute_top10_city_share(projects: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    columns = [
        "institution_city",
        "institution_region",
        "longitude_wgs84",
        "latitude_wgs84",
        "city_weight",
        "sdg_codes",
    ]
    for agency, data in projects.items():
        for row in data[columns].itertuples(index=False):
            codes = [code for code in dict.fromkeys(row.sdg_codes) if code in SDG_ORDER]
            if not codes or not np.isfinite(row.longitude_wgs84) or not np.isfinite(row.latitude_wgs84):
                continue
            city_id = f"{agency}|{str(row.institution_region).strip()}|{str(row.institution_city).strip()}"
            contribution = float(row.city_weight) / len(codes)
            for sdg in codes:
                rows.append(
                    {
                        "agency": agency,
                        "city_id": city_id,
                        "sdg": sdg,
                        "fractional_project_support": contribution,
                    }
                )
    events = pd.DataFrame(rows)
    city = (
        events.groupby(["agency", "sdg", "city_id"], observed=True)["fractional_project_support"]
        .sum()
        .reset_index()
    )
    output = []
    for (agency, sdg), part in city.groupby(["agency", "sdg"], observed=True):
        values = part["fractional_project_support"].sort_values(ascending=False).to_numpy(float)
        output.append(
            {
                "agency": agency,
                "sdg": sdg,
                "top10_city_share": float(values[:10].sum() / values.sum()),
                "active_city_n": int((values > 0).sum()),
                "city_fractional_support": float(values.sum()),
            }
        )
    return pd.DataFrame(output)


def aggregate_family_features(
    projects: Mapping[str, pd.DataFrame],
    record_features: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}
    for agency, data in projects.items():
        features = record_features[agency].reset_index(drop=True).astype(float)
        conserved = pd.to_numeric(data["project_family_weight"], errors="raise").to_numpy(float)
        family_ids = data["project_family_id"].astype(str).reset_index(drop=True)
        weighted = features.mul(conserved, axis=0)
        weighted.insert(0, "project_family_id", family_ids)
        numerators = weighted.groupby("project_family_id", sort=False, observed=True).sum()
        denominators = (
            pd.DataFrame({"project_family_id": family_ids, "weight": conserved})
            .groupby("project_family_id", sort=False, observed=True)["weight"]
            .sum()
        )
        output[agency] = numerators.div(denominators, axis=0)
    return output


def build_entropy_sensitivity(
    projects: Mapping[str, pd.DataFrame],
    family_matrices: Mapping[str, tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    settings = AnalysisSettings(seed=SEED, bootstrap_resamples=N_BOOTSTRAP)
    record_features, _ = build_balance_features(projects)
    family_features = aggregate_family_features(projects, record_features)
    reference = 0.5 * (family_features["NSF"].mean(axis=0) + family_features["NSFC"].mean(axis=0))
    sensitivity_rows = []
    audit_rows = []
    summary_rows = []
    for agency in AGENCY_ORDER:
        frame = family_features[agency]
        weights, diagnostics = entropy_balance_to_reference(frame, reference, settings)
        weight_series = pd.Series(weights, index=frame.index.astype(str))
        supply_family, _, action_family, families = family_matrices[agency]
        aligned_weights = weight_series.reindex(families)
        if aligned_weights.isna().any():
            raise ValueError(f"{agency}: missing entropy weight for a family")
        w = aligned_weights.to_numpy(float)
        observed = action_family.sum(axis=0) / supply_family.sum(axis=0)
        balanced = (w @ action_family) / (w @ supply_family)
        for idx, sdg in enumerate(SDG_ORDER):
            sensitivity_rows.append(
                {
                    "agency": agency,
                    "sdg": sdg,
                    "action_share_observed": float(observed[idx]),
                    "action_share_entropy_balanced": float(balanced[idx]),
                    "balanced_minus_observed_pp": float(100 * (balanced[idx] - observed[idx])),
                }
            )
        before = frame.mean(axis=0)
        # `weights` follows `frame.index`; `w` has been reindexed to the sorted
        # family-matrix order and is used only for the matrix estimands.
        after = pd.Series(np.average(frame, axis=0, weights=weights), index=frame.columns)
        for feature in frame.columns:
            audit_rows.append(
                {
                    "agency": agency,
                    "feature": feature,
                    "before_mean": float(before[feature]),
                    "pooled_reference_mean": float(reference[feature]),
                    "after_mean": float(after[feature]),
                    "balance_error": float(after[feature] - reference[feature]),
                }
            )
        summary_rows.append({"agency": agency, "family_n": len(frame), **diagnostics})
    return pd.DataFrame(sensitivity_rows), pd.DataFrame(audit_rows), pd.DataFrame(summary_rows)


def select_labels(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["label_selected"] = True
    data["label_selection_reason"] = "All country-SDG units"
    contribution = data["aitchison_contribution_share"].to_numpy(float)
    data["label_font_size"] = np.select(
        [contribution >= 0.15, contribution >= 0.05, contribution >= 0.01],
        [7.3, 6.6, 5.9],
        default=5.2,
    )
    data["label_font_weight"] = np.where(contribution >= 0.05, "bold", "normal")
    return data


def size_for_contribution(percent: float | np.ndarray) -> float | np.ndarray:
    return 18.0 + 7.0 * np.asarray(percent)


def linewidth_for_top10(share: float | np.ndarray) -> float | np.ndarray:
    return 0.70 + 2.60 * np.asarray(share)


def crosscheck_formal(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    formal_b = pd.read_csv(FIGURE4B_FORMAL, encoding="utf-8-sig").rename(columns={"country": "agency"})
    formal_c = pd.read_csv(FIGURE4C_FORMAL, encoding="utf-8-sig").rename(columns={"country": "agency"})
    formal_city = pd.read_csv(FIGURE3D_CITY, encoding="utf-8-sig")
    formal_top10 = (
        formal_city.loc[formal_city["rank_within_sdg"].le(10)]
        .groupby(["agency", "sdg"], observed=True)["within_sdg_share"]
        .sum()
        .rename("formal_top10_city_share")
        .reset_index()
    )
    merged = (
        data.merge(
            formal_b[["agency", "sdg", "M_count", "ci_low", "ci_high"]],
            on=["agency", "sdg"],
            validate="one_to_one",
        )
        .merge(
            formal_c[["agency", "sdg", "contribution_share_count"]],
            on=["agency", "sdg"],
            validate="one_to_one",
        )
        .merge(formal_top10, on=["agency", "sdg"], validate="one_to_one")
    )
    comparisons = {
        "clr_mismatch_vs_Figure4b": ("clr_mismatch", "M_count", 1.0),
        "clr_ci_low_vs_Figure4b": ("clr_ci_low", "ci_low", 1.0),
        "clr_ci_high_vs_Figure4b": ("clr_ci_high", "ci_high", 1.0),
        "contribution_vs_Figure4c": (
            "aitchison_contribution_share",
            "contribution_share_count",
            0.01,
        ),
        "top10_share_vs_Figure3d": ("top10_city_share", "formal_top10_city_share", 1.0),
    }
    for metric, (current_col, formal_col, formal_scale) in comparisons.items():
        for row in merged.itertuples(index=False):
            current = float(getattr(row, current_col))
            formal = float(getattr(row, formal_col)) * formal_scale
            rows.append(
                {
                    "agency": row.agency,
                    "sdg": row.sdg,
                    "metric": metric,
                    "figure5e_value": current,
                    "formal_reference_value": formal,
                    "absolute_difference": abs(current - formal),
                }
            )
    return pd.DataFrame(rows)


def _candidate_offsets() -> list[tuple[float, float]]:
    return [
        (6, 6), (6, -8), (-6, 6), (-6, -8),
        (10, 13), (10, -15), (-10, 13), (-10, -15),
        (18, 2), (-18, 2), (20, 10), (-20, 10),
        (20, -10), (-20, -10), (3, 20), (3, -22),
        (-3, 20), (-3, -22), (28, 4), (-28, 4),
        (28, -8), (-28, -8), (14, 24), (-14, 24),
        (14, -26), (-14, -26),
    ]


def place_labels(ax: plt.Axes, data: pd.DataFrame) -> None:
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    occupied = []
    axes_box = ax.get_window_extent(renderer=renderer)
    ordered = data.loc[data["label_selected"]].sort_values(
        ["aitchison_contribution_share", "agency"], ascending=[False, True]
    )
    for row in ordered.itertuples(index=False):
        label = f"SDG{int(str(row.sdg)[1:])}"
        color = {"NSF": "#003366", "NSFC": "#8B0000"}[row.agency]
        fontsize = float(row.label_font_size)
        fontweight = str(row.label_font_weight)
        chosen = None
        best = None
        for dx, dy in _candidate_offsets():
            horizontal = "left" if dx >= 0 else "right"
            annotation = ax.annotate(
                label,
                (row.clr_mismatch, row.advanced_action_share * 100),
                xytext=(dx, dy),
                textcoords="offset points",
                ha=horizontal,
                va="center",
                fontsize=fontsize,
                fontweight=fontweight,
                color=color,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.28},
                arrowprops={"arrowstyle": "-", "color": color, "lw": 0.48, "alpha": 1.0},
                annotation_clip=True,
                zorder=6,
            )
            fig.canvas.draw()
            box = annotation.get_window_extent(renderer=renderer).expanded(1.03, 1.08)
            inside = axes_box.contains(box.x0, box.y0) and axes_box.contains(box.x1, box.y1)
            overlaps = [previous for previous in occupied if box.overlaps(previous)]
            collision = bool(overlaps)
            if inside and not collision:
                chosen = (annotation, box)
                break
            outside_penalty = (
                max(0.0, axes_box.x0 - box.x0)
                + max(0.0, box.x1 - axes_box.x1)
                + max(0.0, axes_box.y0 - box.y0)
                + max(0.0, box.y1 - axes_box.y1)
            )
            overlap_penalty = sum(
                max(0.0, min(box.x1, previous.x1) - max(box.x0, previous.x0))
                * max(0.0, min(box.y1, previous.y1) - max(box.y0, previous.y0))
                for previous in overlaps
            )
            score = outside_penalty * 1000.0 + overlap_penalty
            if best is None or score < best[0]:
                best = (score, dx, dy, horizontal)
            annotation.remove()
        if chosen is None:
            _, dx, dy, horizontal = best
            annotation = ax.annotate(
                label,
                (row.clr_mismatch, row.advanced_action_share * 100),
                xytext=(dx, dy),
                textcoords="offset points",
                ha=horizontal,
                va="center",
                fontsize=fontsize,
                fontweight=fontweight,
                color=color,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.28},
                arrowprops={"arrowstyle": "-", "color": color, "lw": 0.48, "alpha": 1.0},
                annotation_clip=True,
                zorder=6,
            )
            fig.canvas.draw()
            occupied.append(annotation.get_window_extent(renderer=renderer).expanded(1.03, 1.08))
        else:
            occupied.append(chosen[1])


def render_figure(data: pd.DataFrame) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(7.2, 4.8), facecolor="white")
    ax = fig.add_axes([0.115, 0.245, 0.855, 0.625])

    x_min_data = float(data["clr_ci_low"].min())
    x_max_data = float(data["clr_ci_high"].max())
    span = x_max_data - x_min_data
    x_pad = max(0.18, 0.06 * span)
    x_min, x_max = x_min_data - x_pad, x_max_data + x_pad
    y_max_data = float(data["action_ci_high"].max() * 100)
    y_max = max(10.0, math.ceil((y_max_data + 2.0) / 5.0) * 5.0)

    ax.axvspan(x_min, -0.5, color="#E4EDF5", zorder=0)
    ax.axvspan(-0.5, 0.5, color="#ECEFF1", zorder=0)
    ax.axvspan(0.5, x_max, color="#F6E4E4", zorder=0)
    ax.axvline(-0.5, color="#AAB5BC", lw=0.65, ls=(0, (2, 2)), zorder=1)
    ax.axvline(0.5, color="#AAB5BC", lw=0.65, ls=(0, (2, 2)), zorder=1)
    ax.axvline(0.0, color=FRAME_COLOR, lw=0.85, ls=(0, (4, 2)), zorder=1)

    for agency in AGENCY_ORDER:
        part = data.loc[data["agency"].eq(agency)].copy()
        color = AGENCY_COLORS[agency]
        x = part["clr_mismatch"].to_numpy(float)
        y = part["advanced_action_share"].to_numpy(float) * 100
        xerr = np.vstack([x - part["clr_ci_low"].to_numpy(float), part["clr_ci_high"].to_numpy(float) - x])
        yerr = np.vstack(
            [
                y - part["action_ci_low"].to_numpy(float) * 100,
                part["action_ci_high"].to_numpy(float) * 100 - y,
            ]
        )
        ax.errorbar(
            x,
            y,
            xerr=xerr,
            yerr=yerr,
            fmt="none",
            ecolor=color,
            elinewidth=0.70,
            capsize=1.8,
            capthick=0.70,
            alpha=0.62,
            zorder=2,
        )
        contribution_percent = part["aitchison_contribution_share"].to_numpy(float) * 100
        sizes = size_for_contribution(contribution_percent)
        ax.scatter(
            x,
            y,
            s=sizes,
            facecolor=color,
            edgecolor="white",
            linewidth=0.75,
            alpha=1.0,
            zorder=4,
        )
        ax.scatter(
            x,
            y,
            s=sizes + 40,
            facecolor="none",
            edgecolor=RING_COLOR,
            linewidth=linewidth_for_top10(part["top10_city_share"].to_numpy(float)),
            alpha=1.0,
            zorder=5,
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Research supply relative to SDG challenge\nCLR mismatch", labelpad=7)
    ax.set_ylabel("Projects reaching validation,\nimplementation or evaluation (%)", labelpad=7)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 2.5, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    ax.grid(True, which="major", color=GRID_COLOR, lw=0.35, alpha=1.0, zorder=0)
    ax.tick_params(colors=TEXT_COLOR, width=0.75, length=3.2, pad=3)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.85)
        spine.set_color(FRAME_COLOR)

    zone_y = 0.975
    left_center = (x_min + min(-0.5, x_max)) / 2
    mid_left, mid_right = max(x_min, -0.5), min(x_max, 0.5)
    right_center = (max(0.5, x_min) + x_max) / 2
    if x_min < -0.5:
        ax.text(left_center, zone_y, "Relatively lower", transform=ax.get_xaxis_transform(), ha="center", va="top", color=MUTED_TEXT, fontsize=6.5)
    if mid_right > mid_left:
        ax.text((mid_left + mid_right) / 2, zone_y, "Near alignment", transform=ax.get_xaxis_transform(), ha="center", va="top", color=MUTED_TEXT, fontsize=6.5)
    if x_max > 0.5:
        ax.text(right_center, zone_y, "Relatively higher", transform=ax.get_xaxis_transform(), ha="center", va="top", color=MUTED_TEXT, fontsize=6.5)

    place_labels(ax, data)

    fig.text(0.018, 0.965, "e", ha="left", va="top", fontsize=15, fontweight="bold", color="#111111")
    fig.text(0.082, 0.965, "SDG mismatch, action-stage reach and spatial concentration", ha="left", va="top", fontsize=10.5, fontweight="bold", color=TEXT_COLOR)
    fig.text(0.082, 0.918, "Observed project-family-conserved estimates; horizontal and vertical bars show 95% CIs", ha="left", va="top", fontsize=6.8, color=MUTED_TEXT)

    country_handles = [
        Line2D([], [], marker="o", linestyle="", markerfacecolor=NSF_COLOR, markeredgecolor="white", markersize=6.5, label="NSF"),
        Line2D([], [], marker="o", linestyle="", markerfacecolor=NSFC_COLOR, markeredgecolor="white", markersize=6.5, label="NSFC"),
    ]
    size_values = (5, 15, 30)
    size_handles = [
        Line2D([], [], marker="o", linestyle="", markerfacecolor="#AAB5BC", markeredgecolor="white", markersize=math.sqrt(float(size_for_contribution(v))) / 1.45, label=(f"Mismatch contribution {v}%" if idx == 0 else f"{v}%"))
        for idx, v in enumerate(size_values)
    ]
    ring_values = (0.30, 0.60, 0.80)
    ring_handles = [
        Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor=RING_COLOR, markeredgewidth=float(linewidth_for_top10(v)), markersize=7.0, label=f"{int(v * 100)}%")
        for v in ring_values
    ]
    legend1 = fig.legend(
        handles=country_handles + size_handles,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.083),
        ncol=5,
        frameon=False,
        handletextpad=0.45,
        columnspacing=1.15,
    )
    fig.add_artist(legend1)
    legend2 = fig.legend(
        handles=ring_handles,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.012),
        ncol=3,
        frameon=False,
        title="Share of each SDG's research supplied by its 10 leading cities",
        title_fontsize=6.5,
        handletextpad=0.50,
        columnspacing=1.25,
    )
    legend2.get_title().set_color(MUTED_TEXT)
    return fig


def save_exports(fig: plt.Figure, stem: Path) -> list[Path]:
    outputs = []
    for suffix in (".png", ".tiff", ".svg", ".pdf"):
        path = stem.with_suffix(suffix)
        kwargs: dict[str, object] = {"facecolor": "white"}
        if suffix in {".png", ".tiff"}:
            kwargs["dpi"] = 600
        if suffix == ".tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(path, **kwargs)
        outputs.append(path)
    return outputs


def write_provenance(projects: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    source_paths = {
        "NSF coded projects": WORKSPACE_ROOT / "框架内容初稿" / 'data' / "llm编码完数据" / "full_v3_5_2_combined_deepseek" / 'NSF_coding_results.csv',
        "NSFC coded projects": WORKSPACE_ROOT / "框架内容初稿" / 'data' / "llm编码完数据" / "full_v3_5_2_combined_deepseek" / 'NSFC_coding_results.csv',
        "NSF SDSN challenge": SDSN_ROOT / "NSF.csv",
        "NSFC SDSN challenge": SDSN_ROOT / "NSFC.csv",
        "Figure 4b formal cross-check": FIGURE4B_FORMAL,
        "Figure 4c formal cross-check": FIGURE4C_FORMAL,
        "Figure 3d formal cross-check": FIGURE3D_CITY,
    }
    roles = {
        "NSF coded projects": "Primary project-level source",
        "NSFC coded projects": "Primary project-level source",
        "NSF SDSN challenge": "Primary external challenge source",
        "NSFC SDSN challenge": "Primary external challenge source",
        "Figure 4b formal cross-check": "Numeric validation only",
        "Figure 4c formal cross-check": "Numeric validation only",
        "Figure 3d formal cross-check": "Numeric validation only",
    }
    rows = []
    for label, path in source_paths.items():
        stat = path.stat()
        rows.append(
            {
                "source": label,
                "role": roles[label],
                "path": str(path),
                "bytes": stat.st_size,
                "last_modified": pd.Timestamp(stat.st_mtime, unit="s").isoformat(),
            }
        )
    for agency, data in projects.items():
        rows.append(
            {
                "source": f"{agency} in-memory audit",
                "role": "Population audit",
                "path": "",
                "bytes": np.nan,
                "last_modified": f"records={len(data)}; families={data['project_family_id'].nunique()}",
            }
        )
    return pd.DataFrame(rows)


def build_qa_report(
    estimates: pd.DataFrame,
    draws: pd.DataFrame,
    sensitivity: pd.DataFrame,
    balance_audit: pd.DataFrame,
    balance_summary: pd.DataFrame,
    crosscheck: pd.DataFrame,
    outputs: Sequence[Path],
) -> str:
    key_unique = estimates[["agency", "sdg"]].drop_duplicates().shape[0]
    per_agency = estimates.groupby("agency", observed=True).size().to_dict()
    contribution_closure = estimates.groupby("agency", observed=True)["aitchison_contribution_share"].sum()
    family_support = estimates.groupby("agency", observed=True)["project_family_support"].sum()
    max_crosscheck = crosscheck.groupby("metric", observed=True)["absolute_difference"].max()
    max_balance_error = float(balance_audit["balance_error"].abs().max())
    max_sensitivity = float(sensitivity["balanced_minus_observed_pp"].abs().max())
    image_lines = []
    for path in outputs:
        if path.suffix.lower() in {".png", ".tiff"}:
            with Image.open(path) as image:
                image_lines.append(f"  - {path.name}: {image.width}×{image.height}px, mode={image.mode}")
        else:
            image_lines.append(f"  - {path.name}: {path.stat().st_size:,} bytes")
    checks = {
        "24 unique cells": key_unique == 24 and per_agency == {"NSF": 12, "NSFC": 12},
        "no missing estimates": not estimates.isna().any().any(),
        "NSF family support closes to 5000": abs(float(family_support["NSF"]) - 5000.0) < 1e-8,
        "NSFC family support closes to 5546": abs(float(family_support["NSFC"]) - 5546.0) < 1e-8,
        "contribution shares close to one": bool(np.allclose(contribution_closure.to_numpy(float), 1.0, atol=1e-10)),
        "action shares bounded": bool(estimates["advanced_action_share"].between(0, 1).all()),
        "top10 shares bounded": bool(estimates["top10_city_share"].between(0, 1).all()),
        "CI contains point": bool(
            estimates["clr_ci_low"].le(estimates["clr_mismatch"]).all()
            and estimates["clr_ci_high"].ge(estimates["clr_mismatch"]).all()
            and estimates["action_ci_low"].le(estimates["advanced_action_share"]).all()
            and estimates["action_ci_high"].ge(estimates["advanced_action_share"]).all()
        ),
        "2000 bootstrap draws per cell": bool(draws.groupby(["agency", "sdg"], observed=True).size().eq(N_BOOTSTRAP).all()),
        "formal point crosschecks": bool(
            crosscheck.loc[~crosscheck["metric"].str.contains("ci_"), "absolute_difference"].max() < 1e-9
        ),
        "formal CI crosschecks": bool(
            crosscheck.loc[crosscheck["metric"].str.contains("ci_"), "absolute_difference"].max() < 1e-9
        ),
        "entropy balance converged": bool(balance_summary["success"].astype(bool).all()),
        "exports non-empty": all(path.exists() and path.stat().st_size > 0 for path in outputs),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    lines = [
        f"# Figure 5e QA report — {status}",
        "",
        "## Scope and closure",
        f"- Unique country–SDG cells: {key_unique}; per agency: {per_agency}.",
        f"- Family-support closure: NSF={family_support['NSF']:.6f}; NSFC={family_support['NSFC']:.6f}.",
        f"- Mismatch-contribution closure: NSF={contribution_closure['NSF']:.12f}; NSFC={contribution_closure['NSFC']:.12f}.",
        f"- Bootstrap rows: {len(draws):,}; resamples per cell={N_BOOTSTRAP}.",
        "",
        "## Cross-panel numeric validation",
    ]
    for metric, value in max_crosscheck.items():
        lines.append(f"- {metric}: max absolute difference={value:.3e}.")
    lines.extend(
        [
            "",
            "## Sensitivity and balance",
            f"- Maximum absolute entropy-balance error: {max_balance_error:.3e}.",
            f"- Maximum balanced-minus-observed action-share change: {max_sensitivity:.3f} percentage points.",
            "- Entropy-balanced estimates are saved as sensitivity results and are not overplotted in the main panel.",
            "",
            "## Output inspection",
            *image_lines,
            "",
            "## Automated checks",
        ]
    )
    for name, passed in checks.items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "- The panel jointly describes compositional mismatch, action-stage reach and spatial concentration.",
            "- It does not estimate a causal effect of research supply on national SDG outcomes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    for directory in (DATA_DIR, FIGURE_DIR, QA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    projects_all, _ = load_projects()
    projects = {
        agency: data.loc[data["award_year"].between(ANALYSIS_START, ANALYSIS_END)].copy()
        for agency, data in projects_all.items()
    }
    family_matrices: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]] = {}
    estimate_parts = []
    draw_parts = []
    seed_sequences = np.random.SeedSequence(SEED).spawn(len(AGENCY_ORDER))
    for agency, seed_sequence in zip(AGENCY_ORDER, seed_sequences, strict=True):
        challenge = load_challenge(agency)
        matrices = aggregate_family_matrices(projects[agency], challenge)
        family_matrices[agency] = matrices
        estimate_parts.append(point_estimates(agency, matrices[0], matrices[1], matrices[2]))
        draw_parts.append(
            bootstrap_joint(
                agency,
                matrices[0],
                matrices[1],
                matrices[2],
                np.random.Generator(np.random.PCG64(seed_sequence)),
            )
        )
    estimates = pd.concat(estimate_parts, ignore_index=True)
    draws = pd.concat(draw_parts, ignore_index=True)
    intervals = summarize_intervals(draws)
    concentration = recompute_top10_city_share(projects)
    estimates = (
        estimates.merge(intervals, on=["agency", "sdg"], validate="one_to_one")
        .merge(concentration, on=["agency", "sdg"], validate="one_to_one")
    )
    estimates["mismatch_class"] = estimates["clr_mismatch"].map(classify_mismatch)
    estimates = select_labels(estimates)
    estimates["display_marker_area_points2"] = size_for_contribution(
        estimates["aitchison_contribution_share"].to_numpy(float) * 100
    )
    estimates["display_ring_linewidth_points"] = linewidth_for_top10(
        estimates["top10_city_share"].to_numpy(float)
    )

    sensitivity, balance_audit, balance_summary = build_entropy_sensitivity(projects, family_matrices)
    crosscheck = crosscheck_formal(estimates)
    provenance = write_provenance(projects)

    estimate_path = DATA_DIR / 'Figure5e_country_SDG_composite_coordinate_estimates.csv'
    draws_path = DATA_DIR / 'Figure5e_project_families_Bootstrap_long_table.csv'
    sensitivity_path = DATA_DIR / 'Figure5e_entropy_balancing_sensitivity.csv'
    balance_audit_path = DATA_DIR / 'Figure5e_entropy_balancing_audit.csv'
    balance_summary_path = DATA_DIR / 'Figure5e_entropy_balancing_summary.csv'
    crosscheck_path = DATA_DIR / 'Figure5e_cross_figure_value_check.csv'
    provenance_path = DATA_DIR / 'Figure5e_data_sources_and_versions.csv'
    for frame, path in (
        (estimates, estimate_path),
        (draws, draws_path),
        (sensitivity, sensitivity_path),
        (balance_audit, balance_audit_path),
        (balance_summary, balance_summary_path),
        (crosscheck, crosscheck_path),
        (provenance, provenance_path),
    ):
        frame.to_csv(path, index=False, encoding="utf-8-sig")

    fig = render_figure(estimates)
    outputs = save_exports(fig, FIGURE_DIR / "Figure5e_结构偏离—行动推进综合坐标图")
    fig.savefig(QA_DIR / 'Figure5e_QApreview.png', dpi=600, facecolor="white")
    plt.close(fig)

    report = build_qa_report(
        estimates,
        draws,
        sensitivity,
        balance_audit,
        balance_summary,
        crosscheck,
        outputs,
    )
    (QA_DIR / "Figure5e_QA报告.md").write_text(report, encoding="utf-8")
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "matplotlib": mpl.__version__,
        "seed": SEED,
        "bootstrap_resamples": N_BOOTSTRAP,
        "script": str(Path(__file__).resolve()),
    }
    (QA_DIR / "Figure5e_运行环境.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(report)


if __name__ == "__main__":
    main()
