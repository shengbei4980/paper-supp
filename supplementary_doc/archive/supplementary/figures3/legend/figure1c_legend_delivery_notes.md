# Figure 1c 图例交付说明

## 交付内容
本目录提供与当前 Gephi 网络导出逐项匹配的英文正式图例。原始 `.gephi`、PNG、PDF 与 SVG 未被修改或覆盖。

### 正式图例
- `图/Figure1c_legend_exact_white.svg`：可编辑矢量版。
- `图/Figure1c_legend_exact_white.pdf`：投稿/排版矢量版。
- `图/Figure1c_legend_exact_white.png`：600 dpi 白底版。
- `图/Figure1c_legend_exact_white.tiff`：600 dpi LZW 压缩版。
- `图/Figure1c_legend_exact_transparent.svg/.pdf/.png`：透明背景版。
- `图/Figure1c_with_exact_legend_preview.png`：原网络图加图例的组合预览，不替代原始主图。

### 数据与审计
- `数据/Figure1c_node_visual_encoding.csv`：12 个 SDG 的实际节点色值与数量。
- `数据/Figure1c_edge_visual_encoding.csv`：5 个视觉分组的实际颜色、数量和强度范围。
- `数据/Figure1c_node_size_reference.csv`：节点大小参照值。
- `数据/Figure1c_edge_width_reference.csv`：边宽参照值。
- `数据/Figure1c_exact_mapping_summary.json`：完整机器可读映射与源文件哈希。
- `核查/Figure1c图例_QA.md`：数值、视觉和格式复核报告。

## 图例中的精确定义
- 节点表示 SDG Target，文字为 Target 编码。
- 节点大小是 NSF 与 NSFC 分数计数 Target 占比的算术平均，不是按两国项目量加权的合并占比。
- 边表示同一项目中的无向 Target 共现。
- 边宽是两国余弦共现强度的算术平均。
- 当前主图保留全部 803 条边，并以深浅蓝红色区分更新后的稳定连线分组。深色包含特异边和共同稳定边，共同稳定边按强度较高方着色；浅色表示仅在一方稳定、但未确立国家特异性的连线。

## 当前图面的必要限制
SDG 6、7、9、13 在当前 Gephi 导出中共同使用灰色 `#C0C0C0`。正式图例没有为它们虚构不同颜色，而是说明依靠 Target 编码前缀区分。
