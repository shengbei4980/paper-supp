# Figure4a 全量构成与总体对齐

## 当前版本

`outputs/Figure4a_条形对齐_外置指标轴` 为本次最新版本，附 PNG、PDF、SVG、TIFF 和预览。图幅 183 × 133.5 mm，主柱区域原尺寸 162.87 × 68.2 mm。

总体指标采用横向条形，起点与第一根 SDG 柱的左边缘对齐，横向尺度宽度与完整柱阵列对应。取消总体条形的横轴线、刻度及 NSF/NSFC 行标签。两项指标名称放在画框左侧，与主柱纵轴标题同列，按三行换行竖排。蓝色为 NSF，红色为 NSFC；图例和底注保留颜色含义。原估计、黑色 95% 区间及括号上下限保留。

Overlap 按 0–100% 线性尺度，灰色尾部为 1−overlap。Aitchison distance 按 0–7 线性显示尺度，7 只是显示上限。各项从零开始；两种指标的条形长度不可跨指标比较，也不使用主柱百分比纵轴读取。取消横轴后，直接读取条形旁数值。

## 叙事责任与数据

引入各国自身的外部 SDG 挑战作为参照，展示并量化科研供给的总体构成偏离。12 SDG 共同分类轴保留，每个 SDG 内 NSF 左、NSFC 右。上柱为供给份额，下柱为该国挑战份额；向下仅是镜像显示，份额均非负。全部 48 个百分比直接标注。Overlap 越大，共享构成越多；Aitchison distance 越小，对数比结构越接近，两项指标不能合并为简单的国家优劣排序。

源数据及既有 2,000 次项目族 bootstrap 样本未改写、未重新抽样。程序核对原估计与区间、24 条记录、48 柱及数字、标签边界和几何对齐。源 CSV 哈希及 600 dpi PNG/TIFF、PDF/SVG 可读性检查通过，最终 PNG 实际审阅通过。报告见 `workspace/final_quality_report.json`；复现脚本为 `workspace/adapted_plot.py`，现有 py311 环境可直接运行。

NSF #3775BA、NSFC #B64342，沿用已确认 Figure1a 配色。Modelviz 既有候选选择与依赖验证结果复用；未改原模板、未新增依赖。

## Suggested caption

**Figure 4a | National research-supply and SDG-challenge alignment.** Solid upward bars show research-supply shares; hatched downward bars show each country's own national SDG-challenge composition across the 12 study SDGs. Within each SDG, NSF is shown on the left and NSFC on the right. All bar labels are percentages; downward shares are mirrored and non-negative. The horizontal bars above summarize composition overlap and Aitchison distance on separate linear scales; blue denotes NSF and red NSFC. Gray overlap tails indicate unshared composition. Estimates and bracketed 95% percentile intervals are shown directly; black whiskers represent the same intervals from 2,000 project-family bootstrap resamples. Higher overlap indicates more shared composition, whereas lower Aitchison distance indicates closer relative structure. Challenge compositions derive from SDSN Sustainable Development Report 2026 goal-score gaps (100−score), averaged over t−3 to t−1 before each award and closed across the 12 study SDGs. Coding and external challenge scores remain fixed in the bootstrap. NSF comprises 5,000 project families observed in 2015–2025; NSFC comprises 5,546 observed in 2015–2023. Unobserved NSFC award years 2024–2025 are not treated as zero.
