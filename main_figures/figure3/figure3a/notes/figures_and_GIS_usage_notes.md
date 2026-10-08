# Figure3a：美国县域与中国城市科研供给

本版采用用户确认的美国州—县边界层级，并按照最终选择改为县域面填色。中国使用既有地级或等价城市面。出版图不叠加气泡，不再使用Place/CDP全量底图，也不改用CBSA。美国县与中国地级城市属于不同制度下的行政空间，不宣称两者严格等价。

## 文件入口

- 数据/Figure3a_州县底图与科研供给.gpkg：可直接在QGIS、ArcGIS Pro等支持GeoPackage的软件中打开。
- 出图/Figure3a_县域与城市科研供给.pdf：矢量图。
- 同名PNG、TIFF为600dpi，另有SVG和小图预览。
- 代码/重新运行.ps1：使用geogis Conda环境从包内已核验的GIS底图重绘，并运行图件和地名核验。代码/准备GIS数据.py保留供需要从输入源重建底图时单独运行。

## GeoPackage图层

| 图层名 | 内容 | 数量 |
|---|---|---:|
| US_states | 美国州及等价地区边界，定位背景 | 56 |
| US_counties | 美国县及等价地区全量边界，附县域供给 | 3235 |
| CN_provinces | 中国省级背景边界 | 34 |
| CN_cities | 中国城市全量边界，附城市供给 | 370 |
| city_supply_points | 归并校正后的中美城市参考点，不用于本版面填色 | 637 |
| source_city_points | 原653个机构城市键的参考点，Clinton坐标已纠正 | 653 |
| NSF_project_locations | 6207条NSF项目记录、坐标、县归属和供给权重 | 6207 |

所有图层为EPSG:4326。美国主图显示时使用EPSG:5070等积投影。GeoPackage保存经纬度，便于GIS自行设置投影。县级等价地区也包含在US_counties中，不能将全部要素简单称为建制县。

`US_counties.supply_q`是县内项目city_weight的和，`share_pct=supply_q/5000×100`；`project_n`是记录数量，不能与分数化供给混用。`has_supply=0`表示样本没有分配到供给，不等于该县没有科研。中国城市的对应供给字段为`city_supply`，分母5546。

在GIS中以US_counties或CN_cities为面图层，按share_pct设置连续填色；0供给单独设浅灰。美国蓝、中国红，各自范围为0至实际最大份额：美国2.6586666667%，中国21.9798052650%。色带末端显示2.659%和21.980%，内部计算不截断或舍入。颜色采用平方根映射，以保留低份额差异；刻度显示原始百分比。GIS复现可用sqrt(share_pct / 对应国家最大值)驱动0—1的连续色带，并将图例标注换回原始份额。两国相同深浅不代表同一绝对份额。州/省界在上层以细线显示。项目点及城市点仅供交互检查，默认不需叠加。

不要把city_supply_points、source_city_points、NSF_project_locations与县域汇总面再次合并求和；这些图层是同一批供给的不同表达层级。

## 重新聚合与原始数据

美国县域供给从6207条项目记录的源坐标与city_weight重新计算，没有把Place面按面积摊派到县，也没有按城市点的气泡大小推算。La Jolla、Brooklyn等城市名称的归并仍保留在输入校正数据；跨县的大城市不强行归入一个县，项目按其已有坐标分别落县。

Clinton/Hamilton College原坐标错误此前已校正为Hamilton College CDP面内代表点，该点不是精确机构门牌坐标。所有县域匹配均基于现有源坐标，不能等同于逐机构地址重新地理编码。详细源记录在数据/输入中保留。

结果：NSF6207条项目全部落入县域，分数化供给总和5000；352个县或等价单元有供给，Top10县份额21.5472%。中国供给总和5546，126个城市面有供给，Top10城市份额64.3166%。这里的21.5%是县域口径，不是原机构城市名称口径19.1%，也不是Place/town聚合口径19.6%；正文如引用本版，必须使用相应统计单元名称和值。

## 边界与制图要素

美国州县边界来自项目已保存的2025 TIGER州/县全量文件，对应辅助数据/美国州县边界数据中的tl_2025_us_state、tl_2025_us_county。包内保留其此前WGS84转换副本。中国省、市边界沿用既有项目数据。县界在本版既作底图细边界，也作为供给面聚合单元。

中国既有边界存在相邻面的小范围几何重叠，本版按行政代码汇总，不按面积分配，不影响份额；不应直接用该边界计算精确面积密度。两国边界采用统一截面，不表示项目年份的历史边界演变。

