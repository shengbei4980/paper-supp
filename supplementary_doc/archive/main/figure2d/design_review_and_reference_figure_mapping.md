# 重设计说明：知识任务子级结构与干预联系

本版替代上一版的人为圆团布局。最终图为 `图/Figure2d_六类任务色系与子级结构.png/.pdf/.svg`。

2026-09-24 更新：K06.1 的斜线覆盖层已经移除；用扇区 † 表示低支持量。K/L 图例均采用原始数据全称。正负差值分别直接使用 Figure1a 的完整蓝、红色带，保留其浅色端点；数值量程仍为本图差值的 ±90。详见 `20260924修正与子级簇解读.md`。

## 1. 重新阅读手稿后的判断

已从用户给定的当前 DOCX 重新提取并阅读 4.2 节全部正文及图2图注，原文保存在 `当前手稿4.2原文.txt`。

4.2 的论证依次为：平衡共同议程后连接差异缩小；相近问题路径下知识任务仍有不同侧重；这些侧重进一步联系到干预和行动组织。新增 d 应承接第三层，并让读者看到六类任务内部更细的结构。上一版将项目人为铺成 16 个圆盘，只能表示归属数量，圆盘之间的位置缺少实质含义；这没有充分服务这条论证。

新版采用两部分协同表达：

- **中心**：全部项目的“需求—压力—系统—知识子级—干预子型”编码相似性地图，显示同一任务内部不同的问题和行动组合。
- **外圈**：16 个正式知识子级与 9 类干预的完整条件份额差，承担中美比较的定量证据。

正式编码中的知识子级仍为 16 类，不能为了形状好看新增或减少。但中心的局部分支不再被硬性画成 16 个团，也不固定每类只有两、三个小球。11,753 个项目实际包含 8,399 种不同的五块编码组合，细分结构由这些组合的相似性形成。8,399 是编码组合数，不是算法发现的“簇数”。本版没有提出新的离散聚类分类。

## 2. 参考图逐项对应

| 参考要素 | 新版实现 | 相比旧版的修正 |
|---|---|---|
| 中央多色、非圆盘式细分结构 | 数据计算的二维项目点图 | 取消手工圆团、排列抖动、装饰性连接 |
| 每个大类统一色系 | K01–K06 六色，其所有子级/项目继承父级色 | 中心不再按 NSF/NSFC 红蓝混色 |
| 只标必要簇标签 | 中心仅六个 K 编码 | 移除逐簇计数、重复名称和大段中央说明 |
| 开口环绕中央地图 | 北向起点、逆时针 270° | 沿用用户给定模板的组织方式 |
| 平滑圆形色块 | 每一角列细分 80 个弧段 | 修复 16 个大角列造成的折线/多边形外观 |
| 圆框与分类带贴合 | 统一圆心、等比例坐标与嵌套半径 | 内侧六色带全部沿圆弧绘制 |
| 开口区图例 | 层级说明和六类任务图例位于右上开口 | 中心图例移出数据区域 |
| 底部连续色条 | 统一红—灰—蓝差值色条 | 保留 Figure1a 色值和 NSF−NSFC 方向 |
| 外圈类型标注 | 保留全部 16 个正式子级；缩短冗长显示名 | 全称另保存在编码名称 JSON 中 |

中心类别色：K01 `#287D8E`，K02 `#679D7A`，K03 `#C3A253`，K04 `#D38658`，K05 `#AC627A`，K06 `#8276A5`。同一父级的子级没有再分配额外颜色。圆环差值与中心类别使用两个不同的图例，避免把任务类别颜色解读为国别差值。

## 3. 中心布局如何产生

原始输入全部来自项目编码 CSV，无文本重新编码、虚构点或抽样删点：

| 特征块 | 原字段 | 编码维数 | 距离权重 |
|---|---|---:|---:|
| 需求子议题 | urban_need_subtopic_multi | 54 | 1/12 |
| 压力子型 | urban_pressure_subtype_multi | 21 | 1/12 |
| 系统子型 | urban_system_subtype_multi | 30 | 1/12 |
| 知识任务子级 | primary_knowledge_subtype_multi | 16 | 1/2 |
| 干预子型 | intervention_subtype_multi | 26 | 1/4 |

每块先作多标签二值编码，再将该块的每行归一到单位欧氏范数，最后乘距离权重的平方根。拼接后有 147 维，每个项目的总平方范数为 1。这样，多标签较多或代码总数较多的字段不会仅因列数更多而主导距离。

这里的 1/2、1/4、1/4 是**展示设计中声明的特征权重**：知识任务占一半，干预占四分之一，需求/压力/系统背景合计四分之一。它们不是回归结果、贡献率或数据估计的效应量。其作用是让图面围绕本节的知识任务问题组织，同时保留问题情境的细节。

最终中心为 t-SNE：欧氏距离、perplexity=80、PCA 初始化、学习率 auto、1,250 次迭代、随机种子 20260923、Barnes–Hut angle=0.5。颜色仅在布局完成后按主知识任务赋值。机构、国别和 Figure2c 平衡权重均未作为投影特征。

每个点对应一个项目，合计 NSF 6,207、NSFC 5,546；一个项目只绘制一次。多子级归属保留在特征向量内，不再用重复点表示。原始投影坐标仅平移并等比缩放以适配圆内区域，没有非线性拉伸、手工移动单个簇或随机补点。输入和参数有 SHA256 缓存签名，改变输入或参数后不会复用旧坐标。

