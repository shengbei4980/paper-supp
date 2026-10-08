# 单画框重构图及图注

已执行确认的版式方案。保存目录沿用作者指定位置，图内面板编号与当前手稿一致，标为a。

当前使用版本为Figure5a_单画框整合版_沿用Figure4色带_20pp。主图为183 × 116 mm，提供可编辑PDF与SVG、600 dpi PNG与TIFF，以及300 dpi预览。外框、类别及需求领域分隔线采用黑色；行标签仅显示N01—N19；全部342个效应色块保留；仅标注未四舍五入差值≤−20或≥+20个百分点的59个格内数值，统一保留一位小数并标明方向。其余283个数值标签省略，包括原29个四舍五入为零的标签；所有颜色仍使用未四舍五入的原始估计。留空表示未达到数值显示阈值，不表示零值、缺失数据或统计不显著。该阈值仅用于简化文字，不改变统计结论。深色格采用白字，其余格采用黑字。ESS列、相关图例、Low support图例、低支持斜线、Stable difference文字图例及全部黑点均已移除。主图仅显示全量条件差值的颜色与数值，不额外标记稳定性。完整支持量、原低支持分类及35个原稳定单元的统计结果仍在配套数据中，统计结果未重新计算。

## 中文图注

**a，三类相对供给位置中的需求—知识任务差异。** 在共同Target及资助时间熵平衡后，展示19项城市需求在六类知识任务上的条件份额差，计算为100×[pNSF(K|N,类别)−pNSFC(K|N,类别)]。三类根据各国自身SDG的CLR偏离点估计界定：低位M<−0.5，近似相称−0.5≤M≤0.5，高位M>+0.5；两国同名类别可包含不同SDG。红、蓝分别表示NSFC、NSF条件任务份额较高，单位为百分点。沿用指定参考图的红色#B64342与蓝色#3775BA，以白色为零值中心；色带为−90至+90个百分点的对称线性差值尺度。颜色使用未四舍五入的原始估计，仅为差值≤−20或≥+20个百分点的单元添加一位小数标签；全量估计包含原有低支持单元。数字留空表示未达到显示阈值，不表示零值、数据缺失或统计不显著；显示阈值不作为显著性判据。图面不单独标记统计稳定性。不确定性采用2,000次项目族Bootstrap估计，多重比较按全部342单元进行Benjamini–Hochberg校正。行标签使用需求代码，完整定义见表S6。N12对应建筑、交通与产业减碳；下方读数为该需求在两国各自近似相称类别中的K02和K04份额差。完整估计、区间、有效Bootstrap重复数、校正结果、稳定性判定及逐单元支持量见表S20和补充数据3。

## English legend

**a, Knowledge-task differences across supply–challenge classes.** Following entropy balancing on common SDG Targets and award-time features, cells show 100 × [pNSF(K | N, class) − pNSFC(K | N, class)] across 19 urban needs and six knowledge tasks. Classes are defined separately for each country's SDGs using CLR mismatch point estimates: lower, M < −0.5; near-aligned, −0.5 ≤ M ≤ 0.5; and higher, M > 0.5. Corresponding classes may contain different SDGs in the two countries. Red and blue indicate higher conditional task shares in NSFC and NSF, respectively; differences are in percentage points. The palette uses red #B64342 for negative differences, white at zero and blue #3775BA for positive differences, on a symmetric linear scale from −90 to +90 percentage points. Colors encode unrounded estimates, and numeric labels are shown to one decimal place only for unrounded differences ≤ −20 or ≥ +20 percentage points. Blank labels denote estimates below this display threshold, rather than zero, missing estimates or non-significant results. This annotation threshold is not a significance criterion. All point estimates are retained, including cells with low support; statistical stability is not separately marked. Intervals were estimated using 2,000 project-family bootstrap resamples, with Benjamini–Hochberg correction across all 342 cells. Rows use need codes; full definitions are provided in Table S6. The bold N12 row and bottom annotation identify the near-aligned decarbonization example discussed in the text. Full estimates, intervals, valid bootstrap counts, adjusted results, stability classifications and cell-specific support are provided in Table S20 and Supplementary Data 3.

## 色带统一

取指定参考图的NSF蓝色#3775BA与NSFC红色#B64342，将其白色渐变合并为红—白—蓝发散色带，零值对应纯白色。沿用国家颜色，差值方向与原图一致；参考图的0—100%份额范围不用于本图，本图保留−90至+90个百分点范围以覆盖全部原始差值。图例端点文字与对应色带同色。全量342个色块逐一核对新颜色映射，格内59个数字及位置与此前版本一致。

## 数值显示规则

比较15、20、25个百分点的绝对值阈值，对应85、59、40个格内数字。采用统一20个百分点阈值，显示17.3%的单元数值：显著降低文字密度，同时保留正文N12案例的−24.5与+30.1。25个百分点阈值会隐藏−24.5的案例读数。规则对正负差值及三类供给位置一致应用，不进行按结论或显著性择选。

## 复核与复现

19项需求仅显示原需求代码；六类任务定义保持不变。全部342个效应色块与原始差值逐项对应；59个格内数值的显示误差不超过0.05个百分点，283个绝对值小于20个百分点的数值标签已隐藏。N12近似相称类别K02为−24.4704个百分点，K04为+30.1129个百分点，图中按一位小数显示。原支持量及低支持判定在源表保留。

配套数据包含原完整估计表与支持量表的逐字节副本，以及342单元绘图映射。复制数据与原输入内容完全一致。SVG核对342个效应单元、59个满足显示阈值的数字、283个省略的标签和19个需求代码；全部黑点、ESS读数、低支持图例、斜线及Stable difference文字图例均为零。全部342个导出色块的颜色与绘图数据逐项一致。一个黑色主矩阵外框。所有文字均在画布内，文本边界检查无重叠，每个数字均在对应色块内。数字与底色的最小对比度为4.78。

PDF实测尺寸为183 × 116 mm，嵌入Arial常规与粗体字体。PNG/TIFF为4322 × 2740像素、600 dpi。nature-figure静态预检为13项通过、0项失败；关于变量定义宽度的1项警告由PDF物理尺寸实测解决。画面复核以最终PDF渲染为准。

使用原有Python绘图环境运行“代码”目录下的plot_integrated_heatmap.py即可复现；程序含全量数据、稳定性、支持量、字体边界及逐单元差值一致性断言。可访问上级原输入时复制输入；否则使用本目录中已保存的数据副本。

图中比较各国自身配置类别中的研究内容，不表示相同SDG内部的纯国别效应，也不衡量需求满足程度或实际实施效果。本次执行生成图件及配套替换图注，未回填Word手稿。
