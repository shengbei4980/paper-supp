from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import sparse


WORKSPACE = Path(r"E:\可持续发展目标基金")
FIGURE_ROOT = WORKSPACE / "定稿撰写" / "成图"
CONTROL_CODE = FIGURE_ROOT / "figure2-figure5制作总控" / "代码"
if str(CONTROL_CODE) not in sys.path:
    sys.path.insert(0, str(CONTROL_CODE))

from figure_common import (  # noqa: E402
    A_ORDER,
    L_ORDER,
    AnalysisSettings,
    build_balance_features,
    entropy_balance_to_reference,
    load_projects,
)


ROOT = FIGURE_ROOT / "figure5" / "figure5d" / "正式版_镜像离散行动边界脊线图"
DATA_DIR = ROOT / "数据"
OUTPUT_DIR = ROOT / "出图"
QA_DIR = ROOT / "QA"
LABEL_DICTIONARY_PATH = FIGURE_ROOT / "figure5" / "数据" / "figure5_labels.csv"

CLASSIFICATION_PATH = (
    FIGURE_ROOT
    / "figure4"
    / "figure4b"
    / "配对CLR偏离诊断与稳定性分类"
    / "方案B_配对森林—跨国差值轨道版"
    / "数据"
    / "Figure4b_B_country_estimates.csv"
)

CLASS_ORDER = (
    "Relative lower research supply",
    "Near alignment",
    "Relative higher research supply",
)
CLASS_ACCENTS = {
    CLASS_ORDER[0]: "#7D96A7",
    CLASS_ORDER[1]: "#8D9398",
    CLASS_ORDER[2]: "#7D96A7",
}

NSF_COLOR = "#4D9BC8"
NSFC_COLOR = "#E27D70"
TEXT_COLOR = "#25313B"
MUTED_TEXT = "#6E7982"
GRID_COLOR = "#DCE3E7"
FRAME_COLOR = "#657680"
STABLE_COLOR = "#1F2D36"
SUPPORT_COLOR = "#AAB5BC"
LOW_SUPPORT_ESS = 10.0
LIMITED_EVIDENCE_ALPHA = 0.86
LIMITED_EVIDENCE_LINEWIDTH = 0.90


def _load_code_labels(level: str, codes: tuple[str, ...]) -> dict[str, str]:
    """Load verbatim labels from the formal Figure 5 coding dictionary."""
    dictionary = pd.read_csv(LABEL_DICTIONARY_PATH)
    subset = dictionary.loc[dictionary["level"].eq(level), ["code", "label"]].copy()
    if subset["code"].duplicated().any():
        duplicates = subset.loc[subset["code"].duplicated(), "code"].tolist()
        raise ValueError(f"Duplicate {level} labels in coding dictionary: {duplicates}")
    mapping = dict(zip(subset["code"], subset["label"]))
    missing = [code for code in codes if code not in mapping]
    if missing:
        raise ValueError(f"Missing {level} labels in coding dictionary: {missing}")
    return {code: str(mapping[code]) for code in codes}


L_LABELS = _load_code_labels("Intervention", tuple(L_ORDER))
A_LABELS = _load_code_labels("Action stage", tuple(A_ORDER))

SETTINGS = AnalysisSettings(seed=20260824, bootstrap_resamples=2_000)

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.2,
        "axes.titlesize": 7.1,
        "axes.labelsize": 6.4,
        "xtick.labelsize": 5.6,
        "ytick.labelsize": 5.35,
        "legend.fontsize": 5.2,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.linewidth": 0.7,
        "legend.frameon": False,
    }
)


def classify_mismatch(value: float, threshold: float = 0.5) -> str:
    if value <= -threshold:
        return CLASS_ORDER[0]
    if value >= threshold:
        return CLASS_ORDER[2]
    return CLASS_ORDER[1]


def cell_metadata() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cell_index = 0
    for class_index, class_name in enumerate(CLASS_ORDER):
        for intervention_index, intervention in enumerate(L_ORDER):
            for action_index, action_stage in enumerate(A_ORDER):
                rows.append(
                    {
                        "cell_index": cell_index,
                        "class_index": class_index,
                        "intervention_index": intervention_index,
                        "action_index": action_index,
                        "mismatch_class": class_name,
                        "intervention": intervention,
                        "intervention_label": L_LABELS[intervention],
                        "action_stage": action_stage,
                        "action_stage_label": A_LABELS[action_stage],
                    }
                )
                cell_index += 1
    return pd.DataFrame(rows)


def _family_id_series(data: pd.DataFrame) -> pd.Series:
    return data["project_family_id"].astype(str).rename("project_family_id")


