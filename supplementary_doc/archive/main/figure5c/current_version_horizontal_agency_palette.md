# 当前版本：Figure5c横排散点与主题词

当前图件：出图/Figure5c_横排散点与主题词_NSF蓝_NSFC红_色带标签。画幅183×85.01 mm，提供PDF、可编辑文字SVG、600 dpi PNG/TIFF和300 dpi预览。复现脚本为代码/figure5c_横排机构配色.py。

每机构采用左侧散点、右侧单个无底框文字区；文字区内按观测份额高于与低于挑战参照分组，两组及两机构对齐。保留原始完整主题名称，只作换行。没有词云散点或延伸线。

NSF全部主题词及对应重点散点使用蓝色，NSFC使用红色。两条色带各自上方标注“Absolute share shift (pp)”，表示挑战标准化份额减观测份额的绝对值，单位为百分点。两条顺序色带均为0—8个百分点的绝对变化幅度，蓝色从#3775BA渐变至#16365B，红色从#B64342渐变至#652325。采用可读主色作为浅端，避免完整长词组在白底上过浅。颜色越深表示绝对偏离越大；色相不再表示偏离方向。方向由“Observed > benchmark”和“Observed < benchmark”两组标题及散点相对等值线的位置表达。

字号采用两机构共同映射6.2 + 2×(|差值|/全体最大|差值|)² pt，本次为6.46—8.20 pt；各方向首位加粗。字号和颜色都对应散点的纵横份额差绝对值，不表示词频或统计显著性。

保留每机构54个主题，共108个点；每机构在正、负变化两个方向各选绝对差值最大的4项，合计16个完整名称，与前版名单相同。其余92点为黑色背景点。浅灰圆覆盖被选点的范围，圈内可能还有未标注的黑点；圆是选中范围的视觉提示，不表示聚类、语义邻域或置信区间。文字排布不保留散点几何坐标，仅用于内容识别。

## 中文图注

c，国家SDG挑战权重下的研究主题结构差异。各机构左侧散点图保留全部54个主题。横轴为观测科研供给份额；纵轴为保持各SDG内部主题构成不变、以各自国家SDG挑战权重替换供给SDG权重后的主题份额；两轴均为百分比，虚线表示相等。各机构在两个偏离方向分别选取绝对变化最大的4项，以机构颜色标出对应点，并在右侧列出完整名称。NSF为蓝色，NSFC为红色；颜色深浅与字号随绝对变化幅度增加，两机构共用幅度尺度。观测份额高于与低于参照的主题分组展示，各组首位加粗。浅灰圆突出选中主题的分布范围，其他主题保留为黑点。筛选只控制文字标注，不改变估计或排除散点，亦不按显著性筛选。文字位置仅用于排版。完整主题估计、项目族Bootstrap逐点95%区间、SDG贡献和逐SDG移除诊断见配套源数据。挑战标准化份额是固定SDG内部主题构成的描述性参照，不直接测量主题层社会需求或需求满足程度。

## English caption

c, Research-theme differences under national SDG challenge weights. Each scatterplot retains all 54 observed themes for its agency. The horizontal axis shows observed research share; the vertical axis shows share after replacing supply-side SDG weights with national challenge weights while holding within-SDG theme profiles fixed. Both axes are in percent; the dashed line denotes equality. Four themes with the largest absolute point-estimate shifts in each direction are selected per agency and named in full to the right. NSF themes and their selected points are blue, and NSFC themes and their selected points are red. Darker shades and larger labels indicate larger absolute shifts under common magnitude mappings. Above-benchmark and below-benchmark themes are grouped separately, with the first-ranked name in each direction in bold. Gray circles highlight the distribution of selected points; they are not confidence regions or semantic neighborhoods. Other themes remain black. Selection affects annotation only, excludes no scatter points and is not based on significance. Label positions are editorial. Complete estimates, pointwise project-family bootstrap intervals, SDG contributions and leave-one-SDG-out diagnostics are provided in the accompanying data. Standardized shares are descriptive fixed-profile benchmarks rather than direct measurements of theme-level societal needs.

## 复核

108个点、16个完整名称及其一一对应关系已核验；点坐标和两份估计源表SHA256保持不变，1296项SDG贡献正确加和至主题差值。SVG逐点核对坐标、逐词核对完整名称及同色对应。数值估计和Bootstrap未重新计算。两机构文字区没有底框或引线，无文字重叠、越界。最小主题文字对比度为6.19。PDF嵌入Arial，SVG保留可编辑文字，PNG/TIFF为600 dpi。静态预检的变量宽度警告由PDF实测183×85.01 mm解决。原Word手稿未修改。
