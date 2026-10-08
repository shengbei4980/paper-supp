# Figure3d：全量地点的任务贡献偏离谱

## 如何读图

主图为美国 NSF 和中国 NSFC 两个面板。美国保留352个县及等价行政单元，中国保留126个地级行政单元，共478条曲线、2868个地点—任务单元。每条线是一处地点，连接六类离散知识任务，不是时间轨迹、任务之间的转移或因果路径。

纵轴为 **任务贡献份额 T − 整体供给份额 F**，单位为百分点。

- F：地点总分数供给 / 本国总分数供给 ×100。
- T：地点某任务的分数供给 / 本国该任务总分数供给 ×100。
- 高于零：该地点在此任务的全国贡献份额高于其整体供给份额。
- 低于零：该任务贡献份额低于其整体供给份额，不等于没有贡献。
- 每个地点的六个偏离不是任意独立量：按本国任务构成加权后和为零；每项任务在全量地点间的偏离之和也为零。

例如：南京整体份额9.8449%，K05贡献12.0954%，偏离+2.2505个百分点；北京整体份额21.9798%，K05贡献17.7172%，偏离−4.2626个百分点。北京的绝对任务贡献仍较大；南京在这一任务的相对贡献更突出。

## 全量口径与数据来源

沿用 Figure3b 的项目级目标任务分配，冻结原始输入后重新计算，不复用渲染坐标。对跨SDG展开记录累加 `supply=city_weight/sdg_count`，而不是直接累加 `city_weight`。12个SDG汇总后全国分数供给为NSF 5000、NSFC 5546。

全部1425个无分配任务供给的地点—任务单元均保留：T=0时，偏离为−F，不应把偏离错误设为零。这些零值表示研究样本中的未分配供给，不代表现实世界完全不存在该类研究。

NSF观察期2015—2025，NSFC观察期2015—2023，2024—2025对NSFC未观测，不补零。此图沿用原Figure3的样本口径，不估计GDP、资金金额或年度趋势。

## 视觉编码与标注规则

- 两国完全相同的asinh纵轴：显示变换为asinh(偏离/0.5)。所有刻度仍写原始百分点，数据表保留未变换值。该连续、可逆变换容纳正负和零值；无断轴、裁切或抖动。线的斜率仅作视觉连接，不能按几何角度比较效应。
- NSF三节点色带：#E4EDF5 → #7F99B2 → #003366；NSFC：#F6E4E4 → #C57F7F → #8B0000。直接从Figure1a源代码读取。
- 仅重点标注的16处地点保留红蓝色带；其余462处地点的曲线和点统一为浅灰色#CDD1D5。重点地点的色深表示其整体供给份额，使用两国共用LogNorm 0.001%—25%；alpha=1。数字范围适配本图变量，不照搬Figure1a的目标贡献0—70%范围。颜色不表示偏离方向或显著性。
- 美国圆点、中国方点；任务项目族数量<10为空心，≥10为实心。计数是在每个地点—任务内对项目族去重，不能跨地点或任务直接相加得到全国项目族数量。
- 全部曲线均绘制。加粗与文字标注采用“整体供给前5＋每项任务最大正偏离地点”的并集，NSF 9处、NSFC 7处。并列极值按稳定地点顺序选一个作标注，其他曲线照常保留。重点标注不是显著性或质量排名。
- 右侧名字通过引导线连接该地点的K06末端，以便追踪完整曲线；地点名称下显示K编号及带正负号的数值，单位写作pp（百分点）。任务全称按数据标签表保留在下方释义中。这一数值不一定是引导线末端的坐标。优先写该地点K01—K05中最高的偏离；只作为K06领先者入选的地点保留K06标注。具体对应关系保存在标注地点数据表。
- 美国图中简化省略County并保留州缩写；完整地名、行政级别、唯一ID均见数据表。
- 上方Gini与K01—K06逐列对齐；Overall为整体供给集中度。每项任务都用该国固定全量地点集，含任务供给为零的地点。
- 完全重合曲线不人为移位，重合清单随数据输出；绘制全部曲线不保证每条在静态图中都能单独辨认。

## K06及解释边界

K06全国分数计数总量仅NSF 42、NSFC 20。最大正偏离地点为Travis County（4个任务项目族）及北京（8个任务项目族），小支持量会放大任务份额与集中度的不稳定性。图中用灰色任务背景、空心点、星号说明提醒；保留所有K06观测，不将极值解读为稳定优势。

该图是样本描述：未作回归、显著性检验、多重校正或置信区间估计。正偏离不等于统计显著，不代表因果机制。总体任务贡献仍受SDG构成影响，不是控制SDG构成后的专业化指标。

正文北京—南京SDG11/K05、King/Los Angeles/Boulder等特定SDG案例仍引用原SDG内数据。本图回答整体任务贡献方向，不替代那些细分证据。此处未修改正文和补充材料文档。

## 建议英文图注

**d, Geographic departures in knowledge-task contributions.** Each profile represents one research location: 352 US counties and equivalents (NSF) and 126 Chinese prefecture-level units (NSFC). For each task, departure is the location’s share of national task-specific fractional supply minus its share of overall national fractional supply, in percentage points. Supply is pooled across the 12 study SDGs. All 2,868 location–task cells are retained, including 1,425 cells without allocated task supply. Profiles connect categorical tasks, not time points. Both panels use the same asinh scale (width parameter, 0.5 percentage points); tick labels report untransformed values. Highlighted profiles use the Figure1a country palettes, with colour intensity indicating overall national supply share on a shared logarithmic normalization. All other profiles and their markers are light grey (#CDD1D5). Open markers indicate fewer than 10 distinct task project families; filled markers indicate at least 10. Highlighted locations are the union of each country’s five largest overall suppliers and each task’s largest positive-departure location. Endpoint leaders identify profiles; accompanying K codes identify the reported task, with official full names listed in the task key. Label values are signed departures in percentage points (pp). Values above each task mark its largest observed positive departure. Gini coefficients use each country’s full fixed location set, including task zeros. K06 has low national fractional support (NSF, 42; NSFC, 20); extremes should be interpreted with this support in view. Results are descriptive, pool SDG composition and imply neither statistical significance nor causation. Observation windows are 2015–2025 for NSF and 2015–2023 for NSFC.

## 文件与复现

- `图/`：主图及两国单独大图；每种均有600dpi PNG/TIFF、可编辑文字PDF/SVG及300dpi预览。
- `数据/`：全量地点整体供给、全量任务供给/份额/偏离/项目族支持、Gini、标注地点、每项任务领先地点、重合记录、标签与色带参数。
- `数据/输入快照/`：本次使用的原始分配CSV、美国州名映射、Figure1a配色源代码。
- `代码/运行.ps1`：使用已有conda py311环境重绘并进行独立复核；重绘脚本支持`--preview-only`。
- `审查/`：设计约定、快照SHA256、数据与渲染检查、独立数值复算及导出检查、源码预检、视觉复核说明。

主图183×185 mm；单国图160×180 mm。运行需要Python、numpy、pandas、matplotlib和Pillow，无新增依赖。

## 标签最终还原

按用户最新要求还原初始紧凑形式：Boulder, CO / K03 +1.60 pp。原标签位置、行距恢复；灰色背景、红蓝重点曲线和下方正式任务名称释义继续保留。pp表示百分点，数值为任务贡献份额减整体供给份额。
