from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Iterable

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Circle, Patch
import numpy as np
import pandas as pd


NSF_DEFAULT = Path(
    'E:\\可持续发展目标基金\\框架内容初稿\\data\\llm编码完数据'
    '\\full_v3_5_2_combined_deepseek\\NSF_coding_results.csv'
)
NSFC_DEFAULT = Path(
    'E:\\可持续发展目标基金\\框架内容初稿\\data\\llm编码完数据'
    '\\full_v3_5_2_combined_deepseek\\NSFC_coding_results.csv'
)

EXPECTED_ROWS = {"NSF": 6207, "NSFC": 5546}
SDG_ORDER = ["S02", "S03", "S06", "S07", "S09", "S10", "S11", "S12", "S13", "S15", "S16", "S17"]
SDG_LABELS = {
    "S02": "Zero hunger",
    "S03": "Good health and well-being",
    "S06": "Clean water and sanitation",
    "S07": "Affordable and clean energy",
    "S09": "Industry, innovation and infrastructure",
    "S10": "Reduced inequalities",
    "S11": "Sustainable cities and communities",
    "S12": "Responsible consumption and production",
    "S13": "Climate action",
    "S15": "Life on land",
    "S16": "Peace, justice and strong institutions",
    "S17": "Partnerships for the goals",
}

TARGET_ROWS = """
2.1|消除饥饿并保障全年获得安全、营养和充足食物|S02
2.2|消除一切形式的营养不良|S02
2.3|提高小规模粮食生产者的生产率和收入|S02
2.4|建立可持续且具韧性的粮食生产系统|S02
2.5|保护种子、作物及养殖动物的遗传多样性|S02
2.a|增加农业基础设施、研究、推广和技术投资|S02
2.b|纠正和防止世界农产品市场贸易限制与扭曲|S02
2.c|改善粮食市场信息并限制价格剧烈波动|S02
3.1|降低孕产妇死亡率|S03
3.2|终止新生儿和五岁以下儿童可预防死亡|S03
3.3|遏制艾滋病、结核病、疟疾等传染病|S03
3.4|降低非传染性疾病过早死亡并促进心理健康|S03
3.5|预防和治疗药物滥用及有害饮酒|S03
3.6|减少道路交通事故伤亡|S03
3.7|普及性与生殖健康服务|S03
3.8|实现全民健康覆盖和基本医疗保障|S03
3.9|减少危险化学品及空气、水和土壤污染所致疾病与死亡|S03
3.a|加强《烟草控制框架公约》实施|S03
3.b|促进疫苗和药品研发、可负担获得与基本药物供应|S03
3.c|增加卫生筹资并加强卫生人力队伍|S03
3.d|加强健康风险预警、降低风险和管理能力|S03
6.1|普及安全且可负担的饮用水|S06
6.2|普及适当卫生设施与个人卫生服务|S06
6.3|改善水质、污水处理、回用和安全再利用|S06
6.4|提高用水效率并应对缺水|S06
6.5|实施综合水资源管理|S06
6.6|保护和恢复涉水生态系统|S06
6.a|扩大水与卫生领域国际合作和能力建设|S06
6.b|加强地方社区参与水与卫生管理|S06
7.1|普及可负担、可靠和现代能源服务|S07
7.2|提高可再生能源占比|S07
7.3|提高能源效率|S07
7.a|加强清洁能源研究、技术与投资合作|S07
7.b|扩展发展中国家的可持续能源基础设施和技术|S07
9.1|建设优质、可靠、可持续和有韧性的基础设施|S09
9.2|促进包容和可持续工业化|S09
9.3|提升小型企业获得金融服务并融入价值链的机会|S09
9.4|升级基础设施和产业以提高资源效率并减少环境影响|S09
9.5|加强科研能力与技术创新|S09
9.a|支持发展中国家建设可持续且有韧性的基础设施|S09
9.b|支持发展中国家的国内技术、研发与产业多样化|S09
9.c|扩大信息通信技术和互联网普及|S09
10.1|提高收入最低40%人口的收入增长|S10
10.2|促进所有人的社会、经济和政治包容|S10
10.3|确保机会平等并减少歧视性结果|S10
10.4|通过财政、工资和社会保障政策促进平等|S10
10.5|加强全球金融市场和金融机构监管|S10
10.6|提升发展中国家在全球经济金融治理中的代表性|S10
10.7|促进安全、有序、正常和负责任的人口迁移流动|S10
10.a|落实对发展中国家的特殊与差别待遇|S10
10.b|促进官方发展援助和资金流向最需要的国家|S10
10.c|降低移民汇款交易成本|S10
11.1|保障适足、安全和可负担住房及基本服务并改造贫民区|S11
11.2|提供安全、可负担、可达和可持续交通系统|S11
11.3|推进包容、可持续城市化和参与式规划管理|S11
11.4|保护世界文化和自然遗产|S11
11.5|减少灾害死亡、受影响人口和直接经济损失|S11
11.6|降低城市人均环境影响，重点关注空气质量和废弃物|S11
11.7|普及安全、包容、可达的绿色和公共空间|S11
11.a|加强城市、城郊和农村地区的积极联系|S11
11.b|实施资源效率、气候适应和灾害韧性综合政策与规划|S11
11.c|支持最不发达国家建设可持续且有韧性的建筑|S11
12.1|实施可持续消费和生产模式十年方案框架|S12
12.2|实现自然资源可持续管理和高效利用|S12
12.3|减少零售和消费端食物浪费及供应链粮食损失|S12
12.4|实现化学品和废弃物全生命周期环境无害化管理|S12
12.5|通过预防、减量、回收和再利用减少废弃物|S12
12.6|推动企业采用可持续实践并纳入报告|S12
12.7|推行可持续公共采购|S12
12.8|普及可持续发展和自然和谐生活方式的信息与意识|S12
12.a|支持发展中国家提升可持续消费生产科技能力|S12
12.b|开发监测可持续旅游影响的工具|S12
12.c|改革低效化石燃料补贴|S12
13.1|增强应对气候灾害和自然灾害的韧性与适应能力|S13
13.2|将气候变化措施纳入政策、战略和规划|S13
13.3|加强气候减缓、适应、影响降低和预警教育与能力|S13
13.a|落实发达国家气候融资承诺并运行绿色气候基金|S13
13.b|加强最不发达国家和小岛屿国家的气候规划管理能力|S13
15.1|保护、恢复和可持续利用陆地及内陆淡水生态系统|S15
15.2|可持续管理森林并制止毁林和恢复退化森林|S15
15.3|防治荒漠化、恢复退化土地并实现土地退化零增长|S15
15.4|保护山地生态系统及其生物多样性|S15
15.5|遏制栖息地退化和生物多样性丧失|S15
15.6|公平分享遗传资源利用产生的惠益|S15
15.7|制止偷猎和贩运受保护物种|S15
15.8|防止外来入侵物种并降低其影响|S15
15.9|将生态系统和生物多样性价值纳入规划与核算|S15
15.a|筹集并增加生物多样性和生态系统保护资金|S15
15.b|筹集森林可持续管理资金并提供激励|S15
15.c|通过提升社区可持续生计遏制偷猎和物种贩运|S15
16.1|减少一切形式暴力及相关死亡|S16
16.2|终止对儿童的虐待、剥削、贩运和暴力|S16
16.3|促进法治并确保平等诉诸司法|S16
16.4|减少非法资金和武器流动并打击有组织犯罪|S16
16.5|减少腐败和贿赂|S16
16.6|建立有效、负责和透明的机构|S16
16.7|确保响应性、包容性、参与性和代表性决策|S16
16.8|扩大并加强发展中国家参与全球治理|S16
16.9|为所有人提供出生登记等法律身份|S16
16.10|保障公众获取信息并保护基本自由|S16
16.a|加强预防暴力、恐怖主义和犯罪的机构能力|S16
16.b|促进和实施非歧视性法律与政策|S16
17.1|加强国内资源动员和税收征管能力|S17
17.2|履行官方发展援助承诺|S17
17.3|为发展中国家动员额外财政资源|S17
17.4|通过融资、减债和重组促进长期债务可持续|S17
17.5|为最不发达国家制定和实施投资促进制度|S17
17.6|加强科学、技术和创新合作及知识共享|S17
17.7|促进环境友好技术开发、转让、传播和推广|S17
17.8|全面运行技术银行并加强信息通信技术使用|S17
17.9|加强发展中国家实施SDGs的能力建设|S17
17.10|促进普遍、基于规则和公平的多边贸易体系|S17
17.11|增加发展中国家出口|S17
17.12|落实最不发达国家免关税免配额市场准入|S17
17.13|加强全球宏观经济稳定|S17
17.14|加强可持续发展政策一致性|S17
17.15|尊重各国制定和实施政策的空间与领导作用|S17
17.16|加强全球可持续发展伙伴关系|S17
17.17|促进公共、政企和民间社会伙伴关系|S17
17.18|提升高质量、及时、可靠和分类数据的可获得性|S17
17.19|发展超越GDP的可持续发展衡量并加强统计能力|S17
""".strip()

