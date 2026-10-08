from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import sparse

CONTROL_CODE = Path('E:\\可持续发展目标基金\\定稿撰写\\成图\\figure2-figure5制作总控\\code')
sys.path.insert(0, str(CONTROL_CODE))

from figure_common import (  # noqa: E402
    A_ORDER,
    D_ORDER,
    K_ORDER,
    L_ORDER,
    N_ORDER,
    O_ORDER,
    P_ORDER,
    AnalysisSettings,
    bh_adjust,
    build_balance_features,
    derive_need_domains,
    entropy_balance_to_reference,
    jsd_components,
    load_projects,
    overlap_coefficient,
    pattern_bootstrap,
    write_csv,
)


FIGURE_ROOT = Path(r"E:\可持续发展目标基金\定稿撰写\成图\figure2")
PANEL_ROOTS = {panel: FIGURE_ROOT / f"figure2{panel}" for panel in "abcde"}
SETTINGS = AnalysisSettings()

STAGES = (
    ("Need → pressure", "need_codes", N_ORDER, "pressure_codes", P_ORDER),
    ("Pressure → system", "pressure_codes", P_ORDER, "system_codes", O_ORDER),
    ("System → knowledge", "system_codes", O_ORDER, "primary_knowledge_codes", K_ORDER),
)


def build_project_joint_matrix(
    data: pd.DataFrame,
    left_field: str,
    left_order: Sequence[str],
    right_field: str,
    right_order: Sequence[str],
) -> np.ndarray:
    left_index = {code: idx for idx, code in enumerate(left_order)}
    right_index = {code: idx for idx, code in enumerate(right_order)}
    matrix = np.zeros((len(data), len(left_order) * len(right_order)), dtype=float)
    for row_idx, (left_codes, right_codes) in enumerate(
        data[[left_field, right_field]].itertuples(index=False, name=None)
    ):
        left = [x for x in dict.fromkeys(left_codes) if x in left_index]
        right = [x for x in dict.fromkeys(right_codes) if x in right_index]
        if not left or not right:
            continue
        contribution = 1.0 / (len(left) * len(right))
        for left_code in left:
            for right_code in right:
                column = left_index[left_code] * len(right_order) + right_index[right_code]
                matrix[row_idx, column] += contribution
    return matrix