中心是一幅**按已编码特征构建的描述性相似性地图**。知识类别本身参与了距离定义，不能将颜色分离作为独立验证分类有效性的证据；t-SNE 的全局方向、类间空隙、包络面积和密度也不作为定量结论。国别差异的证据来自外圈统计。图面底部已注明投影不能用于检验国别差异。

## 4. 实际比较过的方案

已输出三组布局比较和一张完整替代图，保存在 `图/布局比较/`：

1. 仅“知识子级＋干预子型”：输入重复组合较多，容易出现大量重叠小点团，不足以表达城市问题情境。
2. 五块编码等权：展示了问题背景，但需求、压力、系统合计占 60%，知识任务的颜色结构较分散。
3. 知识任务主导的五块编码：保留问题背景并突出任务内部结构；同时比较 PCA、t-SNE 30 和 t-SNE 80。

采用第三组的 t-SNE 80 作为主图，因为其局部分支连续性更清楚，适合在圆环内阅读。保留 t-SNE 30 的完整替代图，可查看更碎的局部结构。选择基于任务适配与可读性，没有将不同 perplexity 的 KL 数值直接作为优劣检验。PCA 的前两维保留信息较少，多个任务在中心交叠，因此作为比较图保留。

与参考截图相比，新图没有强行制造同样的扭曲岛屿轮廓：真实编码维度、重复项目组合和样本量决定了能呈现的形态。六类颜色、局部分支、稀疏文字、开口圆环和图例位置均尽量接近参考；点的来源和相似性计算仍可追溯。

## 5. 外圈分析与原结果的关系

沿用已经独立复核的 144 项子级×干预统计，未因改变点图样式重新调节这些数值。每个项目的 Figure2c 平衡权重先平均分到其知识子级，再平均分到干预类型；按机构、子级归一到 100%，然后计算 NSF−NSFC 的百分点差。

135 项可以计算差值，其中 K06.1 的 9 项因支持量低在扇区标签以 † 表示，不再添加斜线覆盖。K06.3 在 NSFC 没有记录，其 9 个条件差值为未定义，显示 ×。全部正式子级均保留，包括这些稀疏或单侧缺失的子级。

统计区间沿用 2,000 次机构内记录 Bootstrap，平衡权重固定；有至少 95% 有效重抽样的 126 项比较统一 BH 校正。55 个黑点同时满足区间不跨零、q<0.05、两方有效样本量均≥10。色条 −90 至 +90 完整覆盖有限数值，没有截断。

外圈仍是全体项目的主任务子级干预构成，不能解释为 Figure2c 那 54 条路径内部的条件比较。图 d 的新增方法应与图注一起补入手稿，中心地图不应独立承担因果或互补性结论。

## 6. 建议英文图注

**d, Knowledge-task substructures and intervention profiles.** The central map shows all 11,753 projects using a t-SNE projection of coded need, pressure, system, knowledge-task and intervention subtypes. Colours identify the six primary knowledge tasks and are inherited by their constituent subtypes. Each project appears once; multi-label assignments are retained in its feature vector. Binary features were normalized within each block before applying squared-distance weights of 1/2 for knowledge subtypes, 1/4 for intervention subtypes, and 1/12 each for need, pressure and system subtypes. The map is descriptive: category separation is not an independent validation of the coding scheme, and global distances, island areas and densities are not quantitative results. The outer ring displays the complete set of 16 coded knowledge subtypes and nine intervention layers (L01 outside to L09 inside), coloured by target–year-balanced conditional-share differences between NSF and NSFC. Black dots indicate 95% record-bootstrap intervals excluding zero, BH-adjusted q<0.05, and effective sample sizes of at least 10 in both agencies. The dagger denotes low support for the K06.1 sector (NSF n=5; NSFC n=1); its descriptive estimates are shown without inferential markers. Crosses mark undefined comparisons for K06.3, which had no NSFC observations. Bootstrap intervals used 2,000 within-agency resamples with balancing weights held fixed; the 126 comparisons having at least 95% valid resamples formed the BH family.

## 7. 最终复核

- 当前 129 项检查全部通过，包含所有项目 ID、147 维特征的独立重建、六色继承、全部点位与统一坐标变换、16 个子级和 144 项单元、15 个图例全称、色带精确继承、缺失值、显著性条件及输出文件。
- 原统计 200 项复核按未变化的输入复用；已验证原始源文件哈希、统计表、支持量表和 Bootstrap 数组与已通过版本一致。
- academic-figure-skill 完成字体、导出和人工视觉复核。固定技能色板由本次用户要求的六类别颜色覆盖；手工图例位置和毫米除法表达式经实际渲染检查，不将规则识别不足当作未检查通过。
- 输出 PDF 实测为一页、183×210 mm，包含全部 16 个子级代码；PNG 为 600 dpi，SVG 保留文字及矢量对象。
- 圆环每角列 80 段细分，最大弧弦径向误差约 0.000023 绘图单位。中心点、类别带和热图采用同一圆心；中心最大半径 9.05，小于类别带内半径 9.35，所有项目点均完整保留。

本版按 183 mm 宽度设计。与 a–c 合版时应给 d 足够宽度，避免缩小后损失局部分支和 16 个外圈标签的可读性。