只保留两幅主图的比例尺，按WGS84测地距离校准并水平呈现；六幅小图的比例尺均已去除，小图使用各自比例而非主图比例。指北针方向以各自主图的投影图框中心为参考，使用1000米向真北测地线投影计算，不再根据右上角图标摆放位置计算方向；美国约向右偏离竖直0.34°，中国约1.37°。另以PyProj子午线收敛角独立复核方向。其参考点分别约为西经96.57°/北纬38.46°、东经102.62°/北纬36.43°。

本次排版统一两幅主图的高度、基线、指北针和比例尺位置；六幅插图采用同一高度和上下基线，统一标题与边框；县名、市名标注使用细引线和浅底，避免挤占色块。地图保持等比例，不为填满图框拉伸。GIS文件及各供给值未改动，绘图前后SHA256核验一致。

阿拉斯加、夏威夷、波多黎各与美属维尔京群岛和中国南海地区有插图；东北部与长三角为细节放大，不是额外样本。波多黎各与美属维尔京群岛共用插图，但英文标题分别规范写作“Puerto Rico and the U.S. Virgin Islands”。

## Top10标签

标签直接从供给份额降序生成。地图显示排名和县名/城市名，精确份额统一放在下方柱末，避免地图重复数字。美国县名后明确标注County；州名在柱状图中完整写出，不使用州名缩写。每国恰好10个地图标签，并以深色边界突出相应单元。主图各标7个，密集区域的3个放在对应细节小图中，每个单元仅标一次。

美国前10名依次为Los Angeles County, California；New York County, New York；Middlesex County, Massachusetts；Boulder County, Colorado；King County, Washington；Washtenaw County, Michigan；Maricopa County, Arizona；Brazos County, Texas；San Diego County, California；Barnstable County, Massachusetts。东北部小图承载第2、3、10名。Harris County不在前10，已去除旧的Houston示例标签。

中国前10名依次为北京、南京、武汉、上海、广州、西安、兰州、杭州、成都、天津。长三角小图承载第2、4、8名。西安英文标签统一采用原始城市归属表中的“Xi'an”。

完整标签数据在数据/Figure3a_Top10标签对应.csv，含单元ID、排名、完整精度份额、所在视窗和引线目标坐标。标签引线指向对应行政面在当前视窗内的内部代表点。Top10统计口径、各供给值及GIS数据本体均未改变。

## 紧凑排名柱状图与集中份额条

画布从14×9.4英寸调整为14×10英寸，高度增加约6.4%。地图、局部图和色带位于上部，排名柱状图位于下部两列，柱图本体高度1.81英寸，占整图18.1%；含标题、坐标说明和集中份额条的统计区约占四分之一。两列采用相同柱高、列宽、基线及排名顺序。

排名柱按本国供给份额降序，柱长使用未经变换的真实百分比，柱末保留两位小数。美国横轴0—3%，中国0—25%，用于各国内部排序比较，两侧柱长不可直接跨国比较。下方两条100%堆积条使用完全相同的物理长度和0—100%尺度，分别显示美国Top10 21.55%、其余78.45%，中国Top10 64.32%、其余35.68%。独立的Top10文字摘要已替换为份额条，避免重复。

数据/Figure3a_Top10柱状图数据.csv保存实际柱长、完整名称、原始精度份额及坐标轴范围。复核/色带与柱状图参数.json保存实际色带范围、变换、刻度、柱图布局、集中份额及统一尺度。所有值从现有GPKG读取，未修改GIS数据或重新计算聚合边界。

## 英文图注

Subnational distribution of research supply. U.S. counties and county-equivalent areas and Chinese prefecture-level or equivalent units are shaded by their share of each funder's national sample supply. Supply is measured using project-family-conserving fractional project weights. U.S. county totals are aggregated from the coordinates attached to individual project records; all 6,207 records are assigned. Neutral areas have no allocated supply in the study sample. Map colours use square-root normalization over separate national ranges; colour-bar ticks show untransformed percentages. Dark outlines and map ranks identify each country's top ten units. Horizontal bars report their shares on separate linear axes; bottom concentration strips use a common 0–100% scale. Insets use separate geographic scales. County and prefecture-level units are distinct administrative geographies; their concentration shares are descriptive at the stated aggregation levels.

## 目录整理

本“复核规范版本”是上一级 Figure 3a 的独立副本，保留代码、原始输入数据、底图数据、出图、说明和复核结果。上一级图件与历史归档均未修改，便于对照追溯。
