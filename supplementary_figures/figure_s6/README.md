# Figure 2e：统一画框与 Figure 1a 配色重绘

## 交付内容

- `出图/figure2e_preview.png`：完整画布预览（300 dpi）。
- `出图/Figure2e_知识任务干预残差与行动到达曲线.{png,svg,pdf,tiff}`：400 dpi PNG、矢量 SVG/PDF、600 dpi LZW TIFF。
- `代码/绘制Figure2e_统一画框与Figure1a配色.py`：独立绘图脚本，只读取本目录 `数据` 中的 CSV，不依赖原工程的 `figure_common.py`。
- `代码/提取原始编码全标签.py`：从 NSF 和 NSFC 原始编码结果提取、交叉核对 K/L 全称。
- `数据/`：原图使用的全部 10 份 CSV 副本，另有 1 份经核对的 K01–K06、L01–L09 全称映射表。
- `workflow/`：ModelViz 需求解析、模板召回、真实数据上下文、模板选择、依赖检查、适配计划、执行与质量报告。

## 重绘规则

使用 ModelViz 模板目录中的“分组相关性气泡矩阵”作为左侧矩阵版式参考，沿用原 Figure 2e 的残差估计、行动阶段曲线和含义，不采用模板的相关性估计。左侧 9 × 6 矩阵保持方格；右侧 3 × 2 折线图使用尺寸完全相同的四边完整画框，矩阵与右侧面板组的上下边对齐。主图的任务和干预类型仅显示 K01–K06、L01–L09 编号，底部图例逐一给出原始编码数据中的完整英文名称。采用固定画布导出，以保留所有标签和图例。

配色参数取自 `figure1/figure1a/figure1a_sdg_target_ring.py`：NSF 深蓝 `#003366`、中蓝 `#7F99B2`、浅蓝 `#E4EDF5`；NSFC 深红 `#8B0000`、中红 `#C57F7F`、浅红 `#F6E4E4`；中性底色 `#ECEFF1`。国家数据线和点不透明；bootstrap 区间使用对应浅色与 Figure 1a 的叠加透明度 `0.62`。A05–A07 的背景使用中性底色。

## 复现

在具备 `matplotlib`、`numpy`、`pandas` 的 Python 环境中运行：

```powershell
python 'E:\可持续发展目标基金\定稿撰写\成图\figure2\figure2e\最终新\代码\绘制Figure2e_统一画框与Figure1a配色.py'
```

图件数值来源：`figure2e/知识任务—干预残差与行动到达曲线/数据`。完整标签来源：原始 NSF、NSFC 编码数据的 `primary_knowledge_task_labels_en` 和 `primary_intervention_type_labels_en` 字段；两个机构的 15 个编号映射一致。本次只调整标签呈现与版式；原图 10 份 CSV 的 SHA-256 与原始数据文件完全一致。详细核对见 `workflow/geometry_and_data_audit.json`、`workflow/technical_quality_report.json`、`workflow/visual_quality_report.json`。