def aggregate_family_features(
    projects: Mapping[str, pd.DataFrame],
    record_features: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}
    for agency, data in projects.items():
        features = record_features[agency].reset_index(drop=True).astype(float)
        if len(features) != len(data):
            raise ValueError(f"{agency}: feature rows do not match project rows")
        weights = pd.to_numeric(data["project_family_weight"], errors="raise").to_numpy(float)
        family_ids = _family_id_series(data).reset_index(drop=True)
        weighted = features.mul(weights, axis=0)
        weighted.insert(0, "project_family_id", family_ids)
        numerators = weighted.groupby("project_family_id", sort=False, observed=True).sum()
        denominators = (
            pd.DataFrame({"project_family_id": family_ids, "weight": weights})
            .groupby("project_family_id", sort=False, observed=True)["weight"]
            .sum()
        )
        output[agency] = numerators.div(denominators, axis=0)
    return output


def build_family_balance(
    projects: Mapping[str, pd.DataFrame],
    settings: AnalysisSettings = SETTINGS,
) -> tuple[dict[str, pd.Series], pd.DataFrame, pd.DataFrame]:
    record_features, _ = build_balance_features(projects)
    family_features = aggregate_family_features(projects, record_features)
    reference = 0.5 * (
        family_features["NSF"].mean(axis=0) + family_features["NSFC"].mean(axis=0)
    )
    family_weights: dict[str, pd.Series] = {}
    audit_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for agency in ("NSF", "NSFC"):
        frame = family_features[agency]
        weights, diagnostics = entropy_balance_to_reference(frame, reference, settings)
        family_weights[agency] = pd.Series(weights, index=frame.index, name="entropy_weight")
        before = frame.mean(axis=0)
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
    return family_weights, pd.DataFrame(audit_rows), pd.DataFrame(summary_rows)


def distribute_family_weights(
    projects: Mapping[str, pd.DataFrame],
    family_weights: Mapping[str, pd.Series],
) -> dict[str, np.ndarray]:
    output: dict[str, np.ndarray] = {}
    for agency, data in projects.items():
        assigned = _family_id_series(data).map(family_weights[agency])
        if assigned.isna().any():
            raise ValueError(f"{agency}: missing entropy weight for a project family")
        conserved = pd.to_numeric(data["project_family_weight"], errors="raise").to_numpy(float)
        output[agency] = assigned.to_numpy(float) * conserved
    return output


