# Figure4d 紧凑满幅修订

## 最新修订：标签外置

最新文件为 `Figure4d_全量Target_紧凑满幅_标签外置`（PDF、SVG、PNG、TIFF）。根据用户后续要求，取消包围文字的总框，左右黑框分别只包围色块矩阵。SDG、Target 编号在各矩阵左侧，Share 与 K01–K06 在顶部框外；组间分隔线也限定在矩阵内部。画布、色块尺寸、全部数据和配色沿用。已检查编号均位于数据框外且无重叠。

以下记录为上一版的尺寸和编码说明；其中“单一黑色外框”已由上述仅包围数据的左右边框替代。

最新输出：`Figure4d_全量Target_单框左右_紧凑满幅`，提供 PDF、SVG、600 dpi PNG/TIFF。

- 固定 183 × 110 mm，单一黑色外框，左 40 个、右 45 个 Target。
- SDG 与 Target 的文字起点距离从 13 mm 压缩至 7.2 mm；释放宽度给数据色块。
- 色块宽度由 6.6 mm 增至 9.85 mm（增加 49.2%），指标列间空白为零，仅以细灰线区分。
- 每格完整拼接为两个等面积三角形：左上 NSF，右下 NSFC。没有内部白色间隙。
- 两侧数据区都占满 86 mm 高度，左行高 2.15 mm、右行高约 1.911 mm。行高仅用于排版，不编码数量；两国比较依据同一单元的颜色深浅。色标仍为共同的线性 0–100%。
- NSF #3775BA、NSFC #B64342；Share 的分母为该国该 SDG，K01–K06 的分母为该国该 Target。
- 85 个 Target、595 个双国单元、1,190 个数据位置全部保留；154 个未观测位置用灰底短横线标明。† 保留低支持含义。

源数据 SHA256 与上一版一致，未重新计算估计。已运行完整性、画布尺寸及编号重叠检查，并检查最终预览。代码为上一级 `render_figure4d_single_frame.py`；数据与完整标签、区间文件仍在上一级 `数据`，区间图仍在上一级 `图`。旧版图片保留。

英文图注中对应的几何说明应替换为：Each cell is split into two equal-area triangles: upper left for NSF and lower right for NSFC. Color intensity represents the share on a common linear 0–100% scale. Row heights differ between the two layout blocks solely to fill the available space and do not encode quantities.
