# 旧版存档：Figure5c全量散点与重点区域放大标注版

本版已由最新的“参考式邻域放大简洁版”取代。当前使用文件和图注请见`当前建议版本说明_参考式放大.md`；以下内容仅用于旧版比较。

正式文件：`出图/Figure5c_全量散点_重点区域放大标注版`（PDF、SVG、PNG、TIFF）。本次按参考图“全量散点＋选定区域放大标注”的关系重新组织画面。此前全量文字版、19主题归并版及六任务词语版保留供比较；它们的图注不要用于当前版本。

## 逐项修订

| 用户反馈 | 当前处理 |
|---|---|
| 词语旁的−1.78 pp等数字可删 | 上方不显示数值标签；颜色表示标准化份额与观测份额的差值，精确值存入源数据 |
| 上方应呈现散点的重要位置 | 上方直接放大下方灰框中的区域，点的观测坐标和标准化坐标不变。主题完整名称以引线对应原点，未独立生成词频云或投影 |
| 全量长名称冗长 | 下方每国54个主题全量保留，上方只标注绝对份额变化最大的8个主题；框内其他主题作为淡化的背景点保留 |
| 重要的名称应较大 | 两国共用字号映射：6.5 + 3×|Δ|/全体最大|Δ| pt；当前标注字号约7.7至9.5 pt。偏离更大的名称更大 |
| 两国词语应体现各自特点 | 分别根据本机构数据选择8个重点主题；两国重点名单各有3个不同主题，5个共有主题保留 |
| 下方K编码和多种符号难读 | 全部点均为圆形，画面无任务K编码、任务符号图例或净变化菱形 |
| 上下应对齐且易追溯 | 放大区与对应全量图框左右边界一致，下方灰框与连接线明确指出放大范围 |

参考图中的邻域选择基于其原始评估特征中的距离；这里的重点选择基于本研究主题份额的结构变化。只借鉴局部放大与真实点位标注的表达关系，不声称两者具有相同的近邻或语义空间解释。

## 当前每个点与名称代表什么

一个圆点对应一个原始项目编码中的细分需求研究主题，不是一条项目记录，也不是一个SDG。每国实际出现54个主题，全部显示在下方。横轴是该主题的观测科研供给份额，纵轴是保持各SDG内部主题比例不变、按国家SDG挑战份额重新加权后的主题份额。

虚线表示两种份额相等。点在线上方表示标准化份额增加，线下方表示减少。主题名称和重点点使用共同的红—灰—蓝连续色带，范围−8至+8个百分点；其他点采用同一映射并降低透明度作为背景。较大的点仅标识上方选中标注的主题，不表示更多项目。字体大小强调份额变化绝对值，不能解释为词频或精确科研规模。

下方灰框是上方真正显示的坐标范围。上方背景点保留了该范围内的其他主题（NSF与NSFC具体数量见范围映射表），不是只画8个点。名称为防止重叠允许轻微位移，点的位置不移动，引线维持对应关系。SVG中每个点可通过悬停标题查阅完整主题名及精确数值。

## 中文图注

**c，科研供给与国家SDG挑战权重差异对应的研究内容变化。** 下方分别显示NSF与NSFC全部54个实际出现的细分研究主题。每个圆点代表一个主题，横轴为观测科研供给份额，纵轴为保持各SDG内部主题组合不变、按国家SDG挑战权重标准化后的份额，两轴单位均为百分比；虚线表示相等。各机构绝对份额变化最大的8个主题以较大的点突出，其所在区域在上方放大，并用原始完整主题名称标注。灰框及连接线表示实际放大范围，框内其他主题点保留为淡化背景。点的统计坐标保持不变，名称为避免重叠稍作位移并以引线连接。词语及点的颜色共同表示标准化份额减去观测份额，单位为百分点；字号按变化绝对值强调主要偏离，两国使用相同映射。8主题筛选只控制标注，没有排除下方的任何主题或改变估计。NSF含6,207条记录、5,000个项目族，NSFC含5,546条记录、5,546个项目族。完整主题估计、项目族重抽样区间与逐SDG敏感性结果见源数据。

## English caption

**c, Research-content differences under national SDG challenge weights.** The lower plots retain all 54 observed fine-grained research themes in each funding-agency sample. Each circle represents one theme. The horizontal axis shows its observed research share and the vertical axis its share after replacing SDG research-supply weights with national challenge weights while holding the within-SDG theme profile fixed. Both axes are in percent; the dashed line denotes equality. The eight themes with the largest absolute share shifts in each sample are highlighted with larger circles and labeled by their complete original names in the magnified regions above. Gray rectangles and connecting lines identify the corresponding coordinate ranges; other themes within those ranges remain as faded context. Point coordinates are unchanged. Labels are displaced only to avoid overlap and linked to their points. A common continuous color scale encodes standardized minus observed share in percentage points; label size emphasizes the absolute shift using the same mapping across samples. This selection controls annotation only and does not exclude themes from the full plots or alter estimates. The NSF sample comprises 6,207 records in 5,000 project families; the NSFC sample comprises 5,546 records in 5,546 families. Complete estimates, project-family bootstrap intervals and leave-one-SDG-out diagnostics are provided in the source data.

## 计算与解释边界

沿用54细分主题版已经核验的估计。项目族权重、多SDG和多主题标签按原方案分摊；各SDG内部主题比例固定，替换SDG权重得到标准化主题份额。两种主题组合分别总和为100%，全部主题净变化总和为零。主题变化可由12个SDG贡献严格加和得到，完整1296单元数据保留。

上方用相同的绝对变化排序规则展示主要偏离，不是显著性筛选，也没有通过近邻或t-SNE生成坐标。NSFC政策实施与监管能力提升的变化对SDG17较敏感；主题支持度、2,000次项目族重抽样的逐点95%区间及逐SDG移除结果仍保留。挑战标准化是描述性组合诊断，不能直接解释为最优资源分配、实际主题需求缺口或政策因果效果。它服务于4.4节中“目标结构偏离具体对应哪些研究内容变化”的叙事环节。

## 数据与复核

- `数据/实际研究主题估计_108项.csv`：全部54×2主题的观测份额、标准化份额、差值、区间与支持度。
- `数据/重点区域_16个完整主题标注.csv`：每国8个重点的主题名称、原坐标、差值、字号及标签位置。
- `数据/重点区域_上下图范围映射.csv`：下方灰框及上方实际放大范围。
- `数据/研究主题_SDG贡献_1296项.csv`及`研究主题_逐SDG移除_1296项.csv`：完整贡献和敏感性。
- `代码/figure5c_重点区域放大.py`：读取上述已核验估计、重画当前版本及执行断言；分析重算方法见全量主题版说明。
- `复核/重点区域版_*`：画面断言、nature-figure静态预检、实际PDF导出规格及渲染核验。

当前图183 × 193 mm，Arial；PDF与SVG保留文字，PNG/TIFF为600 dpi，预览为300 dpi。已按nature-figure检查主题全量保留、选中规则、坐标保持、放大范围映射、完整名称、共同色带、字号、文字重叠、裁切及导出。静态预检13项PASS、0项FAIL、1项WARN；警告为无法静态求解宽度变量，实际PDF页框已核验。主图显示点估计，完整区间保留在数据表，未作显著性推断。
