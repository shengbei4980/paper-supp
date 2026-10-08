from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp


WORKSPACE = Path(r"E:\可持续发展目标基金")
FIGURE_ROOT = WORKSPACE / "定稿撰写" / "成图"
CONTROL_ROOT = FIGURE_ROOT / "figure2-figure5制作总控"
DATA_ROOT = (
    WORKSPACE
    / "框架内容初稿"
    / 'data'
    / "llm编码完数据"
    / "full_v3_5_2_combined_deepseek"
)
PROJECT_PATHS = {
    "NSF": DATA_ROOT / 'NSF_coding_results.csv',
    "NSFC": DATA_ROOT / 'NSFC_coding_results.csv',
}
EXPECTED_ROWS = {"NSF": 6207, "NSFC": 5546}

SDG_ORDER = ("S02", "S03", "S06", "S07", "S09", "S10", "S11", "S12", "S13", "S15", "S16", "S17")
D_ORDER = tuple(f"D{i:02d}" for i in range(1, 7))
N_ORDER = tuple(f"N{i:02d}" for i in range(1, 20))
P_ORDER = tuple(f"P{i:02d}" for i in range(1, 9))
O_ORDER = tuple(f"O{i:02d}" for i in range(1, 13))
K_ORDER = tuple(f"K{i:02d}" for i in range(1, 7))
L_ORDER = tuple(f"L{i:02d}" for i in range(1, 10))
A_ORDER = tuple(f"A{i:02d}" for i in range(1, 8))
PERIOD_ORDER = ("2015–2017", "2018–2020", "2021–2025")

NSF_COLOR = "#003366"
NSFC_COLOR = "#8B0000"
SHARED_COLOR = "#59636E"
TEXT_COLOR = "#1F2933"
GRID_COLOR = "#D9DEE3"
LIGHT_GREY = "#EEF1F4"
MID_GREY = "#8A949E"

# Restrained parent-goal palette. Country identity is never encoded by these hues.
SDG_COLORS = {
    "S02": "#C99A3A",
    "S03": "#5E9A68",
    "S06": "#4C9BB5",
    "S07": "#D1A83B",
    "S09": "#C96D47",
    "S10": "#A56B9C",
    "S11": "#D38B3A",
    "S12": "#A78656",
    "S13": "#5D8A58",
    "S15": "#6FAE75",
    "S16": "#4D7399",
    "S17": "#5B6E9C",
}

FIELD_SPECS = {
    "SDG": ("sdg_goal_multi", "sdg_goal_multi_labels_en", "sdg_codes", SDG_ORDER),
    "Target": ("sdg_target_multi", "sdg_target_multi_labels_en", "target_codes", None),
    "Urban-need domain": (
        "urban_need_category_multi",
        "urban_need_category_multi_labels_en",
        "domain_codes",
        D_ORDER,
    ),
    "Urban-need topic": ("urban_need_topic_multi", "urban_need_topic_multi_labels_en", "need_codes", N_ORDER),
    "Pressure": ("urban_pressure_type", "urban_pressure_type_labels_en", "pressure_codes", P_ORDER),
    "Urban system": ("urban_system_type", "urban_system_type_labels_en", "system_codes", O_ORDER),
    "Knowledge task": ("knowledge_task_multi", "knowledge_task_multi_labels_en", "knowledge_codes", K_ORDER),
    "Primary knowledge task": (
        "primary_knowledge_task",
        "primary_knowledge_task_labels_en",
        "primary_knowledge_codes",
        K_ORDER,
    ),
    "Intervention": ("intervention_type_multi", "intervention_type_multi_labels_en", "intervention_codes", L_ORDER),
    "Primary intervention": (
        "primary_intervention_type",
        "primary_intervention_type_labels_en",
        "primary_intervention_codes",
        L_ORDER,
    ),
    "Action stage": ("research_action_stage", "research_action_stage_labels_en", "action_codes", A_ORDER),
}


@dataclass(frozen=True)
class AnalysisSettings:
    seed: int = 20260824
    bootstrap_resamples: int = 2_000
    balance_ridge: float = 1e-4
    balance_maxiter: int = 2_000
    balance_max_weight: float = 30.0
    alpha: float = 0.05


