# Figure5c全量实际研究主题版

当前建议使用`出图/Figure5c_全量真实研究主题_词云散点对应版`。此前六任务词语版及其图注保留供比较，但不能套用到本次主题版。

## 逐项解决的问题

| 问题 | 本次处理 | 验收依据 |
|---|---|---|
| 上方带数值标签显得重复 | 删除全部词语旁的百分点数字；方向和强度由统一连续色带表示 | 上方108个主题名称均无附加数字；精确值保留在数据表 |
| 固定六任务名称不能表达具体内容 | 改用项目原始编码中实际出现的54个细分需求研究主题，保留原始英文完整名称 | 每国54个主题全量展示；两国原始字段与标签逐行核对 |
| 两国词语呈现机械一致 | 分别按各国观测主题份额确定字号与布局，颜色取各国主题的标准化变化 | 两国字号、排序、位置和颜色分别由真实数据生成，采用共同映射 |
| 词语与散点不是同一统计对象 | 统一为细分研究主题：每个词语对应一个圆点 | SVG中108个词语与108个点的机构—主题键集合完全一致 |
| K编码及多种标记增加辨识负担 | 删除画面中的K编码、任务行与汇总菱形，点全部使用圆形 | 每个点现在只表示一个具体研究主题；不再混用任务汇总和目标贡献 |
| 上下区域对齐及简洁性 | 浅灰矩形主题区与对应散点图框严格等宽对齐；两国共用坐标轴范围、字号映射和色带 | 自动检查左右边界相同、全部主题保留、无词语重叠和图外裁切 |

两国都实际覆盖这54个主题，因而名称集合相同。这个共同覆盖来自原始数据；国家差异体现在各主题的科研供给权重、挑战标准化变化及布局上。没有为制造不同词集而删掉共有主题。上方主题采用研究中既有的细分编码体系，不是重新从原文挖掘的自由词汇，也没有将六任务名称拆开后当作独立研究主题。

## 当前图的含义

上方字号强调该主题在本机构样本中的**观测科研供给份额**。主题颜色表示保持每个SDG内部观测主题组合不变、替换SDG权重后的**主题份额变化**。红色为标准化后份额减少，蓝色为增加，近零为灰；两国和上下图共用−8至+8百分点的连续色带。字号使用相同单调函数，保留最低可读字号；字体面积不能作为精确比例测量。

下方每个圆点与上方一个完整主题名称对应：横坐标为观测科研供给份额，纵坐标为挑战标准化后的科研供给份额。虚线表示两种份额相等；线上方对应蓝色正变化，线下方对应红色负变化。点的大小固定，没有项目数或显著性含义；所有54个点均保留，不使用抖动或t-SNE。每国直接标注观测份额最大、增加最多和减少最多的三个主题，其他点的完整名称与数值可在SVG悬停标题和数据表中查询。

## 计算定义与分摊口径

每国独立计算。对每条项目记录，以原项目族权重计量；一条记录编码了G个SDG和T个细分主题时，各SDG—主题共现单元分摊权重w/(G×T)。每个项目族的全部分摊权重为1。该规则按项目内标签共现构造联合分布，不表示逐个主题与逐个SDG之间已被独立人工确认的语义联系，也不重复累计整条记录。

设S_g为供给的SDG份额，D_g为已有国家挑战参照的SDG份额，q_tg为SDG g内主题t的分摊比例：

- 观测主题份额：O_t = Σ_g S_g q_tg。
- 标准化主题份额：R_t = Σ_g D_g q_tg。
- 词语及圆点颜色：Δ_t = 100(R_t−O_t)，单位为百分点。
- 目标贡献：C_gt = 100(D_g−S_g)q_tg，完整数据保留全部1296个机构—SDG—主题单元。
- 加法关系：Σ_g C_gt = Δ_t；各国O和R分别总和为1，全部主题净变化总和为0。

沿用此前国家挑战参照，原始记录重新构建54主题条件组合。供给SDG份额与既有参照核对一致。该图推进的是目标结构偏离的研究内容含义，不是CLR或Aitchison距离的细分分解。它不把标准化份额作为主题实际需求、最优经费方案或政策效果。

## 中文图注

**c，科研供给与国家SDG挑战权重差异对应的细分研究主题变化。** 分别在NSF与NSFC样本内，按原项目族权重及多标签分摊规则估计54个实际出现的细分需求研究主题。上方矩形主题云全量保留各国主题的原始完整英文名称；字号强调观测科研供给份额，位置仅用于排布。颜色表示保持各SDG内部主题组合不变、以国家挑战份额替换科研供给SDG份额后，主题份额的变化。下方每个圆点与上方一个主题对应，横轴为观测份额，纵轴为挑战标准化后的份额，两轴单位均为百分比。虚线表示两种份额相等；上下图和两国共用以零为中心的连续色带，单位为百分点。每国标注观测份额最大、正变化最大及负变化最大的主题，其余主题仍全部保留。NSF样本含6,207条记录、5,000个项目族；NSFC含5,546条记录、5,546个项目族。主图呈现点估计，主题份额及变化的项目族重抽样95%百分位区间、支持度和逐SDG移除诊断见随图数据。

