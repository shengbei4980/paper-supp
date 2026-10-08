# Figure5c完整术语、连续色带与上下对齐修订

本次按用户反馈修改画面，沿用此前核验的项目族分析结果。新增正式文件名为`Figure5c_完整术语_连续色带_对齐修订版`，位于本文件夹的`出图`目录；上一版保留，供比较。

## 问题提炼与落实

| 用户指出的问题 | 原画面的原因 | 本次修订 |
|---|---|---|
| 词语颜色应由数值强度决定 | 上一版颜色区分任务类别，同一种颜色下的数值强弱无法比较 | 词语与SDG圆点共用零中心、−10至+10百分点的红—灰—蓝连续色带。负值为红，正值为蓝，接近零为灰；越接近两端颜色越深。|
| K01–K06散点辨识困难 | 读者需要在六种颜色、六种形状、编码和含义之间来回查找 | 直接用完整任务名称分行；SDG贡献均为圆点，任务净变化为黑色菱形。取消画面中的K编码及六任务符号图例。|
| 词语过少、术语不应简化 | 上一版把完整任务名称压缩为六个短标签 | 每国呈现六类完整任务名称所含的12个原始概念短语，左右配对。下方同时保留六个完整任务名称。没有新增虚构研究类别。|
| 上下布局应对齐 | 椭圆范围和图框结构没有清晰对应 | 改为浅灰矩形词语区，与各自下方图框左右边界严格对齐；两国任务顺序、字号映射和色带一致。|

上方每行的左右短语共同构成一个任务定义，行下数字是该任务的一次净变化，不能把左右短语视为两个独立统计结果。12个短语是原任务名称的完整概念成分，未缩写、截断或改写为口号。词语位置只用于组织阅读，不表示语义距离；这里只按已编码的任务体系呈现术语，没有用额外文本挖掘人为扩充词数。

## 中文图注（本次修订版）

**c，国家SDG挑战权重标准化后的研究任务变化及目标贡献。** 在NSF与NSFC样本内，保持各SDG内部观测到的任务比例不变，以国家挑战份额替换SDG科研供给份额。上方以完整研究术语展示六类任务的份额净变化：每行两个概念短语对应同一个完整任务定义，数字表示一次任务净变化，单位为百分点（pp）。词语位置没有距离含义；字号使用两国共用的变化绝对值映射并设可读下限。下方按完整任务名称分行，圆点显示全部12个SDG对该任务变化的贡献，黑色菱形为12个贡献之和；两机构共144个贡献点及12个净变化点全部保留。各行圆点按SDG顺序固定错位以区分重合点。每行最大正、负贡献中绝对值至少1个百分点者直接标注SDG编号，其余点保留但不加文字。文字与贡献圆点共用以零为中心的连续色带，红色、灰色与蓝色分别对应负值、近零值与正值；黑色菱形不使用色带。细线表示此前项目族层面2,000次非参数重抽样的逐点95%百分位区间，重抽样同时重估科研供给份额与目标内任务比例，国家挑战份额保持固定。NSF含6,207条记录、5,000个项目族；NSFC含5,546条记录、5,546个项目族。

## English caption

**c, Research-task shifts and SDG contributions under national challenge weights.** Within each funding-agency sample, the observed task profile within each SDG was held fixed while its research-supply share was replaced by its national challenge share. The upper displays retain the complete conceptual terms in the six task definitions. Each pair of terms forms one task definition, and its signed value denotes a single net task-share shift in percentage points (pp). Word positions have no distance interpretation, and font sizes emphasize absolute shifts using a common mapping with a readability floor. The lower plots are arranged by complete task names. Circles show the contributions of all 12 SDGs; black diamonds show their sums. All 144 SDG contributions and 12 net shifts are retained across the two samples. Fixed vertical offsets separate SDGs within a task. The largest positive and negative contributions in each row are directly labeled when their absolute magnitude is at least 1 pp. Words and contribution circles share a zero-centered continuous color scale: red denotes negative values, gray near-zero values, and blue positive values. Black diamonds are not encoded by this color scale. Thin lines show pointwise 95% percentile intervals from 2,000 nonparametric project-family bootstrap resamples, jointly re-estimating supply shares and within-SDG task profiles while keeping national challenge shares fixed. The NSF sample comprises 6,207 records in 5,000 project families; the NSFC sample comprises 5,546 records in 5,546 families.

## 科学解释与4.4节的衔接

上方回答“目标结构的权重差异会对应怎样的总体任务组合变化”；下方回答“哪些目标增强或抵消了这些变化”。保持逐任务可加和关系，读者可以直接从全称任务行定位对应的SDG贡献及净值，不需先查K编码。

本次未重新估计任何点值或区间，SDG17影响诊断沿用此前结果。其对规划决策支持任务的影响仍较大，尤其NSFC的SDG17项目支持度有限。任务组合标准化是描述性诊断，不应直接解释为最优经费分配、实际任务需求缺口或政策干预的因果效应。外部挑战指标与编码误差的不确定性未包含在区间中；未执行显著性检验。

## 复现和复核

新版绘图脚本：`代码/figure5c_连续色带版.py`。直接运行即读取已核验结果表并绘制新版，无需重新重抽样。完整术语与颜色映射见`数据/完整术语连续色带_24项.csv`，每国12个短语、合计24行。原估计来源及重算方式见上一版`图注与使用说明.md`。

正式尺寸183 × 190 mm，Arial字体；导出PDF、可编辑SVG及600 dpi PNG/TIFF，另存300 dpi预览。复核按nature-figure的适配与QA规范执行：检查144个圆点、12个净值标记和24个短语全部保留，画面无K编码，矩形与图框对齐，色带同单位同范围，数值加法闭合，文字不重叠、不被裁切。最终PDF渲染和核验文件位于`复核/`。

静态预检13项PASS、0项FAIL、1项WARN。警告是扫描器不能静态求出宽度变量；实际PDF页框已验证为183 × 190 mm。字号最低6 pt（主要SDG直接标注及色带刻度），完整任务标签与净变化值7 pt，概念术语7.4至8.4 pt。两列全量点的表达以实际出版宽度复核；正式排入整张Figure5时需保持这个尺度下的文字可读性。
