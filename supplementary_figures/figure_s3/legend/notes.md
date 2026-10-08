# Notes: Figure 1c 图例证据

## Evidence priority
1. 实际导出 SVG：最终颜色、半径、线宽、透明度和可见标签。
2. Gephi 项目：Appearance、Preview、布局和显示参数。
3. 节点与边 CSV：字段值、类别计数和指标范围。
4. 分析代码：稳定性判据和共现强度定义。

## Confirmed facts
- 121 个 Target 节点。
- 803 条无向并集边。
- 节点大小字段为 `pooled_share_pct`，即 NSF 与 NSFC 分数计数 Target 占比的算术平均。
- 边宽字段为 `weight`，即 NSF 与 NSFC 余弦共现强度的算术平均；缺失侧按 0 进入平均。
- 稳定性类别计数：Shared 22、NSF-specific 12、NSFC-specific 9、Other stable 19、Not retained 741。
- 当前导出中 SDG 6、7、9、13 共用灰色 `#C0C0C0`。

## 2026-09-25 更新
- 当前图源为 `颜色休整后` 目录，所有视觉映射以最终 SVG 为准。
- 深蓝 26 条，含 NSF-specific 12 条及 Shared 中 NSF 较强的 14 条。
- 深红 17 条，含 NSFC-specific 9 条及 Shared 中 NSFC 较强的 8 条。
- 浅蓝 8 条、浅红 11 条，为对应机构的 Other stable 连线。
- 背景 741 条，当前 SVG 为 #D1D1D1、opacity=1，与 CSV 预设不同，图例采用 SVG 映射。
- 原有五类统计定义保留在数据摘要中；图例映射表按五个实际视觉分组输出。
- 保留节点颜色、节点大小和线宽说明；检验阈值仍记录于核查文件，不在图例中展开。
- 节点示意圆按实际导出半径比例缩放。
- 自动验证通过，SVG 保留可编辑文字，PNG/TIFF 为 600 dpi，透明版 alpha 完整，源文件哈希未变。
