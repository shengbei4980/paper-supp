# Figure 5b 多和弦图重构

总图位于 `图/Figure5b_六和弦图_整体.png`；同名 PDF、SVG 为可放大版本。`图/` 还含三类相对位置 × NSF/NSFC 的六张单图，各有 PNG、PDF、SVG。

## 图面解释

- 沿用 Figure 5b 的 `b`、主标题、副标题和 `Project-count stability gate` 表述。
- 六个圆环内部只有 **正式 Target、知识任务 K01–K06、行动阶段 A01–A07**。各面板右上角的 `Goals …` 是该面板入选 SDG 的背景说明，不是和弦节点。
- 每条弦只代表相邻层的汇总连接（Target–K 或 K–A）。弦宽编码分数项目支持量，同一国家沿用 Figure 1a 的蓝色或红色色阶；由淡到深区分该面板内连接权重等级。
- 圆环中知识任务节点同时承接两侧关系，因此其扇区长度包含进入与离开的支持量；不要跨节点层比较扇区长度。六个圆环各自定标，不能凭图上弦宽比较跨面板的绝对支持量；面板上方列出支持量总和。
- 和弦汇总无法沿单条弦重建一条完整的 SDG→Target→K→A 路径。完整的 753 条路径在 `数据/Figure5b_稳定入口完整路径.csv` 中保留。
- 每个圆环最外侧的细环融入行动阶段组成，根据完整路径直接计算。三段依次是 A01–A02（浅）、A03–A04（中）、A05–A07（深）；三组精确百分比在各和弦图左下角的小图例中显示。没有独立的底部阶段图或总图图例。

## 文件

- `代码/绘制Figure5b_六和弦图.py`：可复现绘图代码，使用 `pycirclize`、matplotlib、pandas。
- `数据/Figure5b_目标任务阶段连接权重.csv`：六图中 397 条非零汇总连接。
- `数据/Figure5b_行动阶段分组占比.csv`：六个外环的精确分段数值。
- `数据/Figure5b_Target标签对照.csv`：环上短标签与原始 Target 全称的对照。
- `数据/Figure5b_稳定入口入选SDG.csv`、`数据/Figure5b_稳定入口Target覆盖审计.csv`：原始辅助数据副本。
- `QA/modelviz技术核查.json`：文件有效性、数据守恒、图像可读性核查。
- `modelviz_workflow/`：模板选择、依赖、适配、执行和质量核查过程记录。

## 复现

在装有 `pycirclize`、matplotlib、pandas 的 Python 环境中运行 `代码/绘制Figure5b_六和弦图.py`。本次运行使用 `D:\xuexi\canshuhua\anaconda\Anaconda\envs\py311\python.exe`。
