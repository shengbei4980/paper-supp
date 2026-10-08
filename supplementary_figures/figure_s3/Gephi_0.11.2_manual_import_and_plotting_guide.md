# Figure 1c：Gephi 0.11.2 手动导入与成图操作指南

## 1. 本指南对应的数据

工作目录：

`E:\可持续发展目标基金\定稿撰写\成图\figure1\figure1c\figure1c网络\gephi_import`

建议直接导入：

`figure1c_pooled_union.gexf`

该文件已经过程序校验，数据口径如下：

| 项目 | 数量 |
|---|---:|
| Target 节点 | 121 |
| NSF 与 NSFC 并集边 | 803 |
| 两国共同出现的边 | 301 |
| 仅 NSF 出现的边 | 345 |
| 仅 NSFC 出现的边 | 157 |

网络为无向图。节点代表城市相关 SDG Target；边代表两个 Target 在同一资助项目中的共现关系。边权重 `weight` 为 NSF 与 NSFC 标准化共现强度的合并值，用于全量网络的布局和线宽映射。

> `gephi_nodes.csv` 和 `gephi_edges.csv` 是审计与备用导入文件。正常情况下只需打开 GEXF，不要再分别导入两个 CSV，以免重复生成节点或边。

---

## 2. 启动 Gephi 并导入 GEXF

1. 双击启动：

   `D:\xuexi\共现网络绘制\Gephi-0.11.2\bin\gephi64.exe`

2. 在 Gephi 中选择 **File > Open...**，或按 `Ctrl+O`。

3. 选择：

   `E:\可持续发展目标基金\定稿撰写\成图\figure1\figure1c\figure1c网络\gephi_import\figure1c_pooled_union.gexf`

4. 在导入报告窗口中检查：

   - Graph type：**Undirected**；
   - Nodes：**121**；
   - Edges：**803**；
   - 导入到新的 workspace；
   - 不额外生成自环；
   - 点击 **OK** 或 **Finish** 完成导入。

5. 如果导入报告显示的节点数或边数不是 `121 / 803`，立即取消导入，并检查是否误选了 CSV 或旧版 GEXF。

---

## 3. 在 Data Laboratory 中核查字段

切换至顶部的 **Data Laboratory**。

### 3.1 节点表必须包含的关键字段

| 字段 | 研究含义 | 图中用途 |
|---|---|---|
| `Id` / `Label` | SDG Target 编码，如 11.6 | 节点标签 |
| `target_label_zh` | Target 中文含义 | 数据核查或补充说明 |
| `sdg_number` | 所属 SDG | 节点颜色分组 |
| `pooled_share_pct` | 两国合并样本中的 Target 份额 | 节点大小 |
| `pooled_degree` | 并集网络中的连接数量 | 网络结构审计 |
| `pooled_weighted_degree` | 加权连接强度 | 辅助识别核心 Target |

### 3.2 边表必须包含的关键字段

| 字段 | 研究含义 | 图中用途 |
|---|---|---|
| `weight` | 两国合并标准化共现强度 | 边宽与布局权重 |
| `strength_nsf` | NSF 标准化共现强度 | NSF 网络分析 |
| `strength_nsfc` | NSFC 标准化共现强度 | NSFC 网络分析 |
| `present_nsf` | 该连接是否在 NSF 中出现 | 筛选 NSF 网络 |
| `present_nsfc` | 该连接是否在 NSFC 中出现 | 筛选 NSFC 网络 |
| `presence_class` | Shared nonzero、NSF only 或 NSFC only | 国家出现类别比较 |
| `stability_class` | 置换检验后的稳定性类别 | 默认边颜色层级 |
| `edge_alpha` | 默认边透明度 | 弱化普通边并突出稳定组合 |
| `presence_color` | 国家出现类别的备用颜色 | 切换为国家比较样式 |

点击右下角的节点表和边表标签，确认总数仍为 121 个节点和 803 条边。

---

## 4. 制作正文全量共现网络

