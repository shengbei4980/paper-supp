> 已更新为横排机构配色版，当前图件与图注见“当前使用版本_横排机构配色.md”。以下保留为前版说明。

# 当前使用：Figure5c规整紧凑词云版

当前文件：出图/Figure5c_规整紧凑词云_参考式灰圈版。提供PDF、SVG、600 dpi PNG/TIFF和预览。画幅183×154.53 mm。上方按作者最新要求恢复规则长方形排布，白底、无底框；下方保留参考图的浅灰圆、小黑点和红色选中点。以本说明所指文件为当前版本。

## 上方呈现与下方对应

每个机构一个无底框的长方形文字区，左列为观测份额高于挑战参照的4个主题，右列为低于参照的4个主题；各列按差值绝对值从大到小排列。两列统一左对齐，形成四行；同一行的两个名称顶端对齐，完整名称在固定列宽内换行，避免向中央挤靠及高低错落。行间距参数保持0.60 mm，最小列间留白2.28 mm。实际内容高度为NSF 29.02 mm、NSFC 33.75 mm，页面仍按内容高度收紧；下方散点物理尺寸不变。完整英文主题名称保留，只作换行，不省略或另造词汇。重点字号更大，每个方向首位加粗。

下方保留每机构全部54个主题，共108个点。每个机构8个红点与上方8个名称逐项对应，其他46个点用黑色表示。红点只表示选中标注，不表示负差值。两种方向各选择绝对变化最大的4项；筛选只控制标注，不改变科学估计，不按显著性筛选。

横轴为观测科研供给份额，纵轴为保持各SDG内部主题构成不变、替换为各自国家SDG挑战权重后的份额；两轴单位均为百分比，虚线表示相等。上方位置属于文字排版，不再是原始坐标的精确放大；精确份额关系由下方散点和源数据表达。

浅灰圆包围每个机构8个选中点，只服务视觉高亮，不是语义邻域、聚类或置信区间。圈内其他黑点仍保留，不在上方标注。圆心为被选点横、纵坐标极值区间的中点，半径为最大圆心距离加0.20个百分点。NSFC重点点分布更分散，灰圈较大，部分背景被坐标轴边界截去；主题数据未删除。圆形大小不用于比较偏离强弱。

## 红蓝颜色与字号

上方名称使用红—灰—蓝连续色带，编码挑战标准化份额减观测份额，范围−8至+8个百分点。红色名称表示观测份额高于参照，蓝色名称表示低于参照；深浅反映幅度。色带明确标为 Theme-label color，和下方红色选中点的含义区分。

字号采用两机构共同映射：6.3 + 4.2×(|差值|/全体最大|差值|)² pt，本次范围6.85–10.50 pt。该单调映射突出较大变化，字号不是词频，也不直接代表线性比例。

## 4.4节的科研含义

本图将Figure4的国家SDG目标权重差异落实到具体主题组合：下方给出全量主题的定量背景，上方说明重点差异是什么研究内容，补充Figure5a/5b关于知识任务和文本行动阶段的描述。各主题净变化可通过既有12项SDG贡献追溯。

国家挑战数据只到SDG层级，因此纵轴是条件标准化参照，不能解释为直接测得的主题需求、最优资金分配或政策因果效果。既有估计、项目族区间和SDG贡献均沿用，未重跑Bootstrap。原Word本次未修改。

## 中文图注

c，国家SDG挑战权重下的研究主题结构差异。下方分别展示NSF与NSFC全部54个实际研究主题，横轴为观测科研供给份额，纵轴为保持各SDG内部主题构成不变、以各自国家挑战权重替换科研供给SDG权重后的份额；单位均为百分比，虚线表示相等。各机构在观测份额高于和低于参照两个方向分别选取绝对变化最大的4个主题，在下方标红，并在上方单个文字区中按左、右列排列完整名称；其他主题用黑点显示。浅灰圆用于高亮被选主题的分布范围，不表示语义邻域、置信区间或聚类。名称颜色编码挑战标准化减观测份额的差值，单位为百分点，字号随差值绝对值增加，两机构共用映射，每个方向首位名称加粗。红色散点只表示选中，名称的位置只服务排版。选择不改变估计，不排除下方主题，也不按显著性筛选。完整主题估计、项目族Bootstrap逐点95%区间、SDG贡献和逐目标移除诊断见源数据。

## English caption

c, Research-theme differences under national SDG challenge weights. The lower plots retain all 54 observed themes per agency. The horizontal axis shows observed research share, and the vertical axis shows share after replacing research-supply SDG weights with national challenge weights while holding within-SDG theme profiles fixed. Both axes are in percent; the dashed line denotes equality. Four themes with the largest absolute point-estimate shifts are selected in each direction per agency, marked red below and named above. Other themes are black. In each upper text area, above-benchmark themes appear on the left and below-benchmark themes on the right, ranked by absolute shift. Gray circles highlight the selected themes without implying semantic neighborhoods, confidence regions or clusters. Label color encodes challenge-standardized minus observed share in percentage points. Label size increases monotonically with absolute shift under a common mapping; the first-ranked name in each direction is bold. Red scatter points denote selection only, and name positions are editorial. Selection affects annotation only and is not based on significance. Complete estimates, pointwise project-family bootstrap intervals, SDG contributions and leave-one-SDG-out diagnostics are provided in the source data.

## 当前复核文件

- 代码/figure5c_规整词云.py：当前成图脚本，包含全量数据、名称、圈选、矩形排布、重叠和裁切断言。
- 数据/规整词云_16个完整主题标注.csv：完整名称、原始份额、文字排版位置、字号与名称颜色。
- 数据/规整词云_灰圈范围映射.csv：两个灰圈的圆心与半径。
- 复核/规整词云_画面与数据断言.json、规整词云_nature_figure静态预检.json、规整词云_导出与一致性复核.json、规整词云_PDF渲染核验.png。

复核通过：108个点与原始估计保持不变；16个名称与已确认名单一致，PDF和SVG逐项核对完整名称与颜色；16项字号和颜色与前版逐项相同，源估计文件哈希不变；每机构一个无底框、两列左对齐且四行顶端对齐的规整文字区；所有选中点被灰圈包含；没有上方散点、引线、名称重叠或裁切；坐标轴标题与色带端点不重叠。PDF嵌入Arial，SVG保留文字，PNG/TIFF为600 dpi。nature-figure静态预检13项PASS、0项FAIL、1项WARN，静态宽度警告已通过实际PDF页框测量核验。