def _vector_metrics(p: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = p / p.sum(axis=1, keepdims=True)
    q = q / q.sum(axis=1, keepdims=True)
    midpoint = 0.5 * (p + q)
    with np.errstate(divide="ignore", invalid="ignore"):
        left = np.where(p > 0, 0.5 * p * np.log(p / midpoint), 0.0)
        right = np.where(q > 0, 0.5 * q * np.log(q / midpoint), 0.0)
    return np.minimum(p, q).sum(axis=1), (left + right).sum(axis=1)


def _balance_weights(projects: Mapping[str, pd.DataFrame]) -> dict[str, np.ndarray]:
    features, reference = build_balance_features(projects)
    return {
        agency: entropy_balance_to_reference(frame, reference, SETTINGS)[0]
        for agency, frame in features.items()
    }


def compute_stage_metrics(
    projects: Mapping[str, pd.DataFrame],
    n_resamples: int = 2_000,
    balance_weights: Mapping[str, np.ndarray] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    weights = dict(balance_weights or _balance_weights(projects))
    point_rows: list[dict[str, object]] = []
    bootstrap_rows: list[dict[str, object]] = []
    rng = np.random.default_rng(SETTINGS.seed)

    for stage, left_field, left_order, right_field, right_order in STAGES:
        matrices = {
            agency: build_project_joint_matrix(data, left_field, left_order, right_field, right_order)
            for agency, data in projects.items()
        }
        for specification in ("Observed", "Target–year balanced"):
            base = {
                agency: None if specification == "Observed" else weights[agency]
                for agency in projects
            }
            point = {
                agency: np.average(matrices[agency], axis=0, weights=base[agency])
                for agency in projects
            }
            overlap = overlap_coefficient(point["NSF"], point["NSFC"])
            jsd = float(jsd_components(point["NSF"], point["NSFC"]).sum())

            nsf_boot = pattern_bootstrap(matrices["NSF"], n_resamples, rng, base["NSF"])
            nsfc_boot = pattern_bootstrap(matrices["NSFC"], n_resamples, rng, base["NSFC"])
            boot_overlap, boot_jsd = _vector_metrics(nsf_boot, nsfc_boot)
            point_rows.append(
                {
                    "specification": specification,
                    "stage": stage,
                    "overlap": overlap,
                    "overlap_ci_low": float(np.quantile(boot_overlap, 0.025)),
                    "overlap_ci_high": float(np.quantile(boot_overlap, 0.975)),
                    "jsd": jsd,
                    "jsd_ci_low": float(np.quantile(boot_jsd, 0.025)),
                    "jsd_ci_high": float(np.quantile(boot_jsd, 0.975)),
                }
            )
            bootstrap_rows.extend(
                {
                    "specification": specification,
                    "stage": stage,
                    "resample": idx + 1,
                    "overlap": float(boot_overlap[idx]),
                    "jsd": float(boot_jsd[idx]),
                }
                for idx in range(n_resamples)
            )
    return pd.DataFrame(point_rows), pd.DataFrame(bootstrap_rows)


def _normalise_profile(vector: np.ndarray) -> np.ndarray:
    values = np.asarray(vector, dtype=float)
    total = float(values.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("profile must have a positive finite total")
    return values / total


def _normalise_profile_rows(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=float)
    totals = values.sum(axis=1, keepdims=True)
    if not np.isfinite(values).all() or np.any(totals <= 0):
        raise ValueError("bootstrap profiles must have positive finite row totals")
    return values / totals


def _joint_bootstrap_counts(
    n_projects: int,
    n_resamples: int,
    rng: np.random.Generator,
    base_weights: np.ndarray | None,
) -> np.ndarray:
    if n_projects < 1:
        raise ValueError("joint bootstrap requires at least one project")
    if base_weights is None:
        probabilities = np.full(n_projects, 1.0 / n_projects)
    else:
        probabilities = np.asarray(base_weights, dtype=float)
        if probabilities.shape != (n_projects,):
            raise ValueError("balance weights must match the project count")
        if not np.isfinite(probabilities).all() or np.any(probabilities < 0):
            raise ValueError("balance weights must be finite and non-negative")
        total = float(probabilities.sum())
        if total <= 0:
            raise ValueError("balance weights must have a positive total")
        probabilities = probabilities / total
    counts = rng.multinomial(n_projects, probabilities, size=n_resamples)
    # A single cell cannot exceed the number of projects, and the present
    # corpora are well below int16 capacity.  The cast keeps the two joint
    # count matrices compact while preserving their exact integer values.
    if n_projects <= np.iinfo(np.int16).max:
        counts = counts.astype(np.int16, copy=False)
    return counts


def compute_stage_decomposition_metrics(
    projects: Mapping[str, pd.DataFrame],
    n_resamples: int = 2_000,
    balance_weights: Mapping[str, np.ndarray] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute additive stage contributions with a joint project bootstrap.

    Each stage is independently normalised and receives one third of the
    probability mass in the combined translation profile.  Consequently, the
    three stage-specific JSD contributions add exactly to the total-profile
    JSD, while a single project resample is reused across all three stages.
    """
    if n_resamples < 1:
        raise ValueError("n_resamples must be at least 1")
    required_agencies = ("NSF", "NSFC")
    missing = [agency for agency in required_agencies if agency not in projects]
    if missing:
        raise ValueError(f"projects missing required agencies: {missing}")

    weights = dict(balance_weights or _balance_weights(projects))
    matrices: dict[str, dict[str, np.ndarray]] = {}
    for stage, left_field, left_order, right_field, right_order in STAGES:
        matrices[stage] = {}
        for agency in required_agencies:
            matrix = build_project_joint_matrix(
                projects[agency],
                left_field,
                left_order,
                right_field,
                right_order,
            )
            if matrix.shape[0] != len(projects[agency]):
                raise ValueError(f"{agency} {stage} matrix row count does not match projects")
            if not np.isfinite(matrix).all() or np.any(matrix.sum(axis=1) <= 0):
                raise ValueError(f"{agency} {stage} matrix contains invalid project profiles")
            matrices[stage][agency] = matrix

    point_rows: list[dict[str, object]] = []
    bootstrap_rows: list[dict[str, object]] = []
    rng = np.random.default_rng(SETTINGS.seed)
    stage_weight = 1.0 / len(STAGES)

    for specification in ("Observed", "Target–year balanced"):
        base = {
            agency: None if specification == "Observed" else np.asarray(weights[agency], dtype=float)
            for agency in required_agencies
        }
        counts = {
            agency: _joint_bootstrap_counts(
                len(projects[agency]),
                n_resamples,
                rng,
                base[agency],
            )
            for agency in required_agencies
        }

        stage_points: dict[str, dict[str, np.ndarray]] = {}
        stage_bootstraps: dict[str, dict[str, np.ndarray]] = {}
        stage_metrics: dict[str, dict[str, np.ndarray | float]] = {}
        for stage, *_ in STAGES:
            stage_points[stage] = {}
            stage_bootstraps[stage] = {}
            for agency in required_agencies:
                point = np.average(
                    matrices[stage][agency],
                    axis=0,
                    weights=base[agency],
                )
                stage_points[stage][agency] = _normalise_profile(point)
                boot = counts[agency] @ matrices[stage][agency]
                stage_bootstraps[stage][agency] = _normalise_profile_rows(boot)

            overlap = overlap_coefficient(
                stage_points[stage]["NSF"],
                stage_points[stage]["NSFC"],
            )
            jsd = float(
                jsd_components(
                    stage_points[stage]["NSF"],
                    stage_points[stage]["NSFC"],
                ).sum()
            )
            boot_overlap, boot_jsd = _vector_metrics(
                stage_bootstraps[stage]["NSF"],
                stage_bootstraps[stage]["NSFC"],
            )
            stage_metrics[stage] = {
                "overlap": overlap,
                "jsd": jsd,
                "boot_overlap": boot_overlap,
                "boot_jsd": boot_jsd,
            }

        combined_points = {
            agency: np.concatenate(
                [stage_points[stage][agency] * stage_weight for stage, *_ in STAGES]
            )
            for agency in required_agencies
        }
        combined_bootstraps = {
            agency: np.concatenate(
                [stage_bootstraps[stage][agency] * stage_weight for stage, *_ in STAGES],
                axis=1,
            )
            for agency in required_agencies
        }
        total_overlap = overlap_coefficient(combined_points["NSF"], combined_points["NSFC"])
        total_jsd = float(jsd_components(combined_points["NSF"], combined_points["NSFC"]).sum())
        total_boot_overlap, total_boot_jsd = _vector_metrics(
            combined_bootstraps["NSF"],
            combined_bootstraps["NSFC"],
        )

        total_overlap_ci = np.quantile(total_boot_overlap, [0.025, 0.975])
        total_jsd_ci = np.quantile(total_boot_jsd, [0.025, 0.975])
        point_rows.append(
            {
                "specification": specification,
                "scope": "Total",
                "stage": "",
                "overlap": total_overlap,
                "overlap_ci_low": float(total_overlap_ci[0]),
                "overlap_ci_high": float(total_overlap_ci[1]),
                "jsd": total_jsd,
                "jsd_ci_low": float(total_jsd_ci[0]),
                "jsd_ci_high": float(total_jsd_ci[1]),
                "absolute_contribution": total_jsd,
                "contribution_ci_low": float(total_jsd_ci[0]),
                "contribution_ci_high": float(total_jsd_ci[1]),
                "contribution_share": 1.0,
            }
        )
        bootstrap_rows.extend(
            {
                "specification": specification,
                "scope": "Total",
                "stage": "",
                "resample": idx + 1,
                "overlap": float(total_boot_overlap[idx]),
                "jsd": float(total_boot_jsd[idx]),
                "absolute_contribution": float(total_boot_jsd[idx]),
            }
            for idx in range(n_resamples)
        )

        for stage, *_ in STAGES:
            metrics = stage_metrics[stage]
            boot_overlap = np.asarray(metrics["boot_overlap"], dtype=float)
            boot_jsd = np.asarray(metrics["boot_jsd"], dtype=float)
            overlap_ci = np.quantile(boot_overlap, [0.025, 0.975])
            jsd_ci = np.quantile(boot_jsd, [0.025, 0.975])
            contribution = float(metrics["jsd"]) * stage_weight
            boot_contribution = boot_jsd * stage_weight
            contribution_ci = np.quantile(boot_contribution, [0.025, 0.975])
            point_rows.append(
                {
                    "specification": specification,
                    "scope": stage,
                    "stage": stage,
                    "overlap": float(metrics["overlap"]),
                    "overlap_ci_low": float(overlap_ci[0]),
                    "overlap_ci_high": float(overlap_ci[1]),
                    "jsd": float(metrics["jsd"]),
                    "jsd_ci_low": float(jsd_ci[0]),
                    "jsd_ci_high": float(jsd_ci[1]),
                    "absolute_contribution": contribution,
                    "contribution_ci_low": float(contribution_ci[0]),
                    "contribution_ci_high": float(contribution_ci[1]),
                    "contribution_share": contribution / total_jsd,
                }
            )
            bootstrap_rows.extend(
                {
                    "specification": specification,
                    "scope": stage,
                    "stage": stage,
                    "resample": idx + 1,
                    "overlap": float(boot_overlap[idx]),
                    "jsd": float(boot_jsd[idx]),
                    "absolute_contribution": float(boot_contribution[idx]),
                }
                for idx in range(n_resamples)
            )

    summary = pd.DataFrame(point_rows)
    observed = summary[summary["specification"].eq("Observed")].set_index("scope")
    balanced_mask = summary["specification"].eq("Target–year balanced")
    summary["retained_fraction"] = 1.0
    summary.loc[balanced_mask, "retained_fraction"] = [
        value / observed.loc[scope, "absolute_contribution"]
        for scope, value in summary.loc[
            balanced_mask,
            ["scope", "absolute_contribution"],
        ].itertuples(index=False, name=None)
    ]
    return summary, pd.DataFrame(bootstrap_rows)


def build_figure2b_data_only(
    summary_path: Path | str = PANEL_ROOTS["b"] / 'data' / 'Figure2b_stage_commonality_and_divergence.csv',
    bootstrap_path: Path | str = PANEL_ROOTS["b"] / 'data' / 'Figure2b_Bootstrap_full_distribution.csv',
    n_resamples: int = 2_000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build and write only the two Figure 2b data products."""
    summary_target = Path(summary_path)
    bootstrap_target = Path(bootstrap_path)
    if summary_target.resolve() == bootstrap_target.resolve():
        raise ValueError("summary_path and bootstrap_path must be different")
    projects, _ = load_projects()
    balance_weights = _balance_weights(projects)
    summary, bootstrap = compute_stage_decomposition_metrics(
        projects,
        n_resamples=n_resamples,
        balance_weights=balance_weights,
    )
    required_summary = {
        "specification",
        "scope",
        "stage",
        "overlap",
        "overlap_ci_low",
        "overlap_ci_high",
        "jsd",
        "jsd_ci_low",
        "jsd_ci_high",
        "absolute_contribution",
        "contribution_ci_low",
        "contribution_ci_high",
        "contribution_share",
        "retained_fraction",
    }
    required_bootstrap = {
        "specification",
        "scope",
        "stage",
        "resample",
        "overlap",
        "jsd",
        "absolute_contribution",
    }
    if not required_summary.issubset(summary.columns):
        raise ValueError("Figure 2b summary schema is incomplete")
    if not required_bootstrap.issubset(bootstrap.columns):
        raise ValueError("Figure 2b bootstrap schema is incomplete")
    write_csv(summary, summary_target)
    write_csv(bootstrap, bootstrap_target)
    return summary, bootstrap


def build_flow_edges(
    projects: Mapping[str, pd.DataFrame],
    labels: Mapping[str, Mapping[str, str]],
    balance_weights: Mapping[str, np.ndarray] | None = None,
) -> pd.DataFrame:
    label_levels = {
        "Need → pressure": ("Urban-need topic", "Pressure"),
        "Pressure → system": ("Pressure", "Urban system"),
        "System → knowledge": ("Urban system", "Primary knowledge task"),
    }
    rows: list[dict[str, object]] = []
    for agency, data in projects.items():
        row_weights = np.ones(len(data)) if balance_weights is None else balance_weights[agency]
        for stage, left_field, left_order, right_field, right_order in STAGES:
            matrix = build_project_joint_matrix(data, left_field, left_order, right_field, right_order)
            totals = np.sum(matrix * row_weights[:, None], axis=0).reshape(len(left_order), len(right_order))
            left_level, right_level = label_levels[stage]
            for left_idx, left_code in enumerate(left_order):
                for right_idx, right_code in enumerate(right_order):
                    value = float(totals[left_idx, right_idx])
                    if value <= 0:
                        continue
                    rows.append(
                        {
                            "agency": agency,
                            "stage": stage,
                            "source": left_code,
                            "source_label": labels[left_level].get(left_code, left_code),
                            "target": right_code,
                            "target_label": labels[right_level].get(right_code, right_code),
                            "fractional_project_n": value,
                            "stage_share": value / row_weights.sum(),
                        }
                    )
    return pd.DataFrame(rows)


def _path_events(data: pd.DataFrame, balance_weights: np.ndarray, agency: str) -> pd.DataFrame:
    if len(balance_weights) != len(data):
        raise ValueError(
            f"{agency}: balance_weights length {len(balance_weights)} does not match "
            f"project rows {len(data)}"
        )
    rows: list[dict[str, object]] = []
    fields = ["record_id", "need_codes", "pressure_codes", "system_codes", "primary_knowledge_codes"]
    for project_idx, (record_id, needs, pressures, systems, knowledge) in enumerate(
        data[fields].itertuples(index=False, name=None)
    ):
        if not needs:
            raise ValueError(f"{agency} record_id={record_id}: need_codes must contain at least one code")
        for field, codes in (
            ("pressure_codes", pressures),
            ("system_codes", systems),
            ("primary_knowledge_codes", knowledge),
        ):
            if len(codes) != 1:
                raise ValueError(
                    f"{agency} record_id={record_id}: {field} must contain exactly one primary code; "
                    f"found {len(codes)} ({codes})"
                )
        p, o, k = pressures[0], systems[0], knowledge[0]
        for need in needs:
            rows.append(
                {
                    "agency": agency,
                    "project_idx": project_idx,
                    "record_id": record_id,
                    "need": need,
                    "domain": next(iter(derive_need_domains([need]))),
                    "pressure": p,
                    "system": o,
                    "knowledge": k,
                    "path": f"{need}|{p}|{o}",
                    "fraction": 1.0 / len(needs),
                    "balance_weight": float(balance_weights[project_idx]),
                }
            )
    return pd.DataFrame(rows)


def _bootstrap_sparse_columns(
    n_projects: int,
    events: pd.DataFrame,
    paths: Sequence[str],
    balance_weights: np.ndarray,
    n_resamples: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    path_index = {path: idx for idx, path in enumerate(paths)}
    k_index = {code: idx for idx, code in enumerate(K_ORDER)}
    n_paths = len(paths)
    row_ids: list[int] = []
    col_ids: list[int] = []
    values: list[float] = []
    for row in events.itertuples(index=False):
        if row.path not in path_index:
            continue
        p_idx = path_index[row.path]
        row_ids.extend((int(row.project_idx), int(row.project_idx)))
        col_ids.extend((p_idx, n_paths + p_idx * len(K_ORDER) + k_index[row.knowledge]))
        values.extend((float(row.fraction), float(row.fraction)))
    matrix = sparse.coo_matrix(
        (values, (row_ids, col_ids)),
        shape=(n_projects, n_paths + n_paths * len(K_ORDER)),
    ).tocsr()
    point = np.asarray(balance_weights @ matrix).ravel()
    probs = balance_weights / balance_weights.sum()
    bootstrap = np.empty((n_resamples, matrix.shape[1]), dtype=float)
    chunk_size = 100
    for start in range(0, n_resamples, chunk_size):
        stop = min(start + chunk_size, n_resamples)
        counts = rng.multinomial(n_projects, probs, size=stop - start)
        bootstrap[start:stop] = np.asarray(counts @ matrix)
    return point, bootstrap


def build_path_differences(
    projects: Mapping[str, pd.DataFrame],
    labels: Mapping[str, Mapping[str, str]],
    balance_weights: Mapping[str, np.ndarray],
    n_resamples: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = {
        agency: _path_events(data, balance_weights[agency], agency)
        for agency, data in projects.items()
    }
    raw_counts = {
        agency: frame.groupby("path", observed=True)["fraction"].sum()
        for agency, frame in events.items()
    }
    all_paths = sorted(set(raw_counts["NSF"].index) | set(raw_counts["NSFC"].index))
    eligible = [
        path
        for path in all_paths
        if raw_counts["NSF"].get(path, 0.0) >= 10
        and raw_counts["NSFC"].get(path, 0.0) >= 10
        and raw_counts["NSF"].get(path, 0.0) + raw_counts["NSFC"].get(path, 0.0) >= 40
    ]
    rng = np.random.default_rng(SETTINGS.seed + 19)
    point: dict[str, np.ndarray] = {}
    bootstrap: dict[str, np.ndarray] = {}
    for agency in ("NSF", "NSFC"):
        point[agency], bootstrap[agency] = _bootstrap_sparse_columns(
            len(projects[agency]),
            events[agency],
            eligible,
            balance_weights[agency],
            n_resamples,
            rng,
        )

    rows: list[dict[str, object]] = []
    boot_rows: list[dict[str, object]] = []
    n_paths = len(eligible)
    for path_idx, path in enumerate(eligible):
        need, pressure, system = path.split("|")
        domain = next(iter(derive_need_domains([need])))
        for k_idx, knowledge in enumerate(K_ORDER):
            column = n_paths + path_idx * len(K_ORDER) + k_idx
            point_probs = {
                agency: point[agency][column] / point[agency][path_idx]
                for agency in ("NSF", "NSFC")
            }
            boot_probs = {}
            for agency in ("NSF", "NSFC"):
                denom = bootstrap[agency][:, path_idx]
                boot_probs[agency] = np.divide(
                    bootstrap[agency][:, column],
                    denom,
                    out=np.zeros(n_resamples),
                    where=denom > 0,
                )
            difference = boot_probs["NSF"] - boot_probs["NSFC"]
            estimate = point_probs["NSF"] - point_probs["NSFC"]
            p_value = 2.0 * min(
                (np.count_nonzero(difference <= 0) + 1) / (n_resamples + 1),
                (np.count_nonzero(difference >= 0) + 1) / (n_resamples + 1),
            )
            rows.append(
                {
                    "domain": domain,
                    "path": path,
                    "need": need,
                    "need_label": labels["Urban-need topic"].get(need, need),
                    "pressure": pressure,
                    "pressure_label": labels["Pressure"].get(pressure, pressure),
                    "system": system,
                    "system_label": labels["Urban system"].get(system, system),
                    "knowledge": knowledge,
                    "knowledge_label": labels["Primary knowledge task"].get(knowledge, knowledge),
                    "nsf_probability": point_probs["NSF"],
                    "nsfc_probability": point_probs["NSFC"],
                    "difference_nsf_minus_nsfc": estimate,
                    "ci_low": float(np.quantile(difference, 0.025)),
                    "ci_high": float(np.quantile(difference, 0.975)),
                    "p_value": p_value,
                    "nsf_raw_path_n": float(raw_counts["NSF"].get(path, 0.0)),
                    "nsfc_raw_path_n": float(raw_counts["NSFC"].get(path, 0.0)),
                }
            )
            boot_rows.extend(
                {
                    "path": path,
                    "knowledge": knowledge,
                    "resample": idx + 1,
                    "difference_nsf_minus_nsfc": float(difference[idx]),
                }
                for idx in range(n_resamples)
            )
    summary = pd.DataFrame(rows)
    summary["q_value_bh"] = bh_adjust(summary["p_value"])
    summary["quality_gate"] = (
        (summary["q_value_bh"] < SETTINGS.alpha)
        & ((summary["ci_low"] > 0) | (summary["ci_high"] < 0))
    )
    return summary, pd.DataFrame(boot_rows)


def _conditional_joint_summary(
    projects: Mapping[str, pd.DataFrame],
    balance_weights: Mapping[str, np.ndarray],
    left_field: str,
    left_order: Sequence[str],
    right_field: str,
    right_order: Sequence[str],
    n_resamples: int,
    seed_offset: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    matrices = {
        agency: build_project_joint_matrix(data, left_field, left_order, right_field, right_order)
        for agency, data in projects.items()
    }
    point: dict[str, np.ndarray] = {}
    boot: dict[str, np.ndarray] = {}
    rng = np.random.default_rng(SETTINGS.seed + seed_offset)
    for agency in ("NSF", "NSFC"):
        raw_point = np.average(matrices[agency], axis=0, weights=balance_weights[agency]).reshape(
            len(left_order), len(right_order)
        )
        point[agency] = np.divide(
            raw_point,
            raw_point.sum(axis=1, keepdims=True),
            out=np.zeros_like(raw_point),
            where=raw_point.sum(axis=1, keepdims=True) > 0,
        )
        raw_boot = pattern_bootstrap(
            matrices[agency], n_resamples, rng, balance_weights[agency]
        ).reshape(n_resamples, len(left_order), len(right_order))
        boot[agency] = np.divide(
            raw_boot,
            raw_boot.sum(axis=2, keepdims=True),
            out=np.zeros_like(raw_boot),
            where=raw_boot.sum(axis=2, keepdims=True) > 0,
        )
    rows: list[dict[str, object]] = []
    boot_rows: list[dict[str, object]] = []
    for left_idx, left_code in enumerate(left_order):
        for right_idx, right_code in enumerate(right_order):
            difference = boot["NSF"][:, left_idx, right_idx] - boot["NSFC"][:, left_idx, right_idx]
            rows.append(
                {
                    "left_code": left_code,
                    "right_code": right_code,
                    "nsf_probability": point["NSF"][left_idx, right_idx],
                    "nsfc_probability": point["NSFC"][left_idx, right_idx],
                    "difference_nsf_minus_nsfc": point["NSF"][left_idx, right_idx]
                    - point["NSFC"][left_idx, right_idx],
                    "ci_low": float(np.quantile(difference, 0.025)),
                    "ci_high": float(np.quantile(difference, 0.975)),
                }
            )
            boot_rows.extend(
                {
                    "left_code": left_code,
                    "right_code": right_code,
                    "resample": idx + 1,
                    "difference_nsf_minus_nsfc": float(difference[idx]),
                }
                for idx in range(n_resamples)
            )
    return pd.DataFrame(rows), pd.DataFrame(boot_rows)


def build_action_flow(
    projects: Mapping[str, pd.DataFrame],
    balance_weights: Mapping[str, np.ndarray],
    labels: Mapping[str, Mapping[str, str]],
) -> pd.DataFrame:
    stages = (
        ("Knowledge → intervention", "primary_knowledge_codes", K_ORDER, "intervention_codes", L_ORDER,
         "Primary knowledge task", "Intervention"),
        ("Intervention → action stage", "intervention_codes", L_ORDER, "action_codes", A_ORDER,
         "Intervention", "Action stage"),
    )
    rows: list[dict[str, object]] = []
    for agency, data in projects.items():
        for stage, left_field, left_order, right_field, right_order, left_level, right_level in stages:
            matrix = build_project_joint_matrix(data, left_field, left_order, right_field, right_order)
            totals = np.sum(matrix * balance_weights[agency][:, None], axis=0).reshape(
                len(left_order), len(right_order)
            )
            for left_idx, left_code in enumerate(left_order):
                for right_idx, right_code in enumerate(right_order):
                    value = float(totals[left_idx, right_idx])
                    if value <= 0:
                        continue
                    rows.append(
                        {
                            "agency": agency,
                            "stage": stage,
                            "source": left_code,
                            "source_label": labels[left_level].get(left_code, left_code),
                            "target": right_code,
                            "target_label": labels[right_level].get(right_code, right_code),
                            "balanced_fractional_project_n": value,
                            "stage_share": value / balance_weights[agency].sum(),
                        }
                    )
    return pd.DataFrame(rows)


def _write_parameters() -> None:
    rows = pd.DataFrame(
        [
            ("Year range", "2015–2025"),
            ("Project weighting", "Each project sums to 1 within every analyzed layer or adjacent link"),
            ("Standardization", "Maximum-entropy balance to the pooled Target–year reference"),
            ("Bootstrap", f"{SETTINGS.bootstrap_resamples} project-level resamples with replacement"),
            ("Interval", "95% percentile interval"),
            ("Multiple testing", "Benjamini–Hochberg FDR for conditional path contrasts"),
            ("Random seed", str(SETTINGS.seed)),
        ],
        columns=["parameter", "value"],
    )
    write_csv(rows, FIGURE_ROOT / 'data' / "Figure2_分析参数.csv")


def main() -> None:
    projects, labels = load_projects()
    balance_weights = _balance_weights(projects)

    flow_observed = build_flow_edges(projects, labels)
    write_csv(flow_observed, PANEL_ROOTS["a"] / 'data' / 'Figure2a_all_need_translation_flows.csv')

    stage_summary, stage_bootstrap = compute_stage_metrics(
        projects, SETTINGS.bootstrap_resamples, balance_weights
    )
    write_csv(stage_summary, PANEL_ROOTS["b"] / 'data' / 'Figure2b_stage_commonality_and_divergence.csv')
    write_csv(stage_bootstrap, PANEL_ROOTS["b"] / 'data' / 'Figure2b_Bootstrap_full_distribution.csv')

    path_summary, path_bootstrap = build_path_differences(
        projects, labels, balance_weights, SETTINGS.bootstrap_resamples
    )
    write_csv(path_summary, PANEL_ROOTS["c"] / 'data' / "Figure2c_条件路径差异全量.csv")
    write_csv(path_bootstrap, PANEL_ROOTS["c"] / 'data' / "Figure2c_Bootstrap完整分布.csv")

    domain_k, domain_k_boot = _conditional_joint_summary(
        projects,
        balance_weights,
        "domain_codes",
        D_ORDER,
        "primary_knowledge_codes",
        K_ORDER,
        SETTINGS.bootstrap_resamples,
        37,
    )
    domain_k["domain_label"] = domain_k["left_code"].map(labels["Urban-need domain"])
    domain_k["knowledge_label"] = domain_k["right_code"].map(labels["Primary knowledge task"])
    write_csv(domain_k, PANEL_ROOTS["d"] / 'data' / "Figure2d_需求领域知识任务构成.csv")
    write_csv(domain_k_boot, PANEL_ROOTS["d"] / 'data' / "Figure2d_Bootstrap完整分布.csv")

    action_flow = build_action_flow(projects, balance_weights, labels)
    write_csv(action_flow, PANEL_ROOTS["e"] / 'data' / "Figure2e_知识任务至行动出口全量流.csv")
    _write_parameters()

    print(stage_summary.to_string(index=False))
    print(f"Figure2c eligible path–knowledge contrasts: {len(path_summary):,}; quality gate: {int(path_summary['quality_gate'].sum()):,}")


if __name__ == "__main__":
    main()
