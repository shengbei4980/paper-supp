# Figure 1c 现图精确匹配图例 QA

## Overall assessment
**映射已核验。** 图例中的颜色、数量、尺度和统计术语均已从实际导出 SVG、Gephi 保存参数、CSV 与分析代码交叉复核。当前主图有 4 个 SDG 共用灰色，图例已显式披露。

## Source integrity
- 使用 `颜色休整后` 目录的最新 SVG、PNG、Gephi 与 CSV。
- 背景边在当前 SVG 中为 #D1D1D1、opacity=1；与 CSV 预设不同，图例按实际导出显示。
- 统计类别与视觉分组分开保存。深色包含特异边和按强度较高方着色的共同稳定边。
- Target 节点：121（要求 121）。
- 无向边：803（要求 803）。
- SVG 可见标签：110；因 Gephi 避让隐藏：11。
- 隐藏标签：2.1, 6.b, 12.8, 16.6, 16.7, 16.b, 17.2, 17.5, 17.11, 17.15, 17.18。
- 全部边类别合计：803。
- 稳定边合计：62。
- 实际共享灰色的 SDG：SDG 6, SDG 7, SDG 9, SDG 13。

## Calculation spot-checks
- 节点大小字段：`pooled_share_pct = (target_share_pct_nsf + target_share_pct_nsfc) / 2`。
- 节点 SVG 半径：`r = 8.026660477 × share + 44.900000945`；最大残差 6.69e-06。
- 最大节点：Target 13.1，13.081405261% 。
- 边强度：`strength = observed / sqrt(n_a × n_b)`；核对 2012 行，最大绝对误差 0。
- 边宽字段：`weight = (strength_nsf + strength_nsfc) / 2`。
- SVG 边宽：`stroke_width = 89.248144177 × weight + 6.97e-10`；最大残差 1.59e-06。

## Stability definition recovered from analysis code
- 最小观察共现：10。
- BH 校正阈值：q < 0.05。
- 置换次数：10,000；要求 permutation z > 0。
- Bootstrap 次数：2,000；要求 `log2 (O/E)` 95% CI 下限 > 0。
- NSF/NSFC 特异类别还要求两国差异 bootstrap 95% CI 完全位于零的一侧。

## Actual edge-colour classes
- `NSF dark`: #003366, opacity=0.878431, n=26。
- `NSFC dark`: #8B0000, opacity=0.878431, n=17。
- `NSF light`: #7F99B2, opacity=0.619608, n=8。
- `NSFC light`: #C57F7F, opacity=0.619608, n=11。
- `Not retained`: #D1D1D1, opacity=1.000000, n=741。

## Raster outputs
- `Figure1c_legend_exact_white.png`: 4251 × 1559 px, mode=RGBA, 407,969 bytes
- `Figure1c_legend_exact_white.tiff`: 4251 × 1559 px, mode=RGBA, 710,212 bytes
- `Figure1c_legend_exact_transparent.png`: 4251 × 1559 px, mode=RGBA, 327,065 bytes
- `Figure1c_with_exact_legend_preview.png`: 1024 × 1408 px, mode=RGB, 930,597 bytes

## Required caveat
- 当前 SVG 中 SDG 6、7、9、13 共同使用 `#C0C0C0`；读者需借助 Target 编码前缀区分。若将来需要 12 个 SDG 的独立颜色，必须重新导出主网络并同步重建图例。

## Output SHA-256
- `Figure1c_edge_visual_encoding.csv`: `07b1f7c8f20e678f53ea753e4331c7cd0017820cc5b978e608c7df7e81a7c84a`
- `Figure1c_edge_width_reference.csv`: `00f3359ada741f24e5ca7d322def9bb51c6d2864f4893dd33e4657cc6caf012c`
- `Figure1c_exact_mapping_summary.json`: `a43c537788fae1e6a4ab3d92f2996ee8bcd68d54b30dd1e568d98c5f14082338`
- `Figure1c_legend_exact_transparent.pdf`: `8d45f87cf4a235440f8f0a734c97dd9fd74238d3631e646dd391d4846f4c3b70`
- `Figure1c_legend_exact_transparent.png`: `a27784b4e96060bcb83b6193b8cb3413829cc503648593d6d4225ac45d61554d`
- `Figure1c_legend_exact_transparent.svg`: `debb80c7e32a43a16cc22c26d3daf0a1c861d1e751b2dd65da1b7e0363032e48`
- `Figure1c_legend_exact_white.pdf`: `ab788ca45e66fd5fcb4d271633e4af620af5d0cb4fe6fa7291df956a8383e5d4`
- `Figure1c_legend_exact_white.png`: `42a7bcf098d7172cf7e228e995922c4f3b594409f991ebc6ffad5c799609eb93`
- `Figure1c_legend_exact_white.svg`: `00a4eca0ccaf3a165de622de870a0cfd2da315c7f3f703ecf7b1f8986dbc15aa`
- `Figure1c_legend_exact_white.tiff`: `f6755c9e1c9fc0d99b1fb56edc69066d5a699e2cde19b61a4eeb30d95b2e4566`
- `Figure1c_node_size_reference.csv`: `e00028e118ba5fc475f562c5c5a09068ba760d33d215ed582f912e945a989777`
- `Figure1c_node_visual_encoding.csv`: `3c6f6d1cf48252aa59dd51155c379dc7a467670f25c68b9a8f17cd41cb9cf759`
- `Figure1c_with_exact_legend_preview.png`: `438fac18a7ad7f4cbae8c465257c7e1766f744e99c36af51c82899e3d9b52e8e`