正文 Figure 1c 使用全部 121 个 Target 和全部 803 条并集边。主图不删除非稳定边，而是将其显示为浅灰背景骨架，并以较强颜色突出稳定组合。

### 4.1 节点颜色：按 SDG 分类

GEXF 已写入与 Figure 1a 色感协调的低饱和 SDG 色组。导入后若颜色正常，可直接保留。若颜色没有正确显示：

1. 在 **Overview > Appearance > Nodes > Color** 中选择 **Partition**；
2. 选择字段 `sdg_number`；
3. 按下表设置颜色，然后点击 **Apply**。

| SDG | 颜色 |
|---:|---|
| 2 | `#B89B58` |
| 3 | `#6F9870` |
| 6 | `#5B9AAC` |
| 7 | `#C5AA58` |
| 9 | `#C47B61` |
| 10 | `#AD6F88` |
| 11 | `#C38F55` |
| 12 | `#9C8258` |
| 13 | `#5F8068` |
| 15 | `#7FA064` |
| 16 | `#4E7C96` |
| 17 | `#526C83` |

### 4.2 节点大小：映射 Target 议程份额

GEXF 已写入节点大小。若需要在 Gephi 中重新映射：

1. 选择 **Appearance > Nodes > Size > Ranking**；
2. 字段选择 `pooled_share_pct`；
3. 最小值设为 **8**，最大值设为 **28**；
4. 点击 **Apply**。

节点越大，表示该 Target 在两国合并科研资助议程中的相对份额越高。不要使用原始出现次数直接控制节点大小，以免样本规模差异支配视觉结果。

### 4.3 边颜色：突出稳定 Target 组合

GEXF 默认采用稳定性主导的视觉层级。非稳定边仍完整保留，但使用浅灰和较低透明度，稳定组合使用低饱和信号色：

| `stability_class` | 含义 | 颜色 | `edge_alpha` |
|---|---|---|---:|
| Not retained | 未进入稳定组合集合 | 浅冷灰 `#CBD2D8` | 0.16 |
| Shared | 两国共同稳定组合 | 柔和灰紫 `#746A82` | 0.88 |
| NSF-specific | NSF 特有稳定组合 | 低饱和钢蓝 `#607E96` | 0.88 |
| NSFC-specific | NSFC 特有稳定组合 | 低饱和砖红 `#AD7072` | 0.88 |
| Other stable | 其他稳定组合 | 中性灰 `#858B91` | 0.62 |

如果导入后边均为同一颜色：

1. 选择 **Appearance > Edges > Color > Partition**；
2. 字段选择 `stability_class`；
3. 按上表设置颜色并点击 **Apply**；
4. 在 Preview 中降低普通边透明度，使 `Not retained` 保持为背景骨架。

需要切换为“共同／NSF only／NSFC only”的国家出现类别比较时，按 `presence_class` 执行 Partition，并参考字段 `presence_color`：Shared nonzero 为 `#746A82`、NSF only 为 `#7890A3`、NSFC only 为 `#B78484`。这一备用样式不改变默认的稳定性视觉层级。

### 4.4 边宽：映射共现强度

1. 选择 **Appearance > Edges > Size/Weight > Ranking**；
2. 字段选择 `weight`；
3. 将视觉范围先设为 **0.15–3.0**；
4. 点击 **Apply**。

若弱边仍遮挡节点，可把最小边宽降至 `0.05–0.10`；若强连接不突出，可把最大边宽提高至 `3.5–4.0`。线宽只改变显示，不改变原始权重。

---

## 5. 布局：ForceAtlas 2 与防重叠

### 5.1 ForceAtlas 2 推荐起始参数

在 **Overview > Layout** 中选择 **ForceAtlas 2**：

| 参数 | 建议值 |
|---|---:|
| Scaling | 15 |
| Gravity | 1.0 |
| Edge Weight Influence | 1.0 |
| Barnes–Hut Optimization | 开启 |
| Prevent Overlap | 开启 |
| LinLog Mode | 关闭 |
| Dissuade Hubs | 关闭 |
| Stronger Gravity | 关闭 |

