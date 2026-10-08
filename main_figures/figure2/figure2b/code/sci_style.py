"""Reusable Matplotlib defaults for publication-ready scientific figures."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from string import ascii_lowercase
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler


MM_PER_INCH = 25.4
COLUMN_WIDTHS_MM = {
    "single": 89.0,
    "one": 89.0,
    "double": 183.0,
    "two": 183.0,
}

COLORS = {
    "ink": "#202124",
    "muted": "#667085",
    "grid": "#D9DEE7",
    "light": "#EEF1F5",
    "control": "#7A7F87",
    "blue": "#0072B2",
    "sky": "#56B4E9",
    "teal": "#009E73",
    "orange": "#E69F00",
    "vermillion": "#D55E00",
    "purple": "#8E5EA2",
    "magenta": "#CC79A7",
    "yellow": "#F0E442",
}

PALETTES = {
    "categorical": (
        COLORS["blue"],
        COLORS["vermillion"],
        COLORS["teal"],
        COLORS["orange"],
        COLORS["purple"],
        COLORS["sky"],
        COLORS["magenta"],
        COLORS["control"],
    ),
    "pair": (COLORS["blue"], COLORS["vermillion"]),
    "cool_warm": ("#3B6FB6", "#C7DCEF", "#F4C7B7", "#B6423C"),
    "teal_orange": ("#0F6B6D", "#6CB7B2", "#F0C987", "#C75B39"),
    "sequential_blue": ("#F2F7FB", "#C7DBEA", "#78AAC8", "#2A6F9E", "#123B5D"),
    "sequential_green": ("#F1F7F3", "#C9E1D2", "#7FB89B", "#39856B", "#145A4A"),
}

SEMANTIC_COLORS = {
    "observed": COLORS["ink"],
    "estimate": COLORS["blue"],
    "uncertainty": COLORS["sky"],
    "control": COLORS["control"],
    "positive": COLORS["vermillion"],
    "negative": COLORS["blue"],
    "threshold": COLORS["purple"],
    "highlight": COLORS["orange"],
    "missing": "#D0D5DD",
}

SAFE_COLORMAPS = {
    "sequential": ("viridis", "cividis", "magma"),
    "diverging": ("BrBG", "PuOr", "RdBu_r"),
    "cyclic": ("twilight",),
}


def mm_to_inches(value_mm: float) -> float:
    """Convert millimetres to inches."""
    if value_mm <= 0:
        raise ValueError("Dimensions must be positive.")
    return value_mm / MM_PER_INCH


def figure_dimensions(
    width: str | float = "double",
    height_mm: float | None = None,
    aspect: float = 1.55,
) -> tuple[float, float]:
    """Return final figure dimensions in inches.

    ``width`` accepts ``single``/``double`` or a numeric width in millimetres.
    When ``height_mm`` is omitted, ``aspect`` means width divided by height.
    """
    if isinstance(width, str):
        key = width.casefold()
        if key not in COLUMN_WIDTHS_MM:
            choices = ", ".join(sorted(COLUMN_WIDTHS_MM))
            raise ValueError(f"Unknown width preset {width!r}; choose {choices}.")
        width_mm = COLUMN_WIDTHS_MM[key]
    else:
        width_mm = float(width)
    if width_mm <= 0:
        raise ValueError("Width must be positive.")
    if height_mm is None:
        if aspect <= 0:
            raise ValueError("Aspect must be positive.")
        height_mm = width_mm / aspect
    if height_mm <= 0:
        raise ValueError("Height must be positive.")
    return mm_to_inches(width_mm), mm_to_inches(float(height_mm))


def apply_journal_style(
    *,
    font_family: str = "Arial",
    base_font_size: float = 7.0,
    axes_line_width: float = 0.7,
    line_width: float = 1.1,
) -> None:
    """Apply restrained, editable journal defaults to Matplotlib."""
    sans_fonts = [font_family, "Helvetica", "DejaVu Sans"]
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": sans_fonts,
            "font.size": base_font_size,
            "axes.labelsize": base_font_size,
            "axes.titlesize": base_font_size,
            "axes.titleweight": "normal",
            "axes.linewidth": axes_line_width,
            "axes.edgecolor": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "axes.facecolor": "white",
            "axes.prop_cycle": cycler(color=PALETTES["categorical"]),
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": 600,
            "lines.linewidth": line_width,
            "lines.markersize": 4.0,
            "xtick.labelsize": base_font_size - 0.5,
            "ytick.labelsize": base_font_size - 0.5,
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "xtick.major.width": axes_line_width,
            "ytick.major.width": axes_line_width,
            "legend.fontsize": base_font_size - 0.5,
            "legend.frameon": False,
            "legend.handlelength": 1.5,
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.5,
            "grid.alpha": 0.7,
            "mathtext.fontset": "dejavusans",
            "axes.unicode_minus": True,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def journal_subplots(
    *,
    width: str | float = "double",
    height_mm: float | None = None,
    aspect: float = 1.55,
    nrows: int = 1,
    ncols: int = 1,
    constrained_layout: bool = True,
    **kwargs: Any,
):
    """Create subplots at final journal dimensions."""
    figsize = figure_dimensions(width=width, height_mm=height_mm, aspect=aspect)
    return plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=figsize,
        constrained_layout=constrained_layout,
        **kwargs,
    )


def palette(name: str = "categorical", n: int | None = None) -> tuple[str, ...]:
    """Return a named palette without silently repeating colors."""
    if name not in PALETTES:
        raise ValueError(f"Unknown palette {name!r}. Available: {', '.join(PALETTES)}")
    values = PALETTES[name]
    if n is None:
        return values
    if n < 1:
        raise ValueError("n must be at least 1.")
    if n > len(values):
        raise ValueError(
            f"Palette {name!r} has {len(values)} distinct colors; requested {n}. "
            "Use grouping or redundant encodings instead of repeating colors."
        )
    return values[:n]


def style_axes(
    ax,
    *,
    grid: str | None = None,
    hide_spines: Sequence[str] = ("top", "right"),
    tick_direction: str = "out",
) -> None:
    """Apply a quiet axis treatment without changing data limits."""
    for name in hide_spines:
        if name in ax.spines:
            ax.spines[name].set_visible(False)
    ax.tick_params(direction=tick_direction)
    if grid is None or grid == "none":
        ax.grid(False)
    elif grid in {"x", "y", "both"}:
        ax.grid(True, axis=grid)
        ax.set_axisbelow(True)
    else:
        raise ValueError("grid must be one of None, 'none', 'x', 'y', or 'both'.")


def _flatten_axes(axes: Any) -> list[Any]:
    if isinstance(axes, Mapping):
        return list(axes.values())
    if hasattr(axes, "flat"):
        return list(axes.flat)
    if isinstance(axes, Iterable) and not hasattr(axes, "text"):
        flattened: list[Any] = []
        for item in axes:
            flattened.extend(_flatten_axes(item))
        return flattened
    return [axes]


def _panel_names(count: int) -> list[str]:
    names: list[str] = []
    for index in range(count):
        quotient, remainder = divmod(index, len(ascii_lowercase))
        names.append(ascii_lowercase[remainder] if quotient == 0 else ascii_lowercase[quotient - 1] + ascii_lowercase[remainder])
    return names


def label_panels(
    axes: Any,
    labels: Sequence[str] | None = None,
    *,
    x: float = -0.11,
    y: float = 1.04,
    fontsize: float = 8.0,
    weight: str = "bold",
) -> None:
    """Add consistent lowercase panel labels in axes coordinates."""
    axes_list = _flatten_axes(axes)
    panel_labels = list(labels) if labels is not None else _panel_names(len(axes_list))
    if len(panel_labels) != len(axes_list):
        raise ValueError("The number of labels must match the number of axes.")
    for ax, label in zip(axes_list, panel_labels, strict=True):
        ax.text(
            x,
            y,
            str(label),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=fontsize,
            fontweight=weight,
            color=COLORS["ink"],
            clip_on=False,
        )


def add_zero_line(ax, *, axis: str = "y", color: str = COLORS["muted"], **kwargs: Any):
    """Add a restrained zero reference line."""
    style = {"linewidth": 0.7, "linestyle": "--", "zorder": 0}
    style.update(kwargs)
    if axis == "y":
        return ax.axhline(0, color=color, **style)
    if axis == "x":
        return ax.axvline(0, color=color, **style)
    raise ValueError("axis must be 'x' or 'y'.")


def equal_comparison_limits(ax, x: Sequence[float], y: Sequence[float], pad: float = 0.04) -> tuple[float, float]:
    """Set equal x/y limits for observed-versus-predicted comparisons."""
    if not math.isfinite(pad) or pad < 0:
        raise ValueError("pad must be a finite non-negative value.")
    values = [float(value) for series in (x, y) for value in series if math.isfinite(float(value))]
    if not values:
        raise ValueError("x and y contain no finite values.")
    low = min(values)
    high = max(values)
    span = high - low
    margin = span * pad if span else max(abs(low), 1.0) * pad
    limits = (low - margin, high + margin)
    ax.set_xlim(limits)
    ax.set_ylim(limits)
    ax.set_aspect("equal", adjustable="box")
    return limits


def save_figure(
    fig,
    output_stem: str | Path,
    *,
    formats: Sequence[str] = ("svg", "pdf", "png"),
    dpi: int = 600,
    transparent: bool = False,
    bbox_inches: str | None = None,
    close: bool = False,
    metadata: Mapping[str, str] | None = None,
    metadata_by_format: Mapping[str, Mapping[str, str]] | None = None,
    require_delivery_set: bool = True,
) -> list[Path]:
    """Export a vector master and raster derivatives from one figure.

    Leave ``bbox_inches`` as ``None`` to preserve exact journal dimensions.
    Use ``bbox_inches='tight'`` only when exact dimensions are not required.
    """
    allowed = {"svg", "pdf", "png", "tif", "tiff"}
    normalized = tuple(str(fmt).lower().lstrip(".") for fmt in formats)
    if not normalized:
        raise ValueError("At least one export format is required.")
    unknown = set(normalized) - allowed
    if unknown:
        raise ValueError(f"Unsupported format(s): {', '.join(sorted(unknown))}")
    if require_delivery_set:
        has_vector = any(fmt in {"svg", "pdf"} for fmt in normalized)
        has_raster = any(fmt in {"png", "tif", "tiff"} for fmt in normalized)
        if not (has_vector and has_raster):
            raise ValueError(
                "Final delivery requires at least one vector and one raster format. "
                "Set require_delivery_set=False only for an intentional intermediate export."
            )

    metadata_keys = {
        "pdf": {
            "Title",
            "Author",
            "Subject",
            "Keywords",
            "Creator",
            "Producer",
            "CreationDate",
            "ModDate",
            "Trapped",
        },
        "svg": {
            "Title",
            "Date",
            "Creator",
            "Description",
            "Format",
            "Type",
            "Coverage",
            "Identifier",
            "Language",
            "Relation",
            "Source",
            "Contributor",
            "Publisher",
            "Rights",
        },
        "png": None,
        "tif": set(),
        "tiff": set(),
    }
    if metadata_by_format:
        unknown_metadata_formats = set(metadata_by_format) - allowed
        if unknown_metadata_formats:
            raise ValueError(
                f"Unsupported metadata format(s): {', '.join(sorted(unknown_metadata_formats))}"
            )
    metadata_payloads: dict[str, dict[str, str]] = {}
    for fmt in normalized:
        payload = dict(metadata or {})
        if metadata_by_format and fmt in metadata_by_format:
            payload.update(metadata_by_format[fmt])
        accepted = metadata_keys[fmt]
        unsupported_keys = set(payload) - accepted if accepted is not None else set()
        if unsupported_keys:
            raise ValueError(
                f"Metadata key(s) unsupported for {fmt}: {', '.join(sorted(unsupported_keys))}"
            )
        metadata_payloads[fmt] = payload

    stem = Path(output_stem)
    if stem.suffix.lower().lstrip(".") in allowed:
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for fmt in normalized:
        path = stem.with_suffix(f".{fmt}")
        kwargs: dict[str, Any] = {
            "format": fmt,
            "transparent": transparent,
            "bbox_inches": bbox_inches,
        }
        if fmt in {"png", "tif", "tiff"}:
            kwargs["dpi"] = dpi
        if fmt in {"tif", "tiff"}:
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        if metadata_payloads[fmt] and fmt in {"pdf", "svg", "png"}:
            kwargs["metadata"] = metadata_payloads[fmt]
        fig.savefig(path, **kwargs)
        if fmt in {"tif", "tiff"} and not transparent:
            try:
                from PIL import Image
            except ImportError as exc:
                raise RuntimeError("Pillow is required to create an RGB TIFF.") from exc
            with Image.open(path) as image:
                if image.mode != "RGB":
                    rgb = image.convert("RGB")
                    rgb.save(path, compression="tiff_lzw", dpi=(dpi, dpi))
        outputs.append(path)

    if close:
        plt.close(fig)
    return outputs


__all__ = [
    "COLORS",
    "COLUMN_WIDTHS_MM",
    "PALETTES",
    "SAFE_COLORMAPS",
    "SEMANTIC_COLORS",
    "add_zero_line",
    "apply_journal_style",
    "equal_comparison_limits",
    "figure_dimensions",
    "journal_subplots",
    "label_panels",
    "mm_to_inches",
    "palette",
    "save_figure",
    "style_axes",
]