def load_latest_classification(path: Path = CLASSIFICATION_PATH) -> pd.DataFrame:
    data = pd.read_csv(path, encoding="utf-8-sig")
    if "agency" not in data.columns and "country" in data.columns:
        data = data.rename(columns={"country": "agency"})
    required = {"agency", "sdg", "M_count"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Classification file lacks columns: {sorted(missing)}")
    data["M_count"] = pd.to_numeric(data["M_count"], errors="raise")
    data["mismatch_class"] = data["M_count"].map(classify_mismatch)
    data["classification_basis"] = (
        "Count-weighted CLR point estimate; thresholds -0.5 and +0.5"
    )
    return data


def _class_maps(classification: pd.DataFrame) -> dict[str, dict[str, str]]:
    return {
        agency: dict(zip(frame["sdg"].astype(str), frame["mismatch_class"].astype(str)))
        for agency, frame in classification.groupby("agency", observed=True)
    }


def build_family_contribution_matrices(
    projects: Mapping[str, pd.DataFrame],
    record_weights: Mapping[str, np.ndarray],
    classification: pd.DataFrame,
    metadata: pd.DataFrame,
) -> tuple[dict[str, sparse.csr_matrix], dict[str, pd.DataFrame]]:
    class_maps = _class_maps(classification)
    class_index = {name: index for index, name in enumerate(CLASS_ORDER)}
    intervention_index = {code: index for index, code in enumerate(L_ORDER)}
    action_index = {code: index for index, code in enumerate(A_ORDER)}
    matrices: dict[str, sparse.csr_matrix] = {}
    family_tables: dict[str, pd.DataFrame] = {}

    for agency, data in projects.items():
        family_ids = pd.Index(_family_id_series(data).drop_duplicates(), name="project_family_id")
        family_row = {family_id: index for index, family_id in enumerate(family_ids)}
        rows: list[int] = []
        cols: list[int] = []
        values: list[float] = []
        for record_index, row in enumerate(data.itertuples(index=False)):
            record_weight = float(record_weights[agency][record_index])
            sdgs = [code for code in dict.fromkeys(row.sdg_codes) if code in class_maps[agency]]
            interventions = [
                code for code in dict.fromkeys(row.intervention_codes) if code in intervention_index
            ]
            actions = [code for code in dict.fromkeys(row.action_codes) if code in action_index]
            if record_weight <= 0 or not sdgs or not interventions or not actions:
                continue
            class_counts = {name: 0 for name in CLASS_ORDER}
            for sdg in sdgs:
                class_counts[class_maps[agency][sdg]] += 1
            family_position = family_row[str(row.project_family_id)]
            for class_name, count in class_counts.items():
                if count == 0:
                    continue
                class_fraction = count / len(sdgs)
                contribution = record_weight * class_fraction / (
                    len(interventions) * len(actions)
                )
                c_index = class_index[class_name]
                for intervention in interventions:
                    for action in actions:
                        cell = (
                            (c_index * len(L_ORDER) + intervention_index[intervention])
                            * len(A_ORDER)
                            + action_index[action]
                        )
                        rows.append(family_position)
                        cols.append(cell)
                        values.append(contribution)
        matrix = sparse.coo_matrix(
            (values, (rows, cols)),
            shape=(len(family_ids), len(metadata)),
            dtype=float,
        ).tocsr()
        matrices[agency] = matrix
        family_tables[agency] = pd.DataFrame(
            {"agency": agency, "project_family_id": family_ids.astype(str)}
        )
    return matrices, family_tables


def effective_sample_size(weights: np.ndarray) -> float:
    positive = np.asarray(weights, dtype=float)
    positive = positive[np.isfinite(positive) & (positive > 0)]
    if positive.size == 0:
        return 0.0
    return float(positive.sum() ** 2 / np.square(positive).sum())


def _totals_to_shares(totals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(totals, dtype=float)
    if array.ndim == 1:
        array = array[None, :]
    shaped = array.reshape(-1, len(CLASS_ORDER), len(L_ORDER), len(A_ORDER))
    class_denominator = shaped.sum(axis=(2, 3), keepdims=True)
    joint = np.divide(
        shaped,
        class_denominator,
        out=np.full_like(shaped, np.nan),
        where=class_denominator > 0,
    )
    intervention_denominator = shaped.sum(axis=3, keepdims=True)
    conditional = np.divide(
        shaped,
        intervention_denominator,
        out=np.full_like(shaped, np.nan),
        where=intervention_denominator > 0,
    )
    return joint, conditional


def estimate_cells(
    matrices: Mapping[str, sparse.csr_matrix],
    metadata: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    joint: dict[str, np.ndarray] = {}
    conditional: dict[str, np.ndarray] = {}
    support_rows: dict[str, list[dict[str, object]]] = {"NSF": [], "NSFC": []}
    for agency in ("NSF", "NSFC"):
        matrix = matrices[agency].tocsr()
        totals = np.asarray(matrix.sum(axis=0)).ravel()
        joint[agency], conditional[agency] = _totals_to_shares(totals)
        joint[agency] = joint[agency][0]
        conditional[agency] = conditional[agency][0]
        for class_position, class_name in enumerate(CLASS_ORDER):
            class_start = class_position * len(L_ORDER) * len(A_ORDER)
            class_total = float(totals[class_start : class_start + len(L_ORDER) * len(A_ORDER)].sum())
            for intervention_position, intervention in enumerate(L_ORDER):
                start = class_start + intervention_position * len(A_ORDER)
                family_contribution = np.asarray(
                    matrix[:, start : start + len(A_ORDER)].sum(axis=1)
                ).ravel()
                weighted_support = float(family_contribution.sum())
                support_rows[agency].append(
                    {
                        "mismatch_class": class_name,
                        "class_index": class_position,
                        "intervention": intervention,
                        "intervention_index": intervention_position,
                        f"{agency.lower()}_family_n": int(np.count_nonzero(family_contribution > 0)),
                        f"{agency.lower()}_weighted_support": weighted_support,
                        f"{agency.lower()}_ess": effective_sample_size(family_contribution),
                        f"{agency.lower()}_intervention_share": (
                            weighted_support / class_total if class_total > 0 else np.nan
                        ),
                    }
                )

    cells = metadata.copy()
    cells["nsf_joint_share"] = joint["NSF"].reshape(-1)
    cells["nsfc_joint_share"] = joint["NSFC"].reshape(-1)
    cells["nsf_probability"] = conditional["NSF"].reshape(-1)
    cells["nsfc_probability"] = conditional["NSFC"].reshape(-1)
    cells["difference_pp"] = 100.0 * (
        cells["nsf_probability"] - cells["nsfc_probability"]
    )
    support = pd.DataFrame(support_rows["NSF"]).merge(
        pd.DataFrame(support_rows["NSFC"]),
        on=["mismatch_class", "class_index", "intervention", "intervention_index"],
        how="outer",
        validate="one_to_one",
    )
    support["min_ess"] = support[["nsf_ess", "nsfc_ess"]].min(axis=1)
    support["low_support"] = support["min_ess"].lt(LOW_SUPPORT_ESS)
    cells = cells.merge(
        support,
        on=["mismatch_class", "class_index", "intervention", "intervention_index"],
        how="left",
        validate="many_to_one",
    )
    return cells, support


def bootstrap_stage_shares(
    matrices: Mapping[str, sparse.csr_matrix],
    metadata: pd.DataFrame,
    n_resamples: int = 2_000,
    seed: int = 20260824,
    batch_size: int = 100,
) -> dict[str, np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(seed))
    output = {
        "NSF": np.full((n_resamples, len(metadata)), np.nan, dtype=float),
        "NSFC": np.full((n_resamples, len(metadata)), np.nan, dtype=float),
        "difference_pp": np.full((n_resamples, len(metadata)), np.nan, dtype=float),
    }
    offset = 0
    while offset < n_resamples:
        count = min(batch_size, n_resamples - offset)
        batch: dict[str, np.ndarray] = {}
        for agency in ("NSF", "NSFC"):
            matrix = matrices[agency].tocsr()
            n_families = matrix.shape[0]
            resample_counts = rng.multinomial(
                n_families,
                np.full(n_families, 1.0 / n_families),
                size=count,
            )
            totals = np.asarray(resample_counts @ matrix)
            _, conditional = _totals_to_shares(totals)
            batch[agency] = conditional.reshape(count, -1)
            output[agency][offset : offset + count] = batch[agency]
        output["difference_pp"][offset : offset + count] = 100.0 * (
            batch["NSF"] - batch["NSFC"]
        )
        offset += count
    return output


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    output = np.full(values.shape, np.nan, dtype=float)
    valid = np.isfinite(values)
    if not valid.any():
        return output
    p = values[valid]
    order = np.argsort(p)
    ranked = p[order]
    adjusted_ranked = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted_ranked = np.minimum.accumulate(adjusted_ranked[::-1])[::-1]
    adjusted_ranked = np.clip(adjusted_ranked, 0.0, 1.0)
    adjusted = np.empty_like(adjusted_ranked)
    adjusted[order] = adjusted_ranked
    output[valid] = adjusted
    return output


def _nanpercentile_supported(values: np.ndarray, q: float) -> np.ndarray:
    """Column-wise percentile that leaves structurally unsupported cells missing."""
    values = np.asarray(values, dtype=float)
    output = np.full(values.shape[1], np.nan, dtype=float)
    supported = np.isfinite(values).any(axis=0)
    if supported.any():
        output[supported] = np.nanpercentile(values[:, supported], q, axis=0)
    return output


def summarize_bootstrap(cells: pd.DataFrame, bootstrap: Mapping[str, np.ndarray]) -> pd.DataFrame:
    result = cells.copy()
    for agency, prefix in (("NSF", "nsf"), ("NSFC", "nsfc")):
        values = bootstrap[agency]
        result[f"{prefix}_ci_low"] = _nanpercentile_supported(values, 2.5)
        result[f"{prefix}_ci_high"] = _nanpercentile_supported(values, 97.5)
    differences = bootstrap["difference_pp"]
    result["ci_low_pp"] = _nanpercentile_supported(differences, 2.5)
    result["ci_high_pp"] = _nanpercentile_supported(differences, 97.5)
    valid_n = np.isfinite(differences).sum(axis=0)
    nonpositive = np.sum(differences <= 0, axis=0)
    nonnegative = np.sum(differences >= 0, axis=0)
    p_value = 2.0 * np.minimum(
        (nonpositive + 1.0) / (valid_n + 1.0),
        (nonnegative + 1.0) / (valid_n + 1.0),
    )
    p_value = np.minimum(p_value, 1.0)
    p_value[valid_n == 0] = np.nan
    result["bootstrap_valid_n"] = valid_n
    result["bootstrap_p_value"] = p_value
    result["q_value"] = benjamini_hochberg(p_value)
    result["ci_excludes_zero"] = result["ci_low_pp"].gt(0) | result["ci_high_pp"].lt(0)
    result["stable_cell"] = (
        ~result["low_support"]
        & result["ci_excludes_zero"]
        & result["q_value"].lt(SETTINGS.alpha)
    )
    result["classification_basis"] = (
        "Count-weighted CLR point estimate; thresholds -0.5 and +0.5"
    )
    return result


def _support_sizes(values: np.ndarray) -> np.ndarray:
    transformed = np.log10(1.0 + np.maximum(np.asarray(values, dtype=float), 0.0))
    maximum = float(np.nanmax(transformed)) if np.isfinite(transformed).any() else 0.0
    scaled = transformed / maximum if maximum > 0 else transformed
    return 10.0 + 48.0 * scaled


def render_figure(cells: pd.DataFrame, support: pd.DataFrame) -> plt.Figure:
    fig = plt.figure(figsize=(7.2, 7.35), facecolor="white")
    grid = fig.add_gridspec(
        3,
        1,
        left=0.355,
        right=0.955,
        bottom=0.205,
        top=0.855,
        hspace=0.40,
    )
    fig.text(0.018, 0.970, "d", fontsize=13, fontweight="bold", color=TEXT_COLOR, va="top")
    fig.text(
        0.055,
        0.970,
        "Stated action-stage boundaries across intervention modes",
        fontsize=10.1,
        fontweight="bold",
        color=TEXT_COLOR,
        va="top",
    )
    fig.text(
        0.055,
        0.938,
        "Mirrored ridges show the highest explicitly stated action stage after Target- and award-time entropy balancing",
        fontsize=5.85,
        color=MUTED_TEXT,
        va="top",
    )
    fig.text(
        0.055,
        0.913,
        "Mismatch classes: count-weighted CLR (thresholds −0.5 and +0.5); ridge area within each intervention mode = 100%",
        fontsize=5.25,
        color=MUTED_TEXT,
        va="top",
    )

    finite_probabilities = pd.concat(
        [cells["nsf_ci_high"], cells["nsfc_ci_high"]], ignore_index=True
    ).to_numpy(float)
    finite_probabilities = finite_probabilities[np.isfinite(finite_probabilities)]
    maximum_probability = float(np.nanmax(finite_probabilities)) if finite_probabilities.size else 1.0
    ridge_scale = 0.46 / max(maximum_probability, 0.05)
    support_size_map = dict(
        zip(
            list(zip(support["mismatch_class"], support["intervention"])),
            _support_sizes(support["min_ess"].to_numpy(float)),
        )
    )

    axes: list[plt.Axes] = []
    stage_x = np.arange(1, len(A_ORDER) + 1, dtype=float)
    row_positions = np.arange(len(L_ORDER) - 1, -1, -1, dtype=float)
    for class_index, class_name in enumerate(CLASS_ORDER):
        ax = fig.add_subplot(grid[class_index, 0])
        axes.append(ax)
        ax.axvspan(0.5, 2.5, color="#F1F5F7", zorder=0)
        ax.axvspan(2.5, 4.5, color="#F3F3F0", zorder=0)
        ax.axvspan(4.5, 7.5, color="#F7F3F0", zorder=0)
        part_class = cells.loc[cells["mismatch_class"].eq(class_name)].copy()
        for intervention_index, intervention in enumerate(L_ORDER):
            baseline = row_positions[intervention_index]
            part = (
                part_class.loc[part_class["intervention"].eq(intervention)]
                .sort_values("action_index")
                .copy()
            )
            if len(part) != len(A_ORDER):
                raise ValueError(f"Incomplete ridge for {class_name}, {intervention}")
            low_support = bool(part["low_support"].iloc[0])
            nsf = part["nsf_probability"].to_numpy(float)
            nsfc = part["nsfc_probability"].to_numpy(float)
            nsf_low = part["nsf_ci_low"].to_numpy(float)
            nsf_high = part["nsf_ci_high"].to_numpy(float)
            nsfc_low = part["nsfc_ci_low"].to_numpy(float)
            nsfc_high = part["nsfc_ci_high"].to_numpy(float)
            ax.hlines(baseline, 0.55, 7.45, color=GRID_COLOR, linewidth=0.42, zorder=1)
            if not low_support:
                ax.fill_between(
                    stage_x,
                    baseline + nsf_low * ridge_scale,
                    baseline + nsf_high * ridge_scale,
                    step="mid",
                    color=NSF_COLOR,
                    alpha=0.14,
                    linewidth=0,
                    zorder=2,
                )
                ax.fill_between(
                    stage_x,
                    baseline - nsfc_high * ridge_scale,
                    baseline - nsfc_low * ridge_scale,
                    step="mid",
                    color=NSFC_COLOR,
                    alpha=0.14,
                    linewidth=0,
                    zorder=2,
                )
                ax.fill_between(
                    stage_x,
                    baseline,
                    baseline + nsf * ridge_scale,
                    step="mid",
                    color=NSF_COLOR,
                    alpha=0.68,
                    linewidth=0,
                    zorder=3,
                )
                ax.fill_between(
                    stage_x,
                    baseline - nsfc * ridge_scale,
                    baseline,
                    step="mid",
                    color=NSFC_COLOR,
                    alpha=0.68,
                    linewidth=0,
                    zorder=3,
                )
            ax.step(
                stage_x,
                baseline + nsf * ridge_scale,
                where="mid",
                color=NSF_COLOR,
                linewidth=0.85 if not low_support else LIMITED_EVIDENCE_LINEWIDTH,
                alpha=0.92 if not low_support else LIMITED_EVIDENCE_ALPHA,
                zorder=4,
            )
            ax.step(
                stage_x,
                baseline - nsfc * ridge_scale,
                where="mid",
                color=NSFC_COLOR,
                linewidth=0.85 if not low_support else LIMITED_EVIDENCE_LINEWIDTH,
                alpha=0.92 if not low_support else LIMITED_EVIDENCE_ALPHA,
                zorder=4,
            )
            stable = part.loc[part["stable_cell"]].copy()
            for row in stable.itertuples(index=False):
                x = float(row.action_index + 1)
                if row.difference_pp >= 0:
                    start = baseline + float(row.nsf_probability) * ridge_scale + 0.025
                    ax.vlines(x, start, start + 0.085, color=STABLE_COLOR, linewidth=0.85, zorder=6)
                else:
                    start = baseline - float(row.nsfc_probability) * ridge_scale - 0.025
                    ax.vlines(x, start - 0.085, start, color=STABLE_COLOR, linewidth=0.85, zorder=6)
            support_row = support.loc[
                support["mismatch_class"].eq(class_name)
                & support["intervention"].eq(intervention)
            ].iloc[0]
            marker_size = support_size_map[(class_name, intervention)]
            ax.scatter(
                [7.72],
                [baseline],
                s=marker_size,
                facecolor="white" if bool(support_row.low_support) else SUPPORT_COLOR,
                edgecolor=FRAME_COLOR,
                linewidth=0.65,
                alpha=0.95,
                zorder=5,
            )
            effective_count = float(support_row.min_ess)
            effective_count_label = (
                f"{effective_count:.1f}" if effective_count < 10 else f"{effective_count:.0f}"
            )
            ax.text(
                7.90,
                baseline,
                effective_count_label,
                fontsize=5.0,
                color=TEXT_COLOR,
                ha="left",
                va="center",
                zorder=6,
            )

        stable_class = part_class.loc[part_class["stable_cell"]].copy()
        stable_class["abs_difference"] = stable_class["difference_pp"].abs()
        for row in stable_class.nlargest(3, "abs_difference").itertuples(index=False):
            baseline = row_positions[int(row.intervention_index)]
            x = float(row.action_index + 1)
            if row.difference_pp >= 0:
                y = baseline + float(row.nsf_probability) * ridge_scale + 0.13
                va = "bottom"
            else:
                y = baseline - float(row.nsfc_probability) * ridge_scale - 0.13
                va = "top"
            ax.text(
                x,
                y,
                f"{row.intervention}·{row.action_stage} {row.difference_pp:+.0f}",
                ha="center",
                va=va,
                fontsize=5.0,
                fontweight="bold",
                color=STABLE_COLOR,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.45},
                zorder=7,
            )

        ax.set_xlim(0.5, 8.30)
        ax.set_ylim(-0.55, 8.55)
        ax.set_yticks(
            row_positions,
            [f"{code}  {L_LABELS[code]}" for code in L_ORDER],
        )
        ax.set_xticks(stage_x, A_ORDER)
        ax.xaxis.set_ticks_position("top")
        ax.tick_params(axis="x", length=2.5, pad=1.2, colors=TEXT_COLOR)
        ax.tick_params(axis="y", length=0, pad=4, colors=TEXT_COLOR)
        ax.text(
            0.0,
            1.08,
            class_name,
            transform=ax.transAxes,
            fontsize=7.25,
            fontweight="bold",
            color=CLASS_ACCENTS[class_name],
            ha="left",
            va="bottom",
        )
        ax.text(
            7.84,
            8.50,
            "Effective\nproject count",
            fontsize=5.0,
            color=MUTED_TEXT,
            ha="center",
            va="bottom",
            linespacing=0.92,
        )
        for side in ("top", "right", "bottom", "left"):
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color(FRAME_COLOR)
            ax.spines[side].set_linewidth(0.65)

    axes[-1].set_xlabel("Highest stated research–action stage", labelpad=8, color=TEXT_COLOR)
    handles = [
        Patch(facecolor=NSF_COLOR, edgecolor=NSF_COLOR, alpha=0.60, label="NSF"),
        Patch(facecolor=NSFC_COLOR, edgecolor=NSFC_COLOR, alpha=0.60, label="NSFC"),
        Patch(facecolor="#CADDE8", edgecolor="none", alpha=0.45, label="Bootstrap 95% CI"),
        Line2D(
            [],
            [],
            color=NSF_COLOR,
            alpha=LIMITED_EVIDENCE_ALPHA,
            linewidth=LIMITED_EVIDENCE_LINEWIDTH,
            label="Limited evidence (<10 effective projects in either country)",
        ),
        Line2D([], [], color=STABLE_COLOR, marker="|", markersize=7, linestyle="None", label="Reliable stage-share difference"),
        Line2D(
            [],
            [],
            marker="o",
            markersize=5,
            markerfacecolor=SUPPORT_COLOR,
            markeredgecolor=FRAME_COLOR,
            linestyle="None",
            label="Effective project count (lower of NSF and NSFC)",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.55, 0.105),
        ncol=2,
        columnspacing=1.0,
        handletextpad=0.45,
    )
    fig.text(
        0.55,
        0.074,
        "  ·  ".join(f"{code} {A_LABELS[code]}" for code in A_ORDER[:4]),
        ha="center",
        va="center",
        fontsize=5.0,
        color=MUTED_TEXT,
    )
    fig.text(
        0.55,
        0.052,
        "  ·  ".join(f"{code} {A_LABELS[code]}" for code in A_ORDER[4:]),
        ha="center",
        va="center",
        fontsize=5.0,
        color=MUTED_TEXT,
    )
    fig.text(
        0.55,
        0.026,
        "Project-family bootstrap: 2,000 resamples; reliable differences require ≥10 effective projects in each country, a 95% CI excluding 0 and BH-FDR q < 0.05.",
        ha="center",
        va="center",
        fontsize=5.0,
        color=MUTED_TEXT,
    )
    return fig


def save_exports(fig: plt.Figure, stem: Path, dpi: int = 600) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [stem.with_suffix(suffix) for suffix in (".svg", ".pdf", ".png", ".tiff")]
    fig.savefig(outputs[0], bbox_inches="tight")
    fig.savefig(outputs[1], bbox_inches="tight")
    fig.savefig(outputs[2], dpi=dpi, bbox_inches="tight", facecolor="white")
    fig.savefig(outputs[3], dpi=dpi, bbox_inches="tight", facecolor="white")
    return outputs


def _write_source_notes(projects: Mapping[str, pd.DataFrame], summary: pd.DataFrame) -> None:
    lines = [
        "Figure5d 镜像离散行动边界脊线图数据来源与口径",
        "",
        "1. 项目编码数据：NSF_编码结果.csv与NSFC_编码结果.csv；观察窗为2015—2025。",
        "2. 偏离分类：正式Figure4b的项目数CLR点估计M_count，阈值为−0.5与+0.5。",
        "3. 熵平衡：在项目族层级平衡共同正式Target构成、2015—2017/2018—2020时段和线性年份。",
        "4. 条件构成：p(最高明确行动阶段 | 干预方式, 偏离类别, 国家)。",
        "5. 不确定性：项目族bootstrap 2,000次；完整189个国家差单元实施BH-FDR。",
        "6. 跨国证据量：每个偏离类别×干预方式报告NSF与NSFC中较低的有效项目数；任一国家低于10时保留估计并标记为证据有限。",
        "7. 行动阶段表示项目文本明确承诺的最高阶段，不表示真实实施或实际影响。",
        "",
    ]
    for agency in ("NSF", "NSFC"):
        record_n = len(projects[agency])
        family_n = projects[agency]["project_family_id"].nunique()
        row = summary.loc[summary["agency"].eq(agency)].iloc[0]
        lines.append(
            f"{agency}: {record_n:,} records; {family_n:,} project families; "
            f"entropy-balance ESS={row.effective_sample_size:.1f}; "
            f"max weight={row.max_weight:.2f}."
        )
    (DATA_DIR / "Figure5d_数据来源说明.txt").write_text("\n".join(lines), encoding="utf-8-sig")


def _qa_report(
    cells: pd.DataFrame,
    support: pd.DataFrame,
    balance_audit: pd.DataFrame,
    outputs: list[Path],
) -> str:
    joint_errors = []
    conditional_errors = []
    for column in ("nsf_joint_share", "nsfc_joint_share"):
        sums = cells.groupby("mismatch_class", observed=True)[column].sum()
        joint_errors.append(float(np.nanmax(np.abs(sums.to_numpy(float) - 1.0))))
    for column in ("nsf_probability", "nsfc_probability"):
        agency = column.removesuffix("_probability")
        supported = cells[f"{agency}_weighted_support"].gt(0)
        sums = cells.loc[supported].groupby(
            ["mismatch_class", "intervention"], observed=True
        )[column].sum()
        conditional_errors.append(float(np.nanmax(np.abs(sums.to_numpy(float) - 1.0))))
    identity_error = float(
        np.nanmax(
            np.abs(
                cells["difference_pp"].to_numpy(float)
                - 100.0
                * (
                    cells["nsf_probability"].to_numpy(float)
                    - cells["nsfc_probability"].to_numpy(float)
                )
            )
        )
    )
    max_balance_error = float(balance_audit["balance_error"].abs().max())
    comparable = cells["nsf_weighted_support"].gt(0) & cells["nsfc_weighted_support"].gt(0)
    comparable_valid_min = int(cells.loc[comparable, "bootstrap_valid_n"].min())
    report = [
        "# Figure5d 镜像离散行动边界脊线图 QA报告",
        "",
        f"- 单元完整性：{len(cells)}/189。",
        f"- 偏离类别×干预方式支持行：{len(support)}/27。",
        f"- 联合份额最大闭合误差：{max(joint_errors):.3e}。",
        f"- 条件阶段份额最大闭合误差：{max(conditional_errors):.3e}。",
        f"- 国家差恒等式最大误差：{identity_error:.3e} percentage points。",
        f"- 跨国可比单元：{int(comparable.sum())}/189；结构性无跨国支持单元：{int((~comparable).sum())}/189。",
        f"- 任一国家有效项目数不足10的脊线：{int(support['low_support'].sum())}/27。",
        f"- 可靠阶段差异：{int(cells['stable_cell'].sum())}/189。",
        f"- 跨国可比单元 Bootstrap有效次数最小值：{comparable_valid_min}/2,000。",
        f"- 项目族熵平衡最大绝对误差：{max_balance_error:.3e}。",
        f"- 输出格式：{', '.join(path.suffix for path in outputs)}。",
        "",
        "## 解释边界",
        "",
        "脊线连接离散阶段只表示最高明确行动阶段的构成轮廓；不表示单个项目真实经历连续阶段转移，也不构成项目质量或实际实施效果排序。",
    ]
    return "\n".join(report)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    projects, _ = load_projects()
    classification = load_latest_classification()
    family_weights, balance_audit, balance_summary = build_family_balance(projects)
    record_weights = distribute_family_weights(projects, family_weights)
    metadata = cell_metadata()
    matrices, family_tables = build_family_contribution_matrices(
        projects,
        record_weights,
        classification,
        metadata,
    )
    cells, support = estimate_cells(matrices, metadata)
    bootstrap = bootstrap_stage_shares(
        matrices,
        metadata,
        n_resamples=SETTINGS.bootstrap_resamples,
        seed=SETTINGS.seed,
    )
    cells = summarize_bootstrap(cells, bootstrap)

    cells.to_csv(
        DATA_DIR / "Figure5d_完整行动阶段份额与差值.csv",
        index=False,
        encoding="utf-8-sig",
    )
    support.to_csv(
        DATA_DIR / "Figure5d_干预方式支持度.csv",
        index=False,
        encoding="utf-8-sig",
    )
    balance_summary.to_csv(
        DATA_DIR / "Figure5d_项目族熵平衡汇总.csv",
        index=False,
        encoding="utf-8-sig",
    )
    balance_audit.to_csv(
        DATA_DIR / "Figure5d_项目族熵平衡审计.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.concat(family_tables.values(), ignore_index=True).to_csv(
        DATA_DIR / "Figure5d_项目族索引.csv",
        index=False,
        encoding="utf-8-sig",
    )
    _write_source_notes(projects, balance_summary)

    fig = render_figure(cells, support)
    outputs = save_exports(
        fig,
        OUTPUT_DIR / "Figure5d_镜像离散行动边界脊线图",
        dpi=600,
    )
    plt.close(fig)
    report = _qa_report(cells, support, balance_audit, outputs)
    (QA_DIR / "Figure5d_镜像离散脊线图_QA报告.md").write_text(
        report,
        encoding="utf-8-sig",
    )
    notes = (
        "# Figure5d 正式版执行说明\n\n"
        "本版本使用三类偏离分层的镜像离散脊线图，完整保留L01—L09与A01—A07。"
        "分析使用最新Figure4b M_count分类、项目族守恒、项目族熵平衡和2,000次项目族bootstrap。"
        "旧版Figure5d未被覆盖。\n"
    )
    (ROOT / "notes.md").write_text(notes, encoding="utf-8-sig")
    print(report)
    print(f"Outputs written to: {ROOT}")


if __name__ == "__main__":
    main()
