# Figure4d 单框左右版

画布固定 183 × 110 mm；单一黑色外框，左侧 40 个 Target、右侧 45 个 Target，共 12 个 SDG、85 个 Target。

每个单元上半条为 NSF，下半条为 NSFC；颜色深浅表示实际份额，双国共用线性 0–100% 范围。Share 为该国该 SDG 内的 Target 份额，K01–K06 为该国该 Target 内的条件任务份额。所有色带长度相同，不以长度编码数值。

白色为观测零；灰底短横线为未观测国家–Target；† 为至少一国分数项目支持量不足 10。低支持估计全部保留，不据颜色差异宣称统计显著。

沿用 NSF #3775BA、NSFC #B64342。行高 1.85 mm，Target 编号 5.5 pt。已检查最终预览及全部编号边界，未发现编号重叠。PDF 排版时建议按原定双栏宽度使用，避免再缩小。

文件：同名 PDF/SVG 为矢量，PNG/TIFF 为 600 dpi；preview.png 为便捷预览。绘图代码为上一级 `render_figure4d_single_frame.py`，直接运行即可重绘。数据使用上一级 `数据/paired_target_metrics.csv`，全部完整标签、支持量、区间及 JSD 表也在该目录；配套区间图在上一级 `图/配套_全量Target_份额区间与JSD.pdf`。

本次仅改变版式和单元几何，不重新计算估计。核查覆盖全部 595 个双国单元（1,190 个国家–指标位置），其中 154 个未观测位置单独标记。原三角单元版本保留。

## English caption

**d, Target carriers and knowledge-task profiles.** All 85 observed Targets across the 12 study SDGs are displayed in two column blocks. Each cell contains an upper NSF strip and a lower NSFC strip. Color intensity encodes the share on a common linear 0–100% scale; strip length is constant. Share denotes the Target fraction within its parent SDG and country. K01–K06 denote conditional knowledge-task fractions within that Target and country. White indicates observed zero; gray strips with a dash indicate an unobserved country–Target profile. Daggers indicate fractional Target support below 10 in at least one country. Bootstrap intervals and task-profile JSD are provided in the accompanying data and interval figures; color differences alone are not significance tests.

K01: State measurement and problem diagnosis; K02: Mechanism analysis and causal identification; K03: Scenario simulation and risk prediction; K04: Intervention design and performance optimization; K05: Planning decision support and policy design; K06: Implementation monitoring and impact evaluation.