## English caption

**c, Fine-grained research-theme shifts under national SDG challenge weights.** Within the NSF and NSFC samples, 54 observed fine-grained need-oriented research themes were estimated using original project-family weights and fractional allocation across co-occurring SDG and theme labels. The rectangular theme displays retain the complete original English coding labels. Font size emphasizes the observed research share; word positions serve layout only. Color indicates the change in theme share when the observed within-SDG theme profile is held fixed and SDG research-supply weights are replaced by national challenge weights. Each circle below corresponds to one theme above. The horizontal axis shows its observed share and the vertical axis its challenge-standardized share, both in percent. The dashed line indicates equality. A common zero-centered color scale encodes the signed difference in percentage points across both samples and both display types. The largest observed share, largest increase and largest decrease are directly labeled for each sample; all remaining themes are retained. The NSF sample comprises 6,207 records in 5,000 project families; the NSFC sample comprises 5,546 records in 5,546 families. The main figure shows point estimates; project-family bootstrap 95% percentile intervals, support counts and leave-one-SDG-out diagnostics are provided in the accompanying data.

## 4.4节可采用的结果表述

将SDG目标结构差异进一步转译为细分研究主题的组合变化后，两国呈现不同的内容构成。NSF的观测科研供给中，水污染控制与水质改善所占份额最高；按国家挑战权重标准化后，对脆弱群体的包容与机会保障主题增加较多。NSFC的观测供给中，生态系统完整性与功能恢复所占份额最高；标准化后，政策实施与监管能力提升主题增加较多。灾害预防与风险降低主题在两国均出现较大的相对份额减少（Fig. 5c）。这些变化反映目标权重差异如何对应研究内容组合的重排。

精确数值供正文按需取用：NSF水污染控制与水质改善的观测份额8.96%，标准化份额5.21%；对脆弱群体的包容与机会保障由1.30%变为4.83%。NSFC生态系统完整性与功能恢复由13.31%变为9.10%；政策实施与监管能力提升由1.08%变为7.10%。两国灾害预防与风险降低分别由7.48%变为2.25%、由7.06%变为2.60%。这里的“减少”描述相对组合变化，不意味着应削减该领域科研或降低其社会重要性。

## 区间、支持度与敏感性

各国进行2,000次项目族非参数重抽样，全部2,000次有效。每次联合重估供给份额与SDG内部主题比例，挑战权重固定。主题出现较少时保留其原观测估计和区间，不按美观或阈值删掉主题。为了保持主图简洁，误差线存入完整源数据；图上颜色不是显著性判断。未执行假设检验，也没有同时区间或多重比较校正。外部指标及编码误差的不确定性未包含在重抽样区间中。

NSFC政策实施与监管能力提升主题的变化为+6.02个百分点，其中SDG17贡献约+3.16个百分点。移除SDG17并重新闭合两类目标权重后，变化约+3.43个百分点；对SDG17参照和小样本支持的敏感性需保留。NSF对脆弱群体的包容与机会保障的净变化约+3.53个百分点，移除SDG17后的诊断约+4.04个百分点。逐SDG移除改变目标范围，不能当作同一个估计量的独立复现。

## 交付和复核

- `数据/实际研究主题估计_108项.csv`：主题全名、观测份额、标准化份额、变化、各自95%区间和项目族支持度。
- `数据/研究主题_SDG贡献_1296项.csv`：全部目标—主题共现比例和贡献及区间。
- `数据/研究主题_逐SDG移除_1296项.csv`：全部影响诊断。
- `数据/主题云图_全量字号颜色坐标.csv`：词语、颜色、字号、位置的可核对映射。
- `代码/figure5c_全量研究主题.py`：完整分析与绘图。默认重算；`--reuse`重绘；`--check`执行完整性和加法闭合断言。
- `复核/研究主题版_*`：画面断言、静态预检、导出规格及最终PDF渲染。

按nature-figure完成数据完整性、主题名称、共同色带、上下映射、矩形对齐、字号、重叠、裁切和导出检查。正式图183 × 244 mm，Arial；主题字号约6.05至8.6 pt；PDF与SVG保留文字，PNG/TIFF为600 dpi，预览为300 dpi。为同时全量显示54个完整长名称，需要这个展示尺寸；整版排入Figure5时应保持文字可读，不宜缩为半栏。

静态预检12项PASS、0项FAIL、2项WARN：宽度变量不能由静态扫描求值，已用实际PDF页框核验；随机数代码仅用于真实项目族非参数重抽样，不生成虚构观测。