点击 **Run**。待网络结构基本稳定、节点不再大幅移动后点击 **Stop**，通常约 10–30 秒。不要让布局无限运行，以免结构被过度拉开。

布局过密时：把 `Scaling` 提高至 20–30。布局过散时：把 `Scaling` 降至 8–12，或把 `Gravity` 提高至 1.5–2.0。参数调整后再次短时运行。

### 5.2 消除局部节点重叠

ForceAtlas 2 停止后，在 **Layout** 中选择 **Noverlap**；若没有 Noverlap，则选择 **Label Adjust**。

1. 运行数秒；
2. 节点和主要标签不再互相覆盖后停止；
3. 使用拖拽工具只微调极少数重叠节点，不要大幅改变整体网络结构。

---

## 6. 标签与 Preview 设置

### 6.1 Overview 中的标签检查

1. 点击图形窗口底部的 **T** 图标显示标签；
2. 标签字段使用节点 `Label`，即 Target 编码；
3. 开启“标签大小随节点大小变化”；
4. 标签仅显示 Target 编码，如 `11.6`，不要在正文图中显示完整中文 Target 名称。

如果 121 个标签全部显示后过于拥挤，正文图可保留核心节点标签，完整标签网络放入补充材料。核心节点可依据 `pooled_share_pct` 或 `pooled_weighted_degree` 选取，而不是人工挑选。

### 6.2 Preview 推荐设置

切换至 **Preview**，点击 **Refresh**，再调整：

| 项目 | 建议设置 |
|---|---|
| Node border | 0.5–0.8 pt，深灰色 |
| Show Labels | 开启 |
| Label font | Arial 或 Source Sans 3 |
| Label color | `#263238` |
| Proportional label size | 开启 |
| Edge color | Original |
| Edge opacity | 30%–55% |
| Edge thickness | 使用原始/缩放后的 weight |
| Curved edges | 关闭；仅在交叉严重时开启 |
| Arrows | 关闭（本网络为无向图） |
| Background | 白色 |

点击 **Refresh** 检查最终效果。主图应同时表达三件事：Target 所属 SDG、Target 的相对议程份额，以及 Target 之间的共现强度与跨国共同性。

---

## 7. 派生 NSF 与 NSFC 单国网络

不要在主 workspace 上直接删除边。先通过 **Workspace > Duplicate** 复制两个工作区，分别命名为 `NSF` 和 `NSFC`。

### 7.1 NSF 网络

1. 进入 `NSF` workspace；
2. 在 **Filters > Attributes > Edge** 中选择 `present_nsf`；
3. 仅保留 `true`；
4. 点击 **Filter**。

预期得到 646 条边：301 条共同边加 345 条 NSF 特有边。边宽改用 `strength_nsf`。

### 7.2 NSFC 网络

1. 进入 `NSFC` workspace；
2. 在 **Filters > Attributes > Edge** 中选择 `present_nsfc`；
3. 仅保留 `true`；
4. 点击 **Filter**。

预期得到 458 条边：301 条共同边加 157 条 NSFC 特有边。边宽改用 `strength_nsfc`。

两张单国图必须使用同一套布局逻辑、节点颜色、节点大小范围和边宽范围，避免视觉尺度不一致造成误读。

---

## 8. 派生单个 SDG 的共现网络

需要输出 SDG 2、3、6、7、9、10、11、12、13、15、16 和 17 的单独网络时：

1. 复制全量 workspace；
2. 在 **Filters > Attributes > Node** 中选择 `sdg_number`；
3. 仅保留目标 SDG 编号；
4. 运行筛选，形成该 SDG 的节点诱导子图；
5. 使用与正文一致的节点颜色、节点大小和边颜色；
6. 对每个子图短时运行 ForceAtlas 2，再运行 Noverlap；
7. 文件名采用 `SDG11_target_cooccurrence.svg` 等统一格式。

