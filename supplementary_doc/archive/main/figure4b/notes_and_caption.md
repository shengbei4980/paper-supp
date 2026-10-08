# Figure4d：全量 Target 正文紧凑版

## 交付

- 正文画布：**183 × 110 mm**，高度比原简洁版 248.92 mm 减少 **55.8%**。
- `图/Figure4d_全量Target_正文紧凑重构.pdf`：正文排版首选，矢量、嵌入字体。
- 同名 SVG（文字可编辑）、600 dpi PNG、600 dpi TIFF。
- `图/配套_全量Target_份额区间与JSD.pdf`：各 SDG 的份额区间与 JSD 配套页，沿用已核查的原估计。
- `数据/`：全部点估计、区间、支持量、完整标签，以及实际用于本图的成对数据。
- `render_figure4d.py`：独立重绘脚本；`run_workflow.py`：本次 modelviz 服务流程。
- `workspace/`：需求、候选、数据上下文、模板选择、适配、依赖、执行、视觉与数据核查报告。

## 读图与叙事

全部 **12 个研究 SDG、85 个观测 Target** 都保留。上段 40 个、下段 45 个，沿 SDG 边界换行。每列一个 Target，每格左上角为 NSF、右下角为 NSFC。

1. **Share 行**：Target 占该国该 SDG 供给的份额，回答“供给由哪些 Target 承载”。
2. **K01–K06 行**：同一国家、同一 Target 内的条件任务份额，回答“同一 Target 的知识任务组合如何不同”。
3. 深浅随份额线性变化，两国共同使用 0–100% 数值范围。色相代表国家，不代表差值方向。**这不是相关性矩阵。**
4. 白色表示观测为零；灰底短横线表示该国未观测到该 Target，任务组成不可估计。数据表中未观测 Target 的供给份额仍为零，任务份额为缺失，图中统一使用缺失标记以明确证据状态。
5. † 表示至少一国该 Target 的分数项目支持量小于 10；显示全部观测估计，但不把低支持下的强色块解释为稳健差异。缺失国家也属于低支持情形。

正文可继续使用 SDG11 的证据：Target 11.5 的供给份额为 NSF 52.5%、NSFC 20.9%；Target 11.3 为 NSF 7.1%、NSFC 29.4%。这说明 SDG 内部承载结构不同；六行任务组成进一步区分同一 Target 内的知识内容。图中未逐格打印数值，以保留正文可读性。

## 与上一版相比

把 85 条纵向记录转为横向矩阵；两国放入同格，取消两套重复面板、重复气泡大小编码和单独 JSD 图列。全部数据位置保留为 595 个双国单元，即 **170 个 Target 份额位置 + 1,020 个任务份额位置**。主图使用点估计概览；已有 2,000 次项目族 bootstrap 区间、支持量、任务差值和 JSD 保存在配套文件，不重新计算、不据颜色宣称显著性。

## 模板与实现

选用 modelviz `rel_diagonal_split_triangular_heatmap`（`09_REL_005`）。保留同格双三角、多色标和矩阵对齐，把模板原来的下三角矩阵改为两个矩形段，以适应真实的 Target × 指标数据。需求解析、候选召回、数据上下文、最终选择、依赖核查、代码适配、执行及质量服务均实际运行。语义决定由本次 Codex 会话提供给结构化 runnable；未调用或假称另一个外部模型。第一次泛化召回偏向堆叠图，按两国同一单元的“双变量编码”需求细化功能词后重新召回。未修改技能原模板。

配色端点 NSF `#3775BA`、NSFC `#B64342`，与当前 Figure4a 统一配色代码及既有全量数据元信息一致。为表达连续份额，色带由白色线性过渡到对应端点。

## 英文图注

**d, Target carriers and knowledge-task profiles across all observed Targets.** Columns show all 85 Targets observed in at least one country across the 12 study SDGs. In each cell, the upper-left triangle represents NSF and the lower-right triangle NSFC. The Share row gives each Target's fractional share of research supply within its parent SDG and country. Rows K01–K06 give conditional knowledge-task shares within the same Target and country. Color intensity follows a common linear 0–100% scale. White denotes an observed zero; gray triangles with a dash denote an unobserved country–Target profile. Daggers indicate fractional Target support below 10 in at least one country. The display presents point estimates; project-family bootstrap 95% intervals (2,000 resamples), support counts and task-profile JSD are supplied in the accompanying source data and interval figures. Color contrasts alone do not indicate statistically reliable differences.

**Task key.** K01, State measurement and problem diagnosis; K02, Mechanism analysis and causal identification; K03, Scenario simulation and risk prediction; K04, Intervention design and performance optimization; K05, Planning decision support and policy design; K06, Implementation monitoring and impact evaluation.

## 重绘

```powershell
& 'D:\xuexi\canshuhua\anaconda\Anaconda\envs\py311\python.exe' '.\render_figure4d.py'
```

依赖：Python、NumPy、pandas、Matplotlib。输出尺寸固定；不要使用 `bbox_inches='tight'` 改变页面物理尺寸。默认路径相对脚本解析。完整 bootstrap 重算入口仍为上一层 `代码/rebuild_full_figure4d.py --recompute`，并使用上一层的数据快照；本次只重构呈现层。
