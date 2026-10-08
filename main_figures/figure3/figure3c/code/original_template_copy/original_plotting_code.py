# =========================================================================================
# ====================================== 1. 环境设置 =======================================
# =========================================================================================
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
plt.rcParams['axes.unicode_minus'] = False
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.unicode_minus'] = False
# =========================================================================================
# ======================================2.颜色库=======================================
# =========================================================================================
COLOR_SCHEMES = {
    1: ["#4B4CB5", "#4FB99F", "#901A34", "#E27D60", "#85DCBA", "#E8A87C"],
    2: ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
    3: ["#003f5c", "#bc5090", "#ffa600", "#2f4b7c", "#665191", "#a05195"],
    4: ["#8da0cb", "#66c2a5", "#fc8d62", "#e78ac3", "#a6d854", "#ffd92f"],
    5: ["#F44336", "#2196F3", "#4CAF50", "#FFEB3B", "#9C27B0", "#FF9800"],
    6: ["#b58900", "#cb4b16", "#268bd2", "#dc322f", "#d33682", "#6c71c4"],
    7: ["#2E7D32", "#1565C0", "#EF6C00", "#D84315", "#4527A0", "#0277BD"],
    8: ["#ff007f", "#00f0ff", "#7000ff", "#ffdd00", "#00ff00", "#ff7f00"],
    9: ["#8B0000", "#D2691E", "#DAA520", "#556B2F", "#008080", "#483D8B"],
    10: ["#006994", "#00BFFF", "#20B2AA", "#3CB371", "#9370DB", "#FF69B4"],
    11: ["#880E4F", "#C2185B", "#4A148C", "#311B92", "#1A237E", "#004D40"],
    12: ["#08306b", "#2171b5", "#6baed6", "#e41a1c", "#4daf4a", "#984ea3"],
    13: ["#5D4037", "#795548", "#8D6E63", "#FF5722", "#CDDC39", "#00BCD4"],
    14: ["#c62828", "#f57c00", "#fbc02d", "#2e7d32", "#0277bd", "#6a1b9a"],
    15: ["#1b5e20", "#388e3c", "#81c784", "#f44336", "#e91e63", "#9c27b0"],
    16: ["#311b92", "#512da8", "#673ab7", "#009688", "#ff9800", "#795548"],
    17: ["#E27D60", "#85DCBA", "#E8A87C", "#C38D9E", "#41B3A3", "#F3B562"],
    18: ["#00a86b", "#d90166", "#007bb8", "#f2a900", "#6b3fa0", "#e84a27"],
    19: ["#2c3e50", "#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"],
    20: ["#000000", "#d55e00", "#009e73", "#cc79a7", "#f0e442", "#56b4e9"],
    21: ["#FF6F61", "#6B5B95", "#88B04B", "#F7CAC9", "#92A8D1", "#955251"],
    22: ["#B565A7", "#009B77", "#DD4124", "#D65076", "#45B8AC", "#EFC050"],
    23: ["#5B5EA6", "#9B2335", "#DFCFBE", "#55B4B0", "#E15D44", "#7FCDCD"],
    24: ["#BC243C", "#C3447A", "#98B4D4", "#FFD662", "#00539C", "#EEA47F"],
    25: ["#D6ED17", "#604C8D", "#F93822", "#FEE715", "#101820", "#00A4CC"],
    26: ["#F2AA4C", "#101820", "#E94B3C", "#2D2926", "#00203F", "#ADEFD1"],
    27: ["#2C5F2D", "#97BC62", "#EEA47F", "#F93822", "#FFD662", "#00539C"],
    28: ["#101820", "#FEE715", "#CBCE91", "#EA738D", "#89ABE3", "#FCF6F5"],
    29: ["#B1624E", "#5CC8D7", "#E7A4A2", "#99B998", "#F3543A", "#FF9D76"],
    30: ["#FCE181", "#9E9A41", "#F36923", "#3B2C35", "#6B8E23", "#CD5C5C"],
    31: ["#E91E63", "#9C27B0", "#3F51B5", "#00BCD4", "#4CAF50", "#FFEB3B"],
    32: ["#FF5722", "#795548", "#607D8B", "#F44336", "#009688", "#FFC107"],
    33: ["#8E44AD", "#2980B9", "#27AE60", "#F39C12", "#D35400", "#C0392B"],
    34: ["#1ABC9C", "#3498DB", "#9B59B6", "#F1C40F", "#E67E22", "#E74C3C"],
    35: ["#2ECC71", "#34495E", "#F39C12", "#D35400", "#8E44AD", "#16A085"],
    36: ["#FF9F43", "#EE5253", "#0ABDE3", "#10AC84", "#5F27CD", "#222F3E"],
    37: ["#FECA57", "#FF6B6B", "#48DBFB", "#1DD1A1", "#5F27CD", "#C8D6E5"],
    38: ["#FF9FF3", "#FECA57", "#FF6B6B", "#48DBFB", "#1DD1A1", "#54A0FF"],
    39: ["#00A8FF", "#9C88FF", "#FBC531", "#4CD137", "#487EB0", "#E84118"],
    40: ["#192A56", "#353B48", "#E1B12C", "#44BD32", "#C23616", "#8C7AE6"],
    41: ["#E55039", "#4A69BD", "#60A3BC", "#78E08F", "#F6B93B", "#E58E26"],
    42: ["#FAD390", "#E55039", "#4A69BD", "#78E08F", "#38ADA9", "#079992"],
    43: ["#55EFC4", "#0984E3", "#6C5CE7", "#FDCB6E", "#E17055", "#D63031"],
    44: ["#00B894", "#0984E3", "#6C5CE7", "#E84393", "#FDCB6E", "#D63031"],
    45: ["#F19066", "#F5CD79", "#546DE5", "#E15F41", "#C44569", "#3DC1D3"],
    46: ["#EA8685", "#3DC1D3", "#546DE5", "#C44569", "#F5CD79", "#303952"],
    47: ["#FC5C65", "#FD9644", "#FED330", "#26DE81", "#2BCBBA", "#45AAF2"],
    48: ["#EB3B5A", "#FA8231", "#F7B731", "#20BF6B", "#0FB9B1", "#2D98DA"],
    49: ["#4B6584", "#A55EEA", "#FC5C65", "#26DE81", "#FED330", "#45AAF2"],
    50: ["#FF9A9E", "#A18CD1", "#84FAB0", "#FBC2EB", "#F6D365", "#FDA085"],
    51: ["#FF0844", "#FFB199", "#29323C", "#485563", "#00C6FF", "#0072FF"],
    52: ["#F43B47", "#453A94", "#0250C5", "#D43F8D", "#009EFD", "#2AF598"],
    53: ["#F83600", "#F9D423", "#B224EF", "#7579FF", "#00C6FF", "#0072FF"],
    54: ["#16A085", "#F39C12", "#2980B9", "#8E44AD", "#2C3E50", "#E74C3C"],
    55: ["#FF4E50", "#F9D423", "#3A1C71", "#D76D77", "#FFAF7B", "#283C86"],
    56: ["#11998E", "#38EF7D", "#C94B4B", "#4B134F", "#FF8008", "#FFC837"],
    57: ["#833AB4", "#FD1D1D", "#FCB045", "#2193B0", "#6DD5ED", "#B92B27"],
    58: ["#00B4DB", "#0083B0", "#CC2B5E", "#753A88", "#EC008C", "#FC6767"],
    59: ["#141E30", "#243B55", "#FF00CC", "#333399", "#00C9FF", "#92FE9D"],
    60: ["#3494E6", "#EC6EAD", "#F09819", "#EDDE5D", "#780206", "#061161"]
}
# =========================================================================================
# ======================================3.绘图函数=======================================
# =========================================================================================
def plot_advanced_forest_chart(df, scheme_id, color_list):
    unique_algos = df['Algo'].unique() #分组
    color_map = {algo: color_list[i % len(color_list)] for i, algo in enumerate(unique_algos)} #映射颜色
    #创建画布
    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    y_positions = np.arange(len(df)) #生成Y轴位置
    #遍历数据
    for i, row in df.iterrows():
        c_color = color_map[row['Algo']] #颜色
        y = y_positions[i] #y
        x = row['SpearmanR'] #x
        #水平线
        ax.hlines(y=y, #y
                  xmin=0, #起点
                  xmax=x, #终点
                  color=c_color, #颜色
                  linewidth=2.5) #线宽
        #底下点
        ax.scatter(x, #x
                   y, #y
                   color=c_color, #颜色
                   s=200, #大小
                   alpha=0.3, #透明度
                   edgecolors='none') #无边框
        #上面点
        ax.scatter(x, #x
                   y, #y
                   color=c_color, #颜色
                   s=80, #大小
                   edgecolors='white', #边框
                   linewidth=0.5) #边框粗细

        if x > 0:
            #文本
            ax.text(-0.02, #x
                    y, #y
                    row['CellType'], #文本
                    ha='right', #水平
                    va='center', #垂直
                    color=c_color, #颜色
                    fontsize=13) #字体大小
            #标记
            ax.text(x + 0.02, #x
                    y, #y
                    row['Sig'],  #文本
                    ha='center', #水平
                    va='center', #垂直
                    color='#D32F2F', #颜色
                    fontsize=13, #字体大小
                    fontweight='bold') #加粗

        else:
            #文本
            ax.text(0.02, #x
                    y, #y
                    row['CellType'], #文本
                    ha='left', #水平
                    va='center', #垂直
                    color=c_color, # 颜色
                    fontsize=13) #字体大小
            #标记
            ax.text(x - 0.02, #x
                    y, #y
                    row['Sig'], #文本
                    ha='center', # 水平
                    va='center', # 垂直
                    color='#1976D2', #颜色
                    fontsize=13, #字体大小
                    fontweight='bold') #加粗

    #x=0辅助线
    ax.axvline(0, #x
               color='black', #颜色
               linewidth=2.5) #线宽

    max_x = df['SpearmanR'].abs().max() #X轴绝对值最大值
    x_pad = max_x * 0.15 #x轴留白
    ax.set_xlim(-max_x - x_pad, max_x + x_pad) #x轴范围

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15, symmetric=True)) #X轴刻度对称和最大数量

    ax.set_ylim(y_positions.min() - 1, y_positions.max() + 1) #y轴范围
    #x轴标题
    ax.set_xlabel('Spearman.R', #文本
                  fontsize=20,  #字体大小
                  fontweight='bold') #加粗

    ax.set_yticks(y_positions) #y轴刻度位置
    ax.set_yticklabels([]) #去掉y轴标注
    #网格线
    ax.grid(True, #开启
            linestyle='--', #虚线
            color='#E0E0E0', #颜色
            alpha=0.7, #透明度
            linewidth=1) #线宽
    ax.set_axisbelow(True) #层

    ax.invert_yaxis() #反转Y轴
    #设置x轴刻度
    ax.tick_params(axis='x', #轴
                   direction='out', # 朝外
                   length=5, #长
                   width=2.5, #宽
                   labelsize=16) #字体大小
    ax.tick_params(axis='y', length=0) #设置y轴刻度
    #遍历边框
    for spine in ax.spines.values():
        spine.set_color('#000000') #颜色
        spine.set_linewidth(2.5) #线宽

    ax.set_title("(a)", loc='left', fontsize=24, fontweight='bold') #子图编号

    legend_elements = [Line2D([0], #占位
                              [0], #占位
                              marker='o', #圆形
                              color='w', #线
                              label=algo, #图例名
                              markerfacecolor=color, #填充色
                              markersize=10) #大小
                       for algo, color in color_map.items()]
    # 设图例内容
    ax.legend(handles=legend_elements, #句柄
              loc='best', #位置
              frameon=False, #边框
              fontsize=16, #字体大小
              handletextpad=0.05) #间距

    plt.tight_layout() #布局
    #保存
    fig.savefig(fr'F:\公众号素材\20260708-棒棒糖图\scheme_{scheme_id}.png', dpi=300, bbox_inches='tight')
    fig.savefig(fr'F:\公众号素材\20260708-棒棒糖图\scheme_{scheme_id}.pdf', format='pdf', bbox_inches='tight')
    fig.savefig(fr'F:\公众号素材\20260708-棒棒糖图\scheme_{scheme_id}.svg', bbox_inches='tight')
    plt.close(fig) #关图
# =========================================================================================
# ======================================4.执行部分=======================================
# =========================================================================================
if __name__ == "__main__":
    df_real = pd.read_excel(r'F:\公众号素材\20260708-棒棒糖图\data.xlsx') #读取数据
    #是否批量绘图
    plot_all = True
    if plot_all:
        for scheme_id in COLOR_SCHEMES.keys():
            selected_hex_colors = COLOR_SCHEMES[scheme_id]
            print('正在绘制并保存方案：', scheme_id)
            plot_advanced_forest_chart(df_real, scheme_id, selected_hex_colors)
    else:
        scheme_id = 1
        selected_hex_colors = COLOR_SCHEMES[scheme_id]
        print('正在绘制并保存方案：', scheme_id)
        plot_advanced_forest_chart(df_real, scheme_id, selected_hex_colors)