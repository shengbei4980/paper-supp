# Task Plan: Figure 1c 现图精确匹配图例

## Goal
在不修改原始 Gephi 项目和网络图的前提下，依据实际 SVG、Gephi 保存参数、节点表、边表和分析代码，输出可追溯的 Figure 1c 正式英文图例及组合预览。

## Figure Contract
- Core conclusion: 图例准确解释全量 Target 共现网络中的节点身份、节点份额、稳定性类别和共现强度。
- Figure archetype: quantitative legend strip.
- Target output: Nature 风格、英文正式图例，配套中文核查说明。
- Backend: Python only.
- Final size: 180 mm × 66 mm detailed legend strip.
- Evidence hierarchy: 实际导出 SVG > Gephi 项目保存参数 > CSV 字段 > 分析代码定义。
- Image-integrity note: 不修改、重算或覆盖原始网络图。
- Reviewer risk: 四个 SDG 在当前导出中共享灰色，必须显式披露，不能虚构独立颜色。

## Phases
- [x] Phase 1: 建立目录、确认后端和图例契约
- [x] Phase 2: 提取并交叉核对实际视觉映射
- [x] Phase 3: 编写 Python 脚本并生成图、数据与组合预览
- [x] Phase 4: 静态验证、数值复核和最终尺寸视觉 QA
- [x] Phase 5: 完成交付说明

## Key Questions
1. 图例中的颜色、节点尺度和边宽是否逐项匹配实际 SVG？
2. 统计术语是否与分析代码中的公式和稳定性门槛一致？
3. SVG、PDF、TIFF 与 PNG 是否均完整、可读且无裁切？

## Decisions Made
- 使用实际 SVG 作为颜色、节点半径、边宽和可见标签的视觉真值。
- 使用 Gephi 项目和 CSV/分析代码解释这些视觉属性的统计含义。
- SDG 6、7、9、13 按当前导出共同显示为灰色，并在图例中明确说明。
- 输出英文正式图例、透明版、组合预览、映射数据和中文 QA。

## Errors Encountered
- Arial 缺少 Unicode 下标 2：改为稳定的 ASCII `log2` 与 `sqrt(n_a × n_b)`，重新导出后无字体警告。

## Status
**Complete** - 14 项静态规范检查全部通过；映射自测、PNG/TIFF 分辨率、SVG 可编辑文字、透明通道、PDF 300 dpi 实际渲染与组合预览均已复核。