NSF_DARK = "#003366"
NSF_MID = "#7F99B2"
NSFC_DARK = "#8B0000"
NSFC_MID = "#C57F7F"
ZERO_COLOR = "#ECEFF1"
GRID_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2933"


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.unicode_minus": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def parse_target_codebook() -> pd.DataFrame:
    rows = []
    for order, line in enumerate(TARGET_ROWS.splitlines(), start=1):
        target_code, label_zh, sdg_code = [part.strip() for part in line.split("|", maxsplit=2)]
        rows.append(
            {
                "target_order": order,
                "target_code": target_code,
                "target_label_zh": label_zh,
                "sdg_code": sdg_code,
                "sdg_number": int(sdg_code[1:]),
                "sdg_label_en": SDG_LABELS[sdg_code],
            }
        )
    codebook = pd.DataFrame(rows)
    if len(codebook) != 121:
        raise ValueError(f"Target codebook must contain 121 rows, found {len(codebook)}")
    if codebook["target_code"].duplicated().any():
        duplicates = codebook.loc[codebook["target_code"].duplicated(), "target_code"].tolist()
        raise ValueError(f"Duplicated Target codes: {duplicates}")
    if codebook["sdg_code"].drop_duplicates().tolist() != SDG_ORDER:
        raise ValueError("Target codebook SDG order does not match the frozen 12-SDG order")
    return codebook