def split_codes(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    return list(dict.fromkeys(part.strip() for part in str(value).split("|") if part.strip()))


def _split_labels(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    return [part.strip() for part in str(value).split("|")]


def _period(year: int) -> str:
    if year <= 2017:
        return PERIOD_ORDER[0]
    if year <= 2020:
        return PERIOD_ORDER[1]
    return PERIOD_ORDER[2]


def _label_maps(frame: pd.DataFrame) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for level, (code_field, label_field, _, _) in FIELD_SPECS.items():
        mapping: dict[str, str] = {}
        for codes_raw, labels_raw in frame[[code_field, label_field]].itertuples(index=False, name=None):
            codes = split_codes(codes_raw)
            labels = _split_labels(labels_raw)
            for idx, code in enumerate(codes):
                label = labels[idx] if idx < len(labels) and labels[idx] else code
                mapping.setdefault(code, label)
        output[level] = mapping
    return output


def load_projects() -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, str]]]:
    required_base = [
        "country",
        "agency",
        "record_id",
        "award_year",
        "organization",
        "institution_city",
        "institution_region",
        "longitude_wgs84",
        "latitude_wgs84",
        "funding_amount_original",
        "funding_amount_unit",
        "text_fingerprint",
        "project_family_id",
        "project_family_weight",
        "award_record_weight",
        "_task_confidence_json",
        "_review_flags",
    ]
    coding_fields = sorted({field for spec in FIELD_SPECS.values() for field in spec[:2]})
    usecols = required_base + coding_fields
    projects: dict[str, pd.DataFrame] = {}
    frames = []
    for agency, path in PROJECT_PATHS.items():
        data = pd.read_csv(path, usecols=usecols, encoding="utf-8-sig", low_memory=False)
        if len(data) != EXPECTED_ROWS[agency]:
            raise ValueError(f"{agency}: expected {EXPECTED_ROWS[agency]:,} rows, found {len(data):,}")
        data["record_id"] = data["record_id"].astype(str)
        data["award_year"] = pd.to_numeric(data["award_year"], errors="raise").astype(int)
        data["project_family_weight"] = pd.to_numeric(data["project_family_weight"], errors="coerce").fillna(1.0)
        data["award_record_weight"] = pd.to_numeric(data["award_record_weight"], errors="coerce").fillna(1.0)
        data["funding_amount_original"] = pd.to_numeric(data["funding_amount_original"], errors="coerce")
        data["longitude_wgs84"] = pd.to_numeric(data["longitude_wgs84"], errors="coerce")
        data["latitude_wgs84"] = pd.to_numeric(data["latitude_wgs84"], errors="coerce")
        for _, (code_field, _, parsed_field, _) in FIELD_SPECS.items():
            data[parsed_field] = data[code_field].map(split_codes)
        data["agency"] = agency
        data["period"] = data["award_year"].map(_period)
        data["project_weight"] = 1.0
        data["city_weight"] = data["project_family_weight"] * data["award_record_weight"]
        projects[agency] = data
        frames.append(data)
    labels = _label_maps(pd.concat(frames, ignore_index=True))
    return projects, labels


def fractional_matrix(
    code_lists: Iterable[Sequence[str]],
    universe: Sequence[str],
    row_weights: Sequence[float] | np.ndarray | None = None,
) -> np.ndarray:
    lists = list(code_lists)
    index = {code: idx for idx, code in enumerate(universe)}
    matrix = np.zeros((len(lists), len(universe)), dtype=float)
    for row_idx, codes in enumerate(lists):
        unique = [code for code in dict.fromkeys(codes) if code in index]
        if not unique:
            continue
        contribution = 1.0 / len(unique)
        matrix[row_idx, [index[code] for code in unique]] = contribution
    if row_weights is not None:
        weights = np.asarray(row_weights, dtype=float)
        if weights.shape != (len(lists),):
            raise ValueError("row_weights length does not match code list length")
        matrix = matrix * weights[:, None]
    return matrix


def derive_need_domains(codes: Sequence[str]) -> set[str]:
    result = set()
    for code in codes:
        try:
            number = int(code[1:])
        except (ValueError, IndexError):
            continue
        if 1 <= number <= 3:
            result.add("D01")
        elif 4 <= number <= 6:
            result.add("D02")
        elif 7 <= number <= 10:
            result.add("D03")
        elif 11 <= number <= 13:
            result.add("D04")
        elif 14 <= number <= 16:
            result.add("D05")
        elif 17 <= number <= 19:
            result.add("D06")
    return result


