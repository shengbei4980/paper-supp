# Figure5c叙事与呈现方案：参考论文复核后建议

状态：作者已确认，图件已执行并完成复核。本文保留主题选择及科学叙事依据；显示方式已按后续要求改为每机构一个无底框的规则长方形文字区，下方采用浅灰圆、小黑点与红色选中点。上方属于文字排版，不再作精确坐标放大。当前文件和图注以`当前使用版本_散点位置文字放大.md`为准。统计估计未改变，原Word尚未修改；此前4.4建议补充段落保留于`当前使用版本_双向结构偏离.md`。

## Figure5c的核心问题

保持各SDG内部的研究主题构成不变，按各自国家SDG挑战权重重新组合供给后，哪些具体研究主题的相对份额变化最大？这些变化主要由哪些目标的供给—挑战差异驱动？

Figure4提供目标配置、Target内容与偏离来源；Figure5a/5b提供知识任务与文本行动阶段的相关描述。5c新增的是目标权重差异对应的完整主题组合诊断，不再重复六任务词汇、阶段比例或少数Target分布。该诊断是条件标准化，不是对科研效率、实际需求满足程度或实施效果的测量。

## 参考图核查结论

原论文PDF第22页，Extended Data Fig. 6：三个国家都以同一“邻居”概念为锚点；15个近邻由全部原始评估特征中的欧氏距离确定，二维t-SNE只负责显示全部159个关系。颜色编码正式性得分，邻域组成帮助解释同一概念的文化差异。该图a另报告跨地区的相关分析；b是具体案例展示，单靠b的三幅局部图不能建立现代化的因果效果。

可借鉴的是全量结构与局部名称的对应、连续颜色、无引线的文字呈现及共享规则。当前图在两个份额坐标上选取“最大变化点＋最近8个点”，既没有同一研究主题锚点，也没有语义近邻的评估基础。附近主题的坐标接近不意味着它们共同构成一个科学议题。这一选择只能解释局部示例，不足以作为主要结构偏离的主题筛选。

## 推荐唯一主方案

保留NSF和NSFC两列，上方各为一个无底框的规则长方形文字区，下方为全部54个主题的定量散点。两种偏离方向通过名称的连续色带区分：

1. 观测份额高于挑战参照：红色，标准化减观测的差值为负。
2. 观测份额低于挑战参照：蓝色，标准化减观测的差值为正。

各机构每个方向按差值绝对值选择前4项，共8个完整名称。选择只控制标注，全部54个点均保留；不按区间是否跨零筛选。两国规则相同，名单由数据确定，可以重合，也可以不同。上方以紧凑长方形范围呈现完整名称，左列高于参照、右列低于参照；两列各4项按差值绝对值排序，采用统一左对齐、四行顶端对齐和紧凑间距；字号较大的主题变化更大。位置只服务文字排版。名称共用连续红—灰—蓝色带和相同字号映射；下方红点只表示选中标注。

上方没有散点、引线或坐标轴，是选中主题的完整名称呈现。下方保留观测份额为横轴、挑战标准化份额为纵轴及等值线；两个轴等比例，两国共用范围。按作者最新参考式标记要求，16个被选中点标红，其他92个点标黑；每机构用一个无边线浅灰圆包围8个选中点。灰圈只显示被选主题分布范围，不表示语义近邻或聚类；圈内其他黑点不在上方标注。无需增加t-SNE、拟合线或连接线。

## 两种份额与方向

观测主题份额 O_t = sum_g S_g q_t|g；挑战标准化份额 R_t = sum_g D_g q_t|g；差值 Delta_t = R_t - O_t。S为研究供给的SDG权重，D为国家挑战的SDG权重，q为同一机构各SDG内部的主题构成。图中颜色与字号仍使用这一差值，不改成国别色。

名称红色表示O大于R，蓝色表示O小于R；下方红点另表示选中标注。色带标题明确限定为“Theme-label color: challenge-standardized − observed share (pp)”，两端标示“Observed > benchmark”和“Observed < benchmark”。名称旁不重复显示百分点数字。两种主题组合分别和为100%，全部主题差值之和为零。

## 已核对的重点主题与来源

下表数字供作者审查与源数据追溯，不放到名称旁。主要来源按SDG贡献绝对值排序；完整12项贡献加和得到该主题净差值。