def split_codes(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return list(dict.fromkeys(part.strip() for part in str(value).split("|") if part.strip()))


def target_parent(target_code: str) -> str:
    return f"S{int(target_code.split('.')[0]):02d}"


def load_and_validate_projects(path: Path, agency: str, valid_targets: set[str]) -> pd.DataFrame:
    required = ["record_id", "award_year", "sdg_goal_multi", "sdg_target_multi"]
    data = pd.read_csv(path, usecols=required, low_memory=False)
    expected = EXPECTED_ROWS[agency]
    if len(data) != expected:
        raise ValueError(f"{agency}: expected {expected:,} records, found {len(data):,}")
    if data[["sdg_goal_multi", "sdg_target_multi"]].isna().any().any():
        missing = data[["sdg_goal_multi", "sdg_target_multi"]].isna().sum().to_dict()
        raise ValueError(f"{agency}: missing core coding values: {missing}")

    invalid_targets: set[str] = set()
    parent_mismatches: list[str] = []
    for row in data.itertuples(index=False):
        goals = set(split_codes(row.sdg_goal_multi))
        targets = set(split_codes(row.sdg_target_multi))
        invalid_targets.update(targets - valid_targets)
        parents = {target_parent(code) for code in targets}
        if goals != parents:
            parent_mismatches.append(str(row.record_id))
    if invalid_targets:
        raise ValueError(f"{agency}: Target codes outside frozen codebook: {sorted(invalid_targets)}")
    if parent_mismatches:
        raise ValueError(f"{agency}: Target-to-SDG parent mismatches in {len(parent_mismatches)} projects")
    return data


def fractional_counts(series: Iterable[object], universe: list[str]) -> pd.Series:
    counts = pd.Series(0.0, index=universe, dtype=float)
    for value in series:
        labels = split_codes(value)
        if not labels:
            raise ValueError("Encountered a project without a valid label")
        contribution = 1.0 / len(labels)
        counts.loc[labels] += contribution
    return counts


def build_source_tables(
    nsf: pd.DataFrame,
    nsfc: pd.DataFrame,
    codebook: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    target_universe = codebook["target_code"].tolist()
    nsf_target_count = fractional_counts(nsf["sdg_target_multi"], target_universe)
    nsfc_target_count = fractional_counts(nsfc["sdg_target_multi"], target_universe)
    nsf_goal_count = fractional_counts(nsf["sdg_goal_multi"], SDG_ORDER)
    nsfc_goal_count = fractional_counts(nsfc["sdg_goal_multi"], SDG_ORDER)

    if not np.isclose(nsf_goal_count.sum(), len(nsf), atol=1e-7):
        raise AssertionError("NSF SDG fractional weights do not sum to the project count")
    if not np.isclose(nsfc_goal_count.sum(), len(nsfc), atol=1e-7):
        raise AssertionError("NSFC SDG fractional weights do not sum to the project count")
    if not np.isclose(nsf_target_count.sum(), len(nsf), atol=1e-7):
        raise AssertionError("NSF Target fractional weights do not sum to the project count")
    if not np.isclose(nsfc_target_count.sum(), len(nsfc), atol=1e-7):
        raise AssertionError("NSFC Target fractional weights do not sum to the project count")

    source = codebook.copy()
    source["nsf_target_fractional_count"] = source["target_code"].map(nsf_target_count)
    source["nsfc_target_fractional_count"] = source["target_code"].map(nsfc_target_count)
    source["nsf_target_country_share_pct"] = source["nsf_target_fractional_count"] / len(nsf) * 100.0
    source["nsfc_target_country_share_pct"] = source["nsfc_target_fractional_count"] / len(nsfc) * 100.0
    source["nsf_target_within_sdg_pct"] = 0.0
    source["nsfc_target_within_sdg_pct"] = 0.0

    for sdg_code in SDG_ORDER:
        mask = source["sdg_code"].eq(sdg_code)
        for agency in ("nsf", "nsfc"):
            count_col = f"{agency}_target_fractional_count"
            pct_col = f"{agency}_target_within_sdg_pct"
            denominator = float(source.loc[mask, count_col].sum())
            if denominator > 0:
                source.loc[mask, pct_col] = source.loc[mask, count_col] / denominator * 100.0
                if not np.isclose(source.loc[mask, pct_col].sum(), 100.0, atol=1e-7):
                    raise AssertionError(f"{agency.upper()} {sdg_code} Target profile is not conserved")

    source["nsf_observed"] = source["nsf_target_fractional_count"].gt(0)
    source["nsfc_observed"] = source["nsfc_target_fractional_count"].gt(0)

    summary_rows = []
    for sdg_code in SDG_ORDER:
        mask = source["sdg_code"].eq(sdg_code)
        summary_rows.append(
            {
                "sdg_code": sdg_code,
                "sdg_number": int(sdg_code[1:]),
                "sdg_label_en": SDG_LABELS[sdg_code],
                "target_codebook_count": int(mask.sum()),
                "nsf_sdg_fractional_count": float(nsf_goal_count[sdg_code]),
                "nsf_sdg_share_pct": float(nsf_goal_count[sdg_code] / len(nsf) * 100.0),
                "nsf_observed_target_count": int(source.loc[mask, "nsf_observed"].sum()),
                "nsfc_sdg_fractional_count": float(nsfc_goal_count[sdg_code]),
                "nsfc_sdg_share_pct": float(nsfc_goal_count[sdg_code] / len(nsfc) * 100.0),
                "nsfc_observed_target_count": int(source.loc[mask, "nsfc_observed"].sum()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    if not np.isclose(summary["nsf_sdg_share_pct"].sum(), 100.0, atol=1e-7):
        raise AssertionError("NSF SDG shares do not sum to 100%")
    if not np.isclose(summary["nsfc_sdg_share_pct"].sum(), 100.0, atol=1e-7):
        raise AssertionError("NSFC SDG shares do not sum to 100%")

    nsf_set = set(source.loc[source["nsf_observed"], "target_code"])
    nsfc_set = set(source.loc[source["nsfc_observed"], "target_code"])
    coverage = {
        "nsf_only": len(nsf_set - nsfc_set),
        "shared": len(nsf_set & nsfc_set),
        "nsfc_only": len(nsfc_set - nsf_set),
        "nsf_total": len(nsf_set),
        "nsfc_total": len(nsfc_set),
    }
    return source, summary, coverage


def angular_layout(source: pd.DataFrame, gap: float = np.deg2rad(1.15)) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    layout = source.copy()
    cell_width = (2 * np.pi - gap * len(SDG_ORDER)) / len(layout)
    theta = np.zeros(len(layout), dtype=float)
    groups: dict[str, dict[str, float]] = {}
    cursor = gap / 2.0
    for sdg_code in SDG_ORDER:
        idx = layout.index[layout["sdg_code"].eq(sdg_code)].tolist()
        start = cursor
        for row_idx in idx:
            theta[row_idx] = cursor + cell_width / 2.0
            cursor += cell_width
        end = cursor
        groups[sdg_code] = {
            "start": start,
            "end": end,
            "mid": (start + end) / 2.0,
            "span": end - start,
        }
        cursor += gap
    layout["theta"] = theta
    layout["cell_width"] = cell_width
    return layout, groups


def readable_radial_rotation(theta: float) -> tuple[float, str]:
    degrees = np.degrees(theta) % 360
    rotation = 90 - degrees
    horizontal_alignment = "left"
    if 90 < degrees < 270:
        rotation += 180
        horizontal_alignment = "right"
    return rotation, horizontal_alignment


def draw_heat_ring(
    ax: plt.Axes,
    layout: pd.DataFrame,
    value_col: str,
    observed_col: str,
    bottom: float,
    height: float,
    cmap: LinearSegmentedColormap,
    norm: Normalize,
) -> None:
    for row in layout.itertuples(index=False):
        observed = bool(getattr(row, observed_col))
        value = float(getattr(row, value_col))
        facecolor = cmap(norm(value)) if observed else ZERO_COLOR
        ax.bar(
            row.theta,
            height,
            width=row.cell_width * 0.985,
            bottom=bottom,
            color=facecolor,
            edgecolor=GRID_COLOR,
            linewidth=0.32,
            align="center",
            zorder=4,
        )


def draw_coverage_venn(fig: plt.Figure, coverage: dict[str, int]) -> None:
    inset = fig.add_axes([0.330, 0.390, 0.340, 0.270])
    inset.set_xlim(0, 1)
    inset.set_ylim(0, 1)
    inset.set_aspect("equal")
    inset.axis("off")
    left = Circle((0.40, 0.56), 0.30, facecolor="#8FAADC", edgecolor=NSF_DARK, linewidth=1.0, alpha=0.62)
    right = Circle((0.60, 0.56), 0.30, facecolor="#D3A4A4", edgecolor=NSFC_DARK, linewidth=1.0, alpha=0.62)
    inset.add_patch(left)
    inset.add_patch(right)
    inset.text(0.27, 0.57, str(coverage["nsf_only"]), ha="center", va="center", fontsize=7.0, fontweight="bold", color=TEXT_COLOR)
    inset.text(0.50, 0.57, str(coverage["shared"]), ha="center", va="center", fontsize=7.0, fontweight="bold", color=TEXT_COLOR)
    inset.text(0.73, 0.57, str(coverage["nsfc_only"]), ha="center", va="center", fontsize=7.0, fontweight="bold", color=TEXT_COLOR)
    inset.text(0.27, 0.39, "only", ha="center", va="center", fontsize=6.5, color=TEXT_COLOR)
    inset.text(0.50, 0.39, "shared", ha="center", va="center", fontsize=6.5, color=TEXT_COLOR)
    inset.text(0.73, 0.39, "only", ha="center", va="center", fontsize=6.5, color=TEXT_COLOR)
    inset.text(0.27, 0.76, "NSF", ha="center", va="center", fontsize=7.0, fontweight="bold", color=NSF_DARK)
    inset.text(0.73, 0.76, "NSFC", ha="center", va="center", fontsize=7.0, fontweight="bold", color=NSFC_DARK)


def nice_scale(values) -> tuple[float, np.ndarray]:
    """
    以实际最大SDG share作为径向上限，并生成5%间隔刻度。
    """
    vmax = float(max(values))

    # 柱图上限直接匹配实际最大值，不再向上取整。
    share_max = vmax

    # 保留5%间隔，并将实际最大值作为最外层刻度。
    ticks = np.arange(5.0, share_max, 5.0)
    ticks = np.append(ticks, share_max)

    return share_max, ticks

def draw_figure(source: pd.DataFrame, summary: pd.DataFrame, coverage: dict[str, int]) -> plt.Figure:
    configure_matplotlib()
    layout, groups = angular_layout(source)
    blue_cmap = LinearSegmentedColormap.from_list("nsf_target", ["#E4EDF5", NSF_MID, NSF_DARK])
    red_cmap = LinearSegmentedColormap.from_list("nsfc_target", ["#F6E4E4", NSFC_MID, NSFC_DARK])
    # A shared linear scale retains direct perceptual comparability; the pooled
    # positive 95th percentile is approximately 70%, so larger values saturate.
    norm = Normalize(vmin=0.0, vmax=70.0, clip=True)

    fig = plt.figure(figsize=(7.0866, 7.0866), facecolor="white")
    ax = fig.add_axes([0.035, 0.140, 0.930, 0.820], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 6.05)
    ax.axis("off")

    # SDG share scale; only radial height carries the quantitative meaning.
    bar_base = 1.75
    bar_max_height = 1.85

    share_values = list(summary["nsf_sdg_share_pct"]) +\
                   list(summary["nsfc_sdg_share_pct"])

    share_max, share_ticks = nice_scale(
        share_values
    )
    theta_grid = np.linspace(0, 2 * np.pi, 720)

    for tick in share_ticks:
        radius = (
                bar_base
                + bar_max_height * tick / share_max
        )
        tick_label = f"{tick:.1f}%" if np.isclose(tick, share_max) else f"{int(tick)}%"

        ax.plot(
            theta_grid,
            np.full_like(theta_grid, radius),
            color="#D9DEE3",
            linewidth=0.45,
            zorder=0
        )

        ax.text(
            np.deg2rad(1.2),
            radius,
            tick_label,
            ha="left",
            va="center",
            fontsize=5,
            color="#6B7580",
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "pad": 0.35,
                "alpha": 0.86
            },
            zorder=6,
        )

    summary_indexed = summary.set_index("sdg_code")
    nsf_top_code = str(summary_indexed["nsf_sdg_share_pct"].idxmax())
    nsfc_top_code = str(summary_indexed["nsfc_sdg_share_pct"].idxmax())
    nsf_top_share = float(summary_indexed.loc[nsf_top_code, "nsf_sdg_share_pct"])
    nsfc_top_share = float(summary_indexed.loc[nsfc_top_code, "nsfc_sdg_share_pct"])
    if (nsf_top_code, nsfc_top_code) != ("S13", "S11"):
        raise AssertionError(
            "Largest observed SDG shares changed: "
            f"NSF={nsf_top_code}, NSFC={nsfc_top_code}"
        )

    # Two arrows identify the largest observed SDG share within each national
    # portfolio. Their central paths sit between the paired country bars.
    for sdg_code, color in ((nsf_top_code, NSF_DARK), (nsfc_top_code, NSFC_DARK)):
        ax.annotate(
            "",
            xy=(groups[sdg_code]["mid"], 3.56),
            xytext=(groups[sdg_code]["mid"], 0.0),
            arrowprops={
                "arrowstyle": "-|>",
                "color": color,
                "linewidth": 1.3,
                "mutation_scale": 9,
                "shrinkA": 0,
                "shrinkB": 0,
            },
            annotation_clip=False,
            zorder=1,
        )

    for group_idx, sdg_code in enumerate(SDG_ORDER):
        group = groups[sdg_code]
        mid = group["mid"]
        band_color = "#F7F8FA" if group_idx % 2 == 0 else "#EEF1F4"
        ax.bar(
            mid,
            0.62,
            width=group["span"],
            bottom=3.64,
            color=band_color,
            edgecolor="#59636E",
            linewidth=0.55,
            zorder=2,
        )
        rotation, _ = readable_radial_rotation(mid)
        ax.text(
            mid,
            4.095,
            f"SDG {int(sdg_code[1:])}",
            ha="center",
            va="center",
            rotation=rotation - 90,
            rotation_mode="anchor",
            fontsize=8.0,
            fontweight="bold",
            color=TEXT_COLOR,
            zorder=5,
        )

        nsf_share = float(summary_indexed.loc[sdg_code, "nsf_sdg_share_pct"])
        nsfc_share = float(summary_indexed.loc[sdg_code, "nsfc_sdg_share_pct"])
        bar_width = np.deg2rad(8.0)
        offset = np.deg2rad(4.25)
        for theta, share, color in (
            (mid - offset, nsf_share, NSF_DARK),
            (mid + offset, nsfc_share, NSFC_DARK),
        ):
            height = bar_max_height * share / share_max
            ax.bar(
                theta,
                height,
                width=bar_width,
                bottom=bar_base,
                color=color,
                edgecolor="white",
                linewidth=0.35,
                zorder=3,
            )
        band_rotation, _ = readable_radial_rotation(mid)
        value_offset = min(np.deg2rad(3.10), group["span"] * 0.22)
        ax.text(
            mid - value_offset,
            3.785,
            f"{nsf_share:.1f}",
            ha="center",
            va="center",
            rotation=band_rotation - 90,
            rotation_mode="anchor",
            fontsize=6.0,
            color=NSF_DARK,
            fontweight="bold",
            zorder=6,
        )
        ax.text(
            mid + value_offset,
            3.785,
            f"{nsfc_share:.1f}",
            ha="center",
            va="center",
            rotation=band_rotation - 90,
            rotation_mode="anchor",
            fontsize=6.0,
            color=NSFC_DARK,
            fontweight="bold",
            zorder=6,
        )

    # Target composition rings; each country–SDG profile sums to 100%.
    draw_heat_ring(
        ax,
        layout,
        "nsfc_target_within_sdg_pct",
        "nsfc_observed",
        bottom=4.34,
        height=0.50,
        cmap=red_cmap,
        norm=norm,
    )
    draw_heat_ring(
        ax,
        layout,
        "nsf_target_within_sdg_pct",
        "nsf_observed",
        bottom=4.88,
        height=0.50,
        cmap=blue_cmap,
        norm=norm,
    )

    for sdg_code in SDG_ORDER:
        group = groups[sdg_code]
        for boundary in (group["start"], group["end"]):
            ax.plot([boundary, boundary], [4.30, 5.42], color="#303840", linewidth=0.80, zorder=7)

    for row in layout.itertuples(index=False):
        rotation, horizontal_alignment = readable_radial_rotation(row.theta)
        label_radius = 5.52 + (0.13 if int(row.target_order) % 2 == 0 else 0.0)
        ax.text(
            row.theta,
            label_radius,
            row.target_code,
            rotation=rotation,
            rotation_mode="anchor",
            ha=horizontal_alignment,
            va="center",
            fontsize=7.0,
            color=TEXT_COLOR,
            zorder=8,
        )

    # The legend separates country identity from the quantitative encodings.
    legend_handles = [
        Patch(facecolor=NSF_DARK, edgecolor="none", label="NSF (n = 6,207 projects)"),
        Patch(facecolor=NSFC_DARK, edgecolor="none", label="NSFC (n = 5,546 projects)"),
        Patch(facecolor=ZERO_COLOR, edgecolor="#A7AFB7", linewidth=0.5, label="Target not observed"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.070),
        ncol=3,
        frameon=False,
        fontsize=7.0,
        title_fontsize=6.6,
        handlelength=1.1,
        handleheight=0.8,
        columnspacing=1.2,
    )

    cax_blue = fig.add_axes([0.100, 0.018, 0.320, 0.012])
    cax_red = fig.add_axes([0.580, 0.018, 0.320, 0.012])
    cb_blue = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=blue_cmap), cax=cax_blue, orientation="horizontal")
    cb_red = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=red_cmap), cax=cax_red, orientation="horizontal")
    for cbar, title in (
        (cb_blue, "Outer ring · NSF"),
        (cb_red, "Inner ring · NSFC"),
    ):
        cbar.set_ticks([0, 10, 30, 50, 70])
        cbar.set_ticklabels(["0", "10", "30", "50", "≥70"])
        cbar.ax.tick_params(length=0, labelsize=6.3, pad=1.0)
        cbar.outline.set_visible(False)
        cbar.ax.set_title(title, fontsize=6.4, pad=2.2, color=TEXT_COLOR)

    fig.text(
        0.5,
        0.049,
        "Target share within SDG (%) · linear scale; values ≥70% shown at maximum intensity",
        ha="center",
        va="center",
        fontsize=6.4,
        color="#5B6570",
    )

    draw_coverage_venn(fig, coverage)
    fig.text(0.018, 0.975, "a", ha="left", va="top", fontsize=8, fontweight="bold", color="black")
    return fig


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_figure(fig: plt.Figure, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / "figure1a_preview1.png",
        output_dir / "figure1a1.svg",
        output_dir / "figure1a1.pdf",
        output_dir / "figure1a1.tiff",
    ]
    fig.savefig(paths[0], dpi=300, facecolor="white")
    fig.savefig(paths[1], facecolor="white")
    fig.savefig(paths[2], facecolor="white")
    fig.savefig(paths[3], dpi=600, facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    return paths


def write_qa_report(
    output_dir: Path,
    nsf: pd.DataFrame,
    nsfc: pd.DataFrame,
    source: pd.DataFrame,
    summary: pd.DataFrame,
    coverage: dict[str, int],
    outputs: list[Path],
) -> Path:
    lines = [
        "Figure 1a QA report",
        "====================",
        f"NSF records: {len(nsf)}",
        f"NSFC records: {len(nsfc)}",
        f"Target codebook rows: {len(source)}",
        f"SDG summary rows: {len(summary)}",
        f"NSF SDG share sum: {summary['nsf_sdg_share_pct'].sum():.12f}%",
        f"NSFC SDG share sum: {summary['nsfc_sdg_share_pct'].sum():.12f}%",
        f"NSF-only observed Targets: {coverage['nsf_only']}",
        f"Shared observed Targets: {coverage['shared']}",
        f"NSFC-only observed Targets: {coverage['nsfc_only']}",
        "Main weighting: project-count fractional counting; funding amounts not used",
        "Target heatmap: within-SDG conditional composition",
        "Target colour scale: shared linear 0-70%; values above 70% clipped to maximum intensity",
        "Final physical size: 180 mm x 180 mm",
        "",
        "Output files:",
    ]
    for path in outputs:
        lines.append(f"- {path.name}: {path.stat().st_size} bytes; sha256={file_sha256(path)}")
    report = output_dir / "figure1a_qa_report.txt"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Figure 1a: NSF/NSFC SDG and Target circular comparison")
    parser.add_argument("--nsf", type=Path, default=NSF_DEFAULT, help="NSF encoded project CSV")
    parser.add_argument("--nsfc", type=Path, default=NSFC_DEFAULT, help="NSFC encoded project CSV")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent, help="Output directory")
    args = parser.parse_args()

    codebook = parse_target_codebook()
    valid_targets = set(codebook["target_code"])
    nsf = load_and_validate_projects(args.nsf, "NSF", valid_targets)
    nsfc = load_and_validate_projects(args.nsfc, "NSFC", valid_targets)
    source, summary, coverage = build_source_tables(nsf, nsfc, codebook)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_path = args.output_dir / "figure1a_source_data.csv"
    summary_path = args.output_dir / "figure1a_sdg_summary.csv"
    source.to_csv(source_path, index=False, encoding="utf-8-sig", float_format="%.10f")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig", float_format="%.10f")

    fig = draw_figure(source, summary, coverage)
    outputs = export_figure(fig, args.output_dir)
    plt.close(fig)
    report = write_qa_report(args.output_dir, nsf, nsfc, source, summary, coverage, outputs)
    print(f"Wrote {source_path}")
    print(f"Wrote {summary_path}")
    for output in outputs:
        print(f"Wrote {output}")
    print(f"Wrote {report}")
    print(f"Coverage: NSF-only={coverage['nsf_only']}, shared={coverage['shared']}, NSFC-only={coverage['nsfc_only']}")


if __name__ == "__main__":
    main()