def project_integrity_audit(projects: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    universes = {
        "sdg_codes": set(SDG_ORDER),
        "domain_codes": set(D_ORDER),
        "need_codes": set(N_ORDER),
        "pressure_codes": set(P_ORDER),
        "system_codes": set(O_ORDER),
        "knowledge_codes": set(K_ORDER),
        "primary_knowledge_codes": set(K_ORDER),
        "intervention_codes": set(L_ORDER),
        "primary_intervention_codes": set(L_ORDER),
        "action_codes": set(A_ORDER),
    }
    for agency, data in projects.items():
        checks: list[tuple[str, bool, str]] = []
        checks.append(("Expected row count", len(data) == EXPECTED_ROWS[agency], f"rows={len(data)}"))
        checks.append(("Unique record_id", not data["record_id"].duplicated().any(), "record_id duplicates"))
        checks.append(("Year range", data["award_year"].between(2015, 2025).all(), f"years={sorted(data['award_year'].unique())}"))
        for field, allowed in universes.items():
            empty = int(data[field].map(len).eq(0).sum())
            invalid = sorted({code for codes in data[field] for code in codes if code not in allowed})
            checks.append((f"{field} non-empty and valid", empty == 0 and not invalid, f"empty={empty}; invalid={invalid}"))

        target_parent_mismatch = 0
        need_parent_mismatch = 0
        for sdgs, targets, domains, needs in data[["sdg_codes", "target_codes", "domain_codes", "need_codes"]].itertuples(index=False, name=None):
            target_parents = {f"S{int(code.split('.')[0]):02d}" for code in targets}
            if target_parents != set(sdgs):
                target_parent_mismatch += 1
            if derive_need_domains(needs) != set(domains):
                need_parent_mismatch += 1
        checks.append(("Target parent SDG consistency", target_parent_mismatch == 0, f"mismatches={target_parent_mismatch}"))
        checks.append(("Need topic parent domain consistency", need_parent_mismatch == 0, f"mismatches={need_parent_mismatch}"))

        for metric, passed, detail in checks:
            rows.append({"agency": agency, "metric": metric, "passed": bool(passed), "detail": detail})
    return pd.DataFrame(rows)


def _target_sort_key(code: str) -> tuple[int, int, str]:
    goal, suffix = code.split(".", 1)
    numeric = int(suffix) if suffix.isdigit() else 100
    return int(goal), numeric, suffix


def build_balance_features(
    projects: Mapping[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], pd.Series]:
    observed = {
        agency: {code for codes in data["target_codes"] for code in codes}
        for agency, data in projects.items()
    }
    common_targets = sorted(observed["NSF"] & observed["NSFC"], key=_target_sort_key)
    # Drop one target and one period to avoid exact simplex collinearity.
    target_features = common_targets[:-1]
    feature_frames: dict[str, pd.DataFrame] = {}
    for agency, data in projects.items():
        target_matrix = fractional_matrix(data["target_codes"], common_targets)
        frame = pd.DataFrame(target_matrix[:, : len(target_features)], columns=[f"target:{x}" for x in target_features])
        frame["period:2015–2017"] = data["period"].eq(PERIOD_ORDER[0]).astype(float).to_numpy()
        frame["period:2018–2020"] = data["period"].eq(PERIOD_ORDER[1]).astype(float).to_numpy()
        year_scaled = (data["award_year"].to_numpy(dtype=float) - 2020.0) / 5.0
        frame["year:linear"] = year_scaled
        feature_frames[agency] = frame
    reference = 0.5 * (feature_frames["NSF"].mean(axis=0) + feature_frames["NSFC"].mean(axis=0))
    return feature_frames, reference


def entropy_balance_to_reference(
    features: pd.DataFrame,
    reference: pd.Series,
    settings: AnalysisSettings | None = None,
) -> tuple[np.ndarray, dict[str, float | int | bool | str]]:
    active = settings or AnalysisSettings()
    x = features.to_numpy(dtype=float)
    target = reference.loc[features.columns].to_numpy(dtype=float)
    scale = np.maximum(np.std(x, axis=0, ddof=0), 1e-3)
    z = (x - target[None, :]) / scale[None, :]

    def objective(lam: np.ndarray) -> tuple[float, np.ndarray]:
        logits = z @ lam
        lse = logsumexp(logits)
        probs = np.exp(logits - lse)
        value = float(lse - np.log(len(z)) + 0.5 * active.balance_ridge * np.dot(lam, lam))
        gradient = probs @ z + active.balance_ridge * lam
        return value, gradient

    result = minimize(
        fun=lambda lam: objective(lam)[0],
        x0=np.zeros(z.shape[1], dtype=float),
        jac=lambda lam: objective(lam)[1],
        method="L-BFGS-B",
        options={"maxiter": active.balance_maxiter, "ftol": 1e-12, "gtol": 1e-8},
    )
    logits = z @ result.x
    weights = np.exp(logits - logsumexp(logits)) * len(z)
    # Preserve every observed project in the weighted corpus. Extremely small
    # probabilities can underflow to exactly zero in double precision even
    # though entropy balancing has no zero-weight solution by construction.
    weights = np.maximum(weights, np.finfo(float).tiny)
    weights *= len(weights) / weights.sum()
    if float(weights.max()) > active.balance_max_weight:
        weights = np.minimum(weights, active.balance_max_weight)
        weights *= len(weights) / weights.sum()
    balanced = np.average(x, axis=0, weights=weights)
    error = balanced - target
    ess = float(weights.sum() ** 2 / np.square(weights).sum())
    diagnostics: dict[str, float | int | bool | str] = {
        "success": bool(result.success),
        "optimizer_message": str(result.message),
        "iterations": int(result.nit),
        "n_features": int(x.shape[1]),
        "effective_sample_size": ess,
        "effective_sample_fraction": ess / len(weights),
        "max_weight": float(weights.max()),
        "p99_weight": float(np.percentile(weights, 99)),
        "max_abs_balance_error": float(np.abs(error).max()),
        "mean_abs_balance_error": float(np.abs(error).mean()),
    }
    return weights, diagnostics


def pattern_bootstrap(
    matrix: np.ndarray,
    n_resamples: int,
    rng: np.random.Generator,
    base_weights: np.ndarray | None = None,
) -> np.ndarray:
    n = matrix.shape[0]
    if base_weights is None:
        probs = np.full(n, 1.0 / n)
    else:
        probs = np.asarray(base_weights, dtype=float)
        probs = probs / probs.sum()
    counts = rng.multinomial(n, probs, size=n_resamples)
    totals = counts.sum(axis=1, keepdims=True)
    return np.divide(counts @ matrix, totals, out=np.zeros((n_resamples, matrix.shape[1])), where=totals > 0)


def jsd_components(p: Sequence[float], q: Sequence[float]) -> np.ndarray:
    p_arr = np.asarray(p, dtype=float)
    q_arr = np.asarray(q, dtype=float)
    p_arr = p_arr / p_arr.sum()
    q_arr = q_arr / q_arr.sum()
    midpoint = 0.5 * (p_arr + q_arr)
    with np.errstate(divide="ignore", invalid="ignore"):
        left = np.where(p_arr > 0, 0.5 * p_arr * np.log(p_arr / midpoint), 0.0)
        right = np.where(q_arr > 0, 0.5 * q_arr * np.log(q_arr / midpoint), 0.0)
    return left + right


def overlap_coefficient(p: Sequence[float], q: Sequence[float]) -> float:
    p_arr = np.asarray(p, dtype=float)
    q_arr = np.asarray(q, dtype=float)
    p_arr = p_arr / p_arr.sum()
    q_arr = q_arr / q_arr.sum()
    return float(np.minimum(p_arr, q_arr).sum())


def bh_adjust(p_values: Sequence[float]) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    output = np.empty_like(adjusted)
    output[order] = np.clip(adjusted, 0.0, 1.0)
    return output


def gini(values: Sequence[float]) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0 or np.isclose(x.sum(), 0.0):
        return 0.0
    x = np.sort(np.maximum(x, 0.0))
    n = len(x)
    return float((2.0 * np.dot(np.arange(1, n + 1), x) / (n * x.sum())) - (n + 1) / n)


def apply_publication_theme(base_font_size: float = 7.0) -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": base_font_size,
            "axes.titlesize": base_font_size + 0.5,
            "axes.labelsize": base_font_size,
            "xtick.labelsize": base_font_size - 0.5,
            "ytick.labelsize": base_font_size - 0.5,
            "legend.fontsize": base_font_size - 0.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.75,
            "xtick.major.width": 0.65,
            "ytick.major.width": 0.65,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "legend.frameon": False,
        }
    )


def save_publication_figure(
    fig: plt.Figure,
    stem: Path,
    preview_dpi: int = 300,
    tiff_dpi: int = 600,
) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = [stem.with_suffix(ext) for ext in (".png", ".svg", ".pdf", ".tiff")]
    fig.savefig(paths[0], dpi=preview_dpi, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(paths[1], bbox_inches="tight", pad_inches=0.03)
    fig.savefig(paths[2], bbox_inches="tight", pad_inches=0.03)
    fig.savefig(paths[3], dpi=tiff_dpi, bbox_inches="tight", pad_inches=0.03, pil_kwargs={"compression": "tiff_lzw"})
    return paths


def write_csv(data: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, encoding="utf-8-sig")
