# Figure 3c 固定主要科研承担地的跨目标贡献

## 当前版本

按用户指定的Python双向棒棒糖模板作结构适配。一个坐标框内显示12个SDG、24个原始贡献份额；每个SDG占一行，NSF为蓝色圆点，NSFC为红色方点。保留模板的逐行绘制、hlines横线、浅色外层端点、实心内层端点、中央基准线、框线及浅色虚线网格。

原模板展示正负Spearman相关系数。本图展示0—100%的贡献份额，因此中央基准从0改为50%，点的位置仍为原始百分比。棒线从50%延伸至端点，棒长表示距50%的差距，不能将棒长本身当作供给份额。没有把美国份额改成负数，也没有重新归一化。50%仅代表过半供给，不是统计显著性界限。

两国数据共享12行；每个点统一大小，所有数值保留一位小数。原显著性星号删除，字体改为与3a、3b一致的Arial，配色沿用蓝红机构配色。关闭原模板的60套配色批量输出。原始代码保持不变，副本保存在代码/模板原始副本；最初的配对点图作为对照保存在图/配对点图对照版。

## 模板字段映射

| 原字段或设置 | 本图字段或设置 |
|---|---|
| Algo | agency：NSF、NSFC |
| CellType | sdg：12个目标，按编号排序 |
| SpearmanR | fixed_top10_share_pct：真实贡献份额 |
| Sig | 删除；用真实份额数值作端点标签 |
| 一条记录一行 | 同一SDG的两条机构记录共享一行 |
| 零相关基准 | 50%份额基准 |
| 动态对称相关轴 | 固定0—100%线性轴 |

## 统计口径

分别固定3a的总体供给前十名单，不随SDG重新选择。每个点为该固定名单在相应SDG中的供给总量，除以本机构该SDG的全部样本供给，乘100%。项目族贡献守恒，多SDG按分数分配。city_weight已经包含项目族守恒权重，不重复乘权重。

全国分母包含所有地点，不应用3b的20项目族显示门槛。每国10个地点均在12目标的明细表中保留，因此有240条地点—目标明细；零供给按零记录。国家任务类别K01—K06不进入本图编码。

美国按县及同等单元汇总，中国按地级及同等单元汇总。两国行政单元范围、数量及资助观察时段不同；结果描述当前样本，不代表全部科研投入、城市绩效或资助制度的因果作用。“跨目标”不表示跨年份稳定，固定群体的合计贡献也不意味着其中每个地点都在全部目标中居于前列。

NSF固定前十的逐目标份额为16.319%—26.976%，NSFC为54.668%—68.633%。NSFC SDG17的全国目标分母由18个独立项目族支持，图脚保留该信息。全部目标的分数供给、项目族支持及参与地点数均在数据中；不引入未经计算的显著性星号或置信区间。

## 文件组织

- 代码/build_data.py：冻结4项输入，重建项目级分配，确认3a总体供给及固定名单，生成所有明细。
- 代码/plot_figure3c.py：正式入口，调用plot_figure3c_template.py。
- 代码/plot_figure3c_template.py：当前双向棒棒糖版，沿用模板函数结构。
- 代码/plot_figure3c_paired_reference.py：配对点图对照，仅输出至对照子目录。
- 代码/verify_data.py：独立CSV/字典逐记录重算、数据与实际绘制坐标核验、SVG和栅格检查。
- 代码/verify_pdf.py：实际PDF的文字、边界、重叠及24个数值标签检查，并生成渲染预览。
- 代码/run.ps1：按顺序运行构建、正式绘图、独立验证和PDF验证；解释器路径按当前工作站设置。
- 数据/固定总体前十地点.csv：20个固定地点及总体排名、供给份额。
- 数据/全部地点目标供给.csv：完整地点—目标供给与支持量。
- 数据/固定前十_12SDG_逐地点明细.csv：240条明细，包含零供给。
- 数据/Figure3c_12SDG固定前十贡献.csv：24个正式观测的分子、分母、份额及支持量。
- 数据/Figure3c_点位绘制对应.csv：每个SVG观测ID、真实横坐标、行号、端点标签和棒线起点。
- 图：正式PDF、SVG、600 dpi PNG、LZW TIFF和300 dpi预览。

绘图尺寸182.88 × 102.87 mm。正式栅格4320 × 2430 px。PDF与SVG保留文字，SVG的24个观测分别附有数据title。

## 中文图注

c，固定主要科研承担地的跨目标供给贡献。两国分别固定采用面板a按总体供给确定的前十科研承担地，计算其在各SDG中的合计供给占本机构相应目标全部样本供给的份额。圆点和方点分别表示NSF县及同等单元与NSFC地级及同等单元。横轴、端点位置和数值标签均为原始百分比；棒线由50%参照线延伸至各点，分别表现不足或超过一半供给的情况。浅色外层端点为统一样式，不编码另一变量。供给沿用项目族守恒与多目标分数分配，各目标分母包含全部地点，不应用面板b的显示门槛。NSFC SDG17由18个独立项目族支持，完整支持量见随图数据。该图描述固定前十地点群体的合计贡献，不表示每个成员均在所有目标中居于前列。

## English caption

c, Cross-goal contributions of the overall top 10 research locations. The ten locations with the largest overall supply in panel a are held fixed within each agency across all 12 SDGs. Each endpoint gives their combined share of national sample supply for the corresponding goal. Circles denote NSF counties and equivalents; squares denote NSFC prefecture-level units and equivalents. Axis positions and numeric labels show original percentages. Stems extend from the 50% reference to each endpoint, indicating contributions below or above half of national goal supply. Translucent endpoint halos are decorative and encode no additional variable. Supply conserves project-family contributions and is fractionally allocated across SDGs. National denominators include all locations, without the display threshold used in panel b. NSFC SDG17 is supported by 18 distinct project families; complete support counts accompany the figure. Results describe the combined contribution of each fixed cohort, rather than the prominence of every individual member in every goal.

## 验收结果

独立从11,753条源记录重算24个机构—目标结果及240条固定地点—目标明细，最大数值差3.18×10⁻¹²。固定名单与3a一致，所有源文件散列一致。24个SVG观测ID、原始坐标和一位小数标签逐项对应；所有棒线均从50%伸向真实份额。

正式PNG与实际PDF渲染均已目视检查。PDF为单页，12个SDG标签与24个份额数值全部存在；文字框无重叠、无越界。源码预检14项通过、0警告、0失败。详细结果位于数据/独立数据与导出复核.json、图面布局复核.json、绘图源码预检.json、图面复核/PDF复核.json。