| 机构 | 观测位置 | 原始完整主题名称 | 标准化−观测（pp） | 主要SDG来源 |
|---|---|---|---:|---|
| NSF | 高于挑战参照 | Disaster prevention and risk reduction | -5.24 | SDG11, SDG13 |
| NSF | 高于挑战参照 | Water pollution control and water quality improvement | -3.75 | SDG6, SDG12 |
| NSF | 高于挑战参照 | Infrastructure reliability and disturbance resistance | -3.06 | SDG9, SDG11 |
| NSF | 高于挑战参照 | Emergency preparedness and response | -2.34 | SDG11, SDG13 |
| NSF | 低于挑战参照 | Inclusion and opportunity protection for vulnerable groups | +3.53 | SDG10, SDG16 |
| NSF | 低于挑战参照 | Cross-sectoral and cross-organizational coordination | +3.21 | SDG17, SDG16 |
| NSF | 低于挑战参照 | Recycling, reuse and resource circularity | +3.06 | SDG12, SDG17 |
| NSF | 低于挑战参照 | Ecosystem integrity and functional restoration | +2.82 | SDG15, SDG13 |
| NSFC | 高于挑战参照 | Disaster prevention and risk reduction | -4.46 | SDG11, SDG13 |
| NSFC | 高于挑战参照 | Ecosystem integrity and functional restoration | -4.21 | SDG15, SDG13 |
| NSFC | 高于挑战参照 | Outdoor air-pollution control | -2.37 | SDG11, SDG17 |
| NSFC | 高于挑战参照 | Water pollution control and water quality improvement | -2.18 | SDG6, SDG12 |
| NSFC | 低于挑战参照 | Policy implementation and regulatory capacity enhancement | +6.02 | SDG17, SDG16 |
| NSFC | 低于挑战参照 | Reduction of socioeconomic and spatial inequalities | +3.30 | SDG10, SDG11 |
| NSFC | 低于挑战参照 | Inclusion and opportunity protection for vulnerable groups | +2.49 | SDG10, SDG11 |
| NSFC | 低于挑战参照 | Cross-sectoral and cross-organizational coordination | +2.32 | SDG17, SDG16 |

## 同一主题的跨国对照

“Ecosystem integrity and functional restoration”的NSF观测份额约6.98%，标准化约9.81%；NSFC分别约13.31%与9.10%。前者在参照下增加，后者减少。这个共同主题会在两国的不同方向文字组出现，直接表现同一研究内容在不同国家挑战参照下的相对位置，远比更换两个中心词后展示坐标邻居更符合跨国比较的责任。

共同参照是同一分析规则，并非两国使用相同国家挑战权重。因此该对照不是两国实际主题需求差的直接估计。

## 与4.4节的证据联系

应在正文或图注明确指出若干源头：SDG11的配置差异主要对应灾害预防及应急准备；NSF的基础设施可靠性变化主要由SDG9与SDG11贡献；治理和合作权重差异对应政策实施与跨组织协调，其中NSFC政策主题主要由SDG16和SDG17贡献。社会包容类主题还受到SDG10驱动，不能把所有蓝色主题都归入治理合作。

这形成“目标权重的结构差异 → 具体主题组合的变化 → 用主题名称说明研究内容”的可追溯顺序。它是统计贡献与条件组合的联系，不是已识别的政策因果链。正文可据此收束目标配置与研究内容的不同层次；5a/5b继续承担任务与文本阶段的相关叙事，不由5c替代。

## 解释与验收

全部54个主题和项目族区间继续保留。上方8项约覆盖NSF全部主题绝对份额变化总和的45.1%、NSFC的50.4%；这只是标注范围说明，不能称为Figure4中总体Aitchison距离的贡献比例。其他重要主题不因没有文字而被排除。

所有选中项当前有效项目族支持量均高于10，但SDG17部分条件主题来源较少，NSFC政策与协调主题对该目标的敏感性必须继续保留。项目族重抽样区间见既有源数据；不因前4筛选直接宣布统计显著性或排名稳定性。完整SDG贡献和逐目标移除结果沿用已核验数据，无需为了画面重跑Bootstrap。

验收必须确认：上方选中名单与下方红点完全一致；所有108点原坐标不变；名称正负方向与色带一致，红点的选中标记含义单独明确；完整名称无省略；字号跨国共用映射；灰圈包含全部被选点但不宣称语义邻域；不显示上方散点和延伸线；双国均显示两个方向；图注说明条件标准化；Figure4的目标来源与主题贡献对应；导出后按最终尺寸检查文字重叠及裁切。

建议主标题：Research-theme differences under national SDG challenge weights。

在现有数据下，本方案能够描述目标权重偏离对应的研究主题组合变化。国家挑战数据只到SDG层级，因此不能把R称为实测的主题需求份额，也不能把O<R直接写成真实社会需求未满足。若要回答这个更强的问题，需要独立的主题层需求测量。