单个 SDG 图只显示该目标内部的 Target 连接；跨 SDG 连接只在全量 Figure 1c 中表达。

---

## 9. 稳定 Target 组合的辅助识别

正文主网络保留全部 803 条并集边。若需要核查置换检验识别的稳定组合，可复制一个新的 workspace，再按边字段 `stability_class` 筛选：

- `Shared`：两国均稳定；
- `NSF-specific`：NSF 稳定；
- `NSFC-specific`：NSFC 稳定；
- `Other stable`：其他达到稳定性条件的组合；
- `Not retained`：未进入稳定组合集合。

稳定网络适合放入补充材料或作为正文网络的局部标注依据，不应替代全量共现网络。

---

## 10. 保存 Gephi 项目

完成导入和基础设置后立即选择 **File > Save As...**，保存为：

`E:\可持续发展目标基金\定稿撰写\成图\figure1\figure1c\figure1c网络\gephi_import\figure1c_pooled_layout.gephi`

建议在以下节点再次保存：

1. 完成全量网络布局后；
2. 完成 NSF/NSFC workspace 后；
3. 完成 Preview 投稿样式后。

---

## 11. 导出投稿图

在 **Preview** 中点击 **Export**：

1. 首选导出 **SVG**，用于后续在 Illustrator、Inkscape 或 PowerPoint 中排版；
2. 同时导出 **PDF**，保留矢量结构；
3. 如需 TIFF，先导出高分辨率 PNG，再按期刊要求转换为 600 dpi TIFF；
4. 不建议直接用屏幕截图作为投稿图。

推荐文件名：

- `figure1c_target_cooccurrence_full.svg`
- `figure1c_target_cooccurrence_full.pdf`
- `figure1c_target_cooccurrence_nsf.svg`
- `figure1c_target_cooccurrence_nsfc.svg`

---

## 12. 最终核查清单

- [ ] 导入的是 `figure1c_pooled_union.gexf`；
- [ ] 图类型为 Undirected；
- [ ] 节点数为 121；
- [ ] 全量边数为 803；
- [ ] 节点颜色对应 12 个城市相关 SDG；
- [ ] 节点大小映射 `pooled_share_pct`；
- [ ] 边宽映射 `weight`；
- [ ] 浅灰边形成全量网络骨架，灰紫、钢蓝和砖红突出共同、NSF特有和NSFC特有稳定组合；
- [ ] 正文主图未预先删除非稳定边；
- [ ] NSF 网络为 646 条边；
- [ ] NSFC 网络为 458 条边；
- [ ] 无向图箭头已关闭；
- [ ] 标签无大面积重叠；
- [ ] 已保存 `.gephi` 项目；
- [ ] 已导出 SVG 和 PDF 矢量文件。

## 13. 常见问题

**问题 1：导入后所有节点都是灰色。**  
在 Appearance 中按 `sdg_number` 重新执行 Partition 着色，并按本指南的 SDG 色值设置。

**问题 2：导入后边颜色相同。**  
按 `stability_class` 对边执行 Partition 着色；Preview 中将 Edge color 设为 Original。若要比较国家出现类别，再按 `presence_class` 着色并参考 `presence_color`。

**问题 3：网络看起来像一团毛线。**  
先降低边透明度和最小边宽，再提高 ForceAtlas 2 的 Scaling；不要直接删除大量弱边。正文保持全量数据，必要时仅减少非核心标签。

**问题 4：筛选单国网络后边数不正确。**  
确认筛选的是边字段 `present_nsf` 或 `present_nsfc`，且筛选值为 `true`。不要用 `presence_class = NSF only` 代替 NSF 网络，因为这会错误排除 301 条共同边。

**问题 5：Gephi 运行较慢。**  
121 个节点和 803 条边规模较小，正常情况下应流畅运行。关闭不需要的 Preview 实时刷新，并仅在布局稳定后点击 Refresh。
