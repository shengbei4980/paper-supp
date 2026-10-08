# 旧版存档：Figure5c参考式邻域放大简洁版

本版已由作者确认后的双向结构偏离主题版取代。当前文件和图注见`当前使用版本_双向结构偏离.md`。以下内容仅用于旧版比较。

正式图为`出图/Figure5c_参考式邻域放大_简洁版`，提供PDF、SVG、PNG和TIFF。这是根据最新反馈采用的版本。此前带引线的坐标放大版保留供比较，其图注不适用于当前图。

## 本次画面修订

- 上方只保留完整主题名称，去掉词云中的所有散点、坐标轴、延伸线及连接线。
- 下方每个机构保留全部54个主题。统一使用圆点，以淡灰圆形区域提示上方文字的来源。
- 上方保持与对应下方散点图的左右边界对齐，使用浅灰矩形背景；没有恢复圆形词云。
- 每个上方区域呈现一个重点主题及其附近8个主题。重点主题在中部加粗，其余名称分散排布，全部使用原始完整名称，仅作换行，无缩写或省略号。
- 颜色使用共同的红—灰—蓝连续色带；字体大小随份额变化绝对值增加。去掉各名称旁的数值以及K01–K06编码。

## 放大区域如何选择

每个机构先选择标准化份额与观测份额差值绝对值最大的主题作为中心。NSF的中心为“Disaster prevention and risk reduction”；NSFC的中心为“Policy implementation and regulatory capacity enhancement”。随后在下方定量坐标中，按欧氏距离选择距中心最近的8个其他主题。圆的半径为第8个邻近主题距中心的距离；当前每个圆内恰好9个主题，并与上方9个名称一一对应。

下方横轴为观测研究主题份额，纵轴为国家SDG挑战权重标准化后的主题份额，两轴单位均为百分比，且坐标等比例绘制。距离仅用于选出一个可以清楚放大的局部区域；它表示这两个份额上的接近程度，不表示语义相似、研究主题之间的因果关系或原始高维特征近邻。这里没有使用t-SNE。

上方放大的是选定区域的主题名称，文字位置为易读性重新排布，不是保留数值坐标的局部坐标图。因此不能从上方名称之间的距离计算定量差异。实际份额、差值及坐标全部以源数据和下方散点为准。

圆形区域在零值坐标边界处会自然裁切；这不裁切或排除任何主题点。下方全部108个点保留原始估计。圆外主题为灰色背景点；圆内主题和上方名称使用相同的连续色带，中心点加黑色描边，便于定位。

## 字号与色带的含义

颜色表示“标准化研究份额减去观测研究份额”，单位为百分点，共用−8到+8的范围。蓝色表示标准化份额增加，红色表示减少，接近零时为灰色。色带中的刻度保留，主题旁不重复写数值。

两国使用相同的字号映射：6.8 + 2.7×|差值|/全体主题最大|差值| pt；字号只强调结构变化的重要程度，不代表词频、项目规模或统计显著性。中心主题另加粗。上方完整名称共18个，下方仍为54×2个主题。

## 对结果4.4节的叙事责任

本图将SDG目标权重上的结构差异具体连接到原始项目编码中的研究内容：在保持各SDG内部主题组合不变的条件下，改变SDG权重会怎样改变整体研究主题份额。下方全量散点提供完整的主题组合比较，上方以各机构最大变化点附近的主题组作具体内容展示。

这是局部案例展示，不能把NSF放大区以负变化为主、NSFC放大区以正变化为主解释为两国所有主题的普遍方向。完整组合中增加与减少同时存在，所有主题净变化总和为零。该图可补充4.4节“目标结构偏离具体体现在哪些研究内容中”的证据，但不单独证明政策因果、实际需求缺口或最优资金分配。每个主题由哪些SDG贡献驱动，仍以完整1296单元贡献表及敏感性结果为准。

## 中文图注

**c，国家SDG挑战权重下的研究主题结构变化及局部内容展示。** 下方分别呈现NSF与NSFC全部54个实际出现的细分研究主题。每个圆点代表一个主题；横轴为观测科研供给份额，纵轴为保持各SDG内部主题比例不变、按国家SDG挑战权重重新加权后的主题份额，两轴单位均为百分比。虚线表示两种份额相等。每个机构以绝对份额变化最大的主题为中心，按上述二维份额坐标中的欧氏距离选择最近的8个其他主题；淡灰圆形区域包含该组9个主题，其完整名称在上方放大呈现。中心点加描边，对应名称加粗。上方无散点或引线，名称位置仅为易读性重新排布，不构成定量坐标。上方名称与圆内点使用相同的连续色带，表示标准化份额减去观测份额，单位为百分点；字号随变化绝对值增加，两国共用映射。圆外点保留为灰色背景。局部选择只控制文字标注，不改变或排除下方任何主题估计。NSF含6,207条记录、5,000个项目族，NSFC含5,546条记录、5,546个项目族。完整估计、项目族重抽样区间及逐SDG敏感性结果见源数据。

## English caption

**c, Research-theme shifts under national SDG challenge weights and enlarged local theme sets.** The lower plots show all 54 observed fine-grained themes in each agency sample. Each circle represents one theme. The horizontal axis shows its observed research share and the vertical axis its share after replacing SDG research-supply weights with national challenge weights while holding the within-SDG theme profile fixed. Both axes are in percent; the dashed line denotes equality. For each agency, the theme with the largest absolute share shift is selected as the focal theme, together with its eight nearest other themes by Euclidean distance in this two-dimensional share space. The gray circle identifies this nine-theme set, whose complete names are enlarged above. The focal point is outlined and its name is bold. The upper panels contain text only; label positions are rearranged for readability and do not constitute quantitative coordinates. Names and circled points share a continuous color scale encoding standardized minus observed share in percentage points. Label size increases with the absolute shift using a common mapping across samples. Themes outside the circle remain as gray context. The local selection controls annotation only and neither changes estimates nor excludes themes from the lower plots. The NSF sample contains 6,207 records in 5,000 project families; the NSFC sample contains 5,546 records in 5,546 families. Complete estimates, project-family bootstrap intervals and leave-one-SDG-out diagnostics are provided in the source data.

## 可复现文件与复核

- `代码/figure5c_参考式邻域放大.py`：重画当前版本并运行数据、邻域成员、文字重叠与裁切断言。
- `数据/实际研究主题估计_108项.csv`：沿用已核验的完整54×2主题估计，未重新改变分析。
- `数据/参考式放大_18个完整主题.csv`：中心与邻近主题、原坐标、差值、字号和颜色。
- `数据/参考式放大_圆形区域映射.csv`：两国中心、半径及主题数量。
- `数据/研究主题_SDG贡献_1296项.csv`及`研究主题_逐SDG移除_1296项.csv`：保留完整贡献分解与敏感性结果。
- `复核/参考式放大_画面断言.json`、`参考式放大_nature_figure静态预检.json`及`参考式放大_导出规格核验.json`：当前版本核验记录。

当前画面为183×180 mm，Arial，PDF和SVG保留文字，PNG/TIFF为600 dpi，预览为300 dpi。nature-figure静态预检13项PASS、0项FAIL、1项WARN；唯一警告为无法静态解析宽度变量，已用实际PDF页框核验。已检查最终PDF渲染、完整名称、上下图主题对应、全量点保留、连续色带、文字重叠及裁切。主图为点估计，既有2,000次项目族重抽样的95%逐点区间保留于源数据，未作显著性标注。
