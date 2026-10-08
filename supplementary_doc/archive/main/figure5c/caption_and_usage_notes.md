# Figure 5c：挑战标准化后的任务组合变化及其SDG来源

本图服务于结果4.4节的研究问题：科研供给与国家SDG挑战的目标结构偏离，对总体研究任务组合有何含义，哪些SDG构成这种变化？它在既有结构偏离与任务构成描述之后，增加固定目标内任务组合、替换目标权重的定量诊断。图中NSF与NSFC是本研究覆盖的基金项目样本，不能外推为两国全部科研活动。

## 中文图注

**c，按国家SDG挑战权重标准化后的研究任务组合变化。** 分别在NSF和NSFC样本内，保持每个SDG内部观测到的六类研究任务比例不变，将SDG层面的科研供给份额替换为国家挑战份额。上方以结构化词云显示全部六类任务的总体份额变化，单位为百分点（pp），正值表示标准化后份额增加，负值表示减少。词语字号按变化绝对值使用两列共用的映射，并保留最小字号；词语位置不表示语义距离，颜色和形状只区分任务。下方显示全部12个SDG对各任务变化的贡献，每列72个点；同一任务的12个贡献之和等于上方相应净变化。横向微移仅用于区分任务，点的大小固定。细线为项目族层面2,000次非参数重抽样得到的逐点95%百分位区间；每次同时重估供给份额和目标内任务比例，国家挑战份额保持固定。NSF含6,207条记录、5,000个项目族，NSFC含5,546条记录、5,546个项目族；同族记录按原项目族权重计量，多SDG记录按目标数分摊。该分析是任务组合的描述性标准化，不表示理想资源配置或任务层面的实际需求缺口，也不估计政策干预效果。

## English caption

**c, Research-task shifts under national SDG challenge weights.** Within each funding-agency sample (NSF and NSFC), the observed task profile within each SDG was held fixed while the research-supply share of each SDG was replaced by its national challenge share. The upper term displays show the resulting shifts in the shares of all six research tasks, in percentage points (pp). Positive and negative values denote increases and decreases, respectively. Font size emphasizes the absolute shift using a common scale with a readability floor; word positions do not represent semantic distances. Colors and marker shapes identify tasks. The lower plots retain all 12 SDGs and six tasks (72 points per agency). For each task, the 12 SDG contributions sum to the net shift shown above. Horizontal offsets separate tasks within an SDG and have no quantitative meaning. Thin lines indicate pointwise 95% percentile intervals from 2,000 nonparametric bootstrap resamples of project families, jointly re-estimating supply shares and within-SDG task profiles while keeping national challenge shares fixed. The NSF sample comprises 6,207 records in 5,000 project families; the NSFC sample comprises 5,546 records in 5,546 families. Original within-family weights were retained, and records associated with multiple SDGs were fractionally allocated across those goals. This descriptive standardization does not identify an optimal allocation, task-specific unmet demand, or a causal policy effect.

## 定义与读取方式

对每个机构分别计算。令 S_g 为科研供给的SDG份额，D_g 为国家挑战的SDG份额，p_kg 为SDG g内部任务k的观测比例：

- 观测任务组合：P_obs,k = Σ_g S_g p_kg。
- 挑战标准化任务组合：P_std,k = Σ_g D_g p_kg。
- 上方净变化：Δ_k = 100(P_std,k − P_obs,k)。
- 下方目标贡献：C_gk = 100(D_g − S_g)p_kg。
- 因此 Σ_g C_gk = Δ_k，且六类任务净变化总和为零。

这是一项加法恒等分解，不是Aitchison距离或CLR偏离的任务分解。颜色不表示正负；不同任务颜色沿用Figure5b的色相，并统一加深以保证小字号可读性。六类任务字号为8.5至12.5 pt，按绝对净变化线性映射；绝对变化至少4 pp的词语加粗以突出主要变化。字体面积没有额外统计含义，精确值以词下数字为准。

| 编码 | 完整任务名称 | 图上简写 |
|---|---|---|
| K01 | State measurement and problem diagnosis / 状态测量与问题诊断 | Measure & diagnose |
| K02 | Mechanism analysis and causal identification / 机制解析与因果识别 | Explain mechanisms |
| K03 | Scenario simulation and risk prediction / 情景模拟与风险预测 | Predict risks |
| K04 | Intervention design and performance optimization / 干预方案设计与效能优化 | Design & optimize |
| K05 | Planning decision support and policy design / 规划决策支持与政策设计 | Support decisions |
| K06 | Implementation monitoring and impact evaluation / 实施监测与效果评估 | Monitor & evaluate |

## 结果4.4节可采用的表述

在保持各SDG内部任务组合不变、以国家挑战份额替换科研供给份额后，NSF样本中规划决策支持和机制解析任务的总体份额分别增加4.73和4.38个百分点，干预设计任务减少5.41个百分点；NSFC样本中规划决策支持任务增加6.05个百分点，状态测量与问题诊断任务减少5.00个百分点。目标层面的贡献显示，任务组合的净变化同时包含不同SDG之间的增强与抵消，而非由单一方向的整体变化构成（Fig. 5c）。这些结果将目标结构偏离进一步转译为总体研究内容构成的变化。

上述段落应紧接以下限定或在同一段整合：规划决策支持的变化对SDG17较敏感；移除SDG17并分别重新闭合供给与挑战权重后，NSF和NSFC该任务的变化分别为约0.21和2.57个百分点。因此，该模式应解释为当前目标范围及挑战参照下的组合差异，不宜写作普遍的“规划研究供给不足”。完整逐目标移除结果见数据文件。

## 样本支持度、区间与敏感性

SDG17在NSF中由132个项目族支持、分摊项目族权重约71.78、有效项目族数约107.90；在NSFC中仅由18个项目族支持、分摊权重约9.58、有效项目族数约15.29。有效项目族数定义为 (Σw)²/Σw²，用于描述分摊权重集中度，不是新的观测样本数。较小支持度已通过项目族重抽样传播至图上的区间。

重抽样只评估当前项目样本内的构成不确定性，未包含外部SDG指标、挑战权重选择及编码误差的不确定性。区间为逐点区间，没有做同时区间或多重比较校正；本图未运行显著性检验、未报告P值、未使用显著性星号。逐目标移除分析会改变目标范围，属于影响诊断，不能直接当作原估计量的独立复现。

## 文件与复现

- `出图/`：PDF、可编辑文字SVG、600 dpi PNG/TIFF及300 dpi预览；尺寸183 × 164 mm。
- `数据/`：12项任务净变化及区间、144项SDG贡献及区间、144项目标内任务比例、24项目标支持度、144项逐目标移除诊断、配色表，以及输入参照和项目族字段快照。
- `代码/figure5c.py`：分析、项目族重抽样、绘图及可运行断言。原始输入路径和SHA-256列于`复核/数据核验.json`；源数据保留原位。
- `复核/`：nature-figure静态预检、导出核验和人工画面复核记录。

本机已验证的Python环境：`D:\xuexi\canshuhua\anaconda\Anaconda\envs\py311\python.exe`。运行脚本可从原始来源完整重算；加`--reuse`只使用已输出的结果表重新绘图；加`--check`执行表完整性与加法闭合检查。重算需原始项目路径仍可访问；重绘和检查可直接使用交付文件夹中的数据。

参考图仅提供浅灰词语概览与下方全量散点的上下布局启发。没有复用其关系词、国家案例、t-SNE坐标或近邻筛选方法。本次未改动手稿、Figure4、Figure5a或Figure5b。
