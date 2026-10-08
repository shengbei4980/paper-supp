# Figure2d 重设计版

当前版本：六类任务各用一种颜色，子级继承父级颜色；中心采用真实编码的二维相似性结构，外圈为平滑同心圆环。

**2026-09-24 修正**：移除 K06.1 的斜线覆盖层，低支持量改为 † 注记；直接读取 Figure1a 的两条完整原始色带；K01–K06 和 L01–L09 的图例全称直接从原始数据生成。最新解释见 `说明/20260924修正与子级簇解读.md`，完整名称见 `数据/K与L完整名称对照.csv`。

## 先看这些文件

- `图/Figure2d_预览.png`：300 dpi 预览。
- `图/Figure2d_六类任务色系与子级结构.png`：600 dpi 正式 PNG。
- 同名 PDF、SVG：矢量版本，183×210 mm。
- `图/布局比较/三个数据布局_知识任务主导.png`：PCA / t-SNE 30 / t-SNE 80 比较。
- `图/布局比较/完整图_H_taskTSNE30.png`：另一套局部布局的完整图。
- `说明/设计重审与参考图对应.md`：手稿作用、设计选择、参数、解释边界和英文图注。
- `说明/最终数据与图形复核.json`：129 项当前复核记录。

## 内容

中心：11,753 个真实项目、8,399 种实际五块编码组合、六种主任务颜色；只标六个必要 K 编码。

外圈：16 个正式知识子级×9 个干预层，144 个单元。135 项差值可估计；K06.1 的九项低支持量比较在扇区标签用 † 注明，K06.3 的九项未定义比较用 × 表示。原 55 个统计标记保留。

颜色类别来自原始编码。中心的局部分支没有固定数量，但不将分支宣称为新增的正式任务类别或算法发现的簇。投影不包含机构/国别特征；国别比较依靠外圈。

## 复现顺序

Python 环境：`D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe`。主要依赖：numpy、pandas、scipy、scikit-learn 1.8.0、matplotlib、Pillow、python-docx。

```powershell
& 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe' './代码/构建编码相似性布局.py'
& 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe' './代码/绘制六类配色圆环图.py'
& 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe' './代码/复核重设计版.py'
```

仅调整样式时可直接运行第二行，已保存投影坐标与输入快照。第一行使用原始编码文件并重新读取手稿；对输入与参数相同的坐标缓存会作哈希检查。最终图默认使用 I_taskTSNE80；如需输出已保存的另一种布局：

```powershell
& 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe' './代码/绘制六类配色圆环图.py' --model H_taskTSNE30 --alternate
```

`构建子级统计.py` 保留了外圈统计的重算流程，本次布局修改不需要重复执行统计。`复核重设计版.py` 会读取原始源文件及父目录已复核的统计作为对照。`执行技能终检.py` 使用本机安装的 academic-figure-skill。

## 目录

- 代码：布局、绘图、统计和复核脚本；用户指定原模板位于 `代码/参考模板/`。
- 数据：项目编码、特征矩阵、各候选坐标、最终点位与颜色、外圈统计与逐单元追溯。
- 图：正式图和布局比较。
- 说明：手稿4.2原文摘录、设计说明、方法参数、来源与复核报告。
