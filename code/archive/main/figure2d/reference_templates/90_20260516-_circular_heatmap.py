# =========================================================================================
# ====================================== 1. 环境设置 =======================================
# =========================================================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import os
import matplotlib
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
# =========================================================================================
# ======================================2.颜色库=======================================
# =========================================================================================
COLOR_SCHEMES = {
    1: ['#4A4484', '#666666', '#528258', '#993F3F', '#8166BA', '#45648F', '#D98046', '#4A5B5B'],
    2: ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#7F7F7F'],
    3: ['#332288', '#117733', '#44AA99', '#88CCEE', '#DDCC77', '#CC6677', '#AA4499', '#882255'],
    4: ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF'],
    5: ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
    6: ['#8DD3C7', '#FFFFB3', '#BEBADA', '#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5'],
    7: ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600'],
    8: ['#00429d', '#4771b2', '#73a2c6', '#a5d5d8', '#ffffe0', '#ffbcaf', '#f4777f', '#cf3759'],
    9: ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666'],
    10: ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00'],
    11: ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7'],
    12: ['#5c5c5c', '#838383', '#a9a9a9', '#cfcfcf', '#4a90e2', '#50e3c2', '#b8e986', '#f5a623'],
    13: ['#800000', '#9A6324', '#808000', '#469990', '#000075', '#000000', '#e6194B', '#f58231'],
    14: ['#ffe119', '#bfef45', '#3cb44b', '#42d4f4', '#4363d8', '#911eb4', '#f032e6', '#a9a9a9'],
    15: ['#b71c1c', '#4a148c', '#1a237e', '#004d40', '#827717', '#e65100', '#3e2723', '#263238'],
    16: ['#ff8a80', '#ea80fc', '#8c9eff', '#80d8ff', '#a7ffeb', '#ccff90', '#ffff8d', '#ffd180'],
    17: ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#8ab17d', '#babb74', '#1d3557'],
    18: ['#d73027', '#f46d43', '#fdae61', '#fee090', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4'],
    19: ['#543005', '#8c510a', '#bf812d', '#dfc27d', '#80cdc1', '#35978f', '#01665e', '#003c30'],
    20: ['#40004b', '#762a83', '#9970ab', '#c2a5cf', '#a6dba0', '#5aae61', '#1b7837', '#00441b'],
    21: ['#FF007F', '#7B00FF', '#00F0FF', '#FFF700', '#00FF66', '#FF00FF', '#390099', '#9E0059'],
    22: ['#D8DEE9', '#E5E9F0', '#ECEFF4', '#8FBCBB', '#88C0D0', '#81A1C1', '#5E81AC', '#4C566A'],
    23: ['#4A2E2B', '#6C3B2B', '#A8583B', '#D48446', '#F3B162', '#F7D08A', '#A18262', '#665343'],
    24: ['#F7A1C4', '#FFD3E8', '#A1E3D4', '#70CEB6', '#3B9A84', '#FAD4A0', '#F9815C', '#9A412E'],
    25: ['#3D5A80', '#98C1D9', '#E0FBFC', '#EE6C4D', '#293241', '#DDA15E', '#BC6C25', '#606C38'],
    26: ['#0A192F', '#172A45', '#30475E', '#222831', '#393E46', '#00ADB5', '#EEEEEE', '#F9ED69'],
    27: ['#E76F51', '#F4A261', '#E9C46A', '#2A9D8F', '#264653', '#E63946', '#A8DADC', '#457B9D'],
    28: ['#1E352F', '#3B5844', '#617A55', '#A4B494', '#D2E3C8', '#EFEAD8', '#A6BB8D', '#609966'],
    29: ['#FF6B6B', '#FF8E53', '#FFB236', '#FFD93D', '#6BCB77', '#4D96FF', '#9B5DE5', '#F15BB5'],
    30: ['#03001C', '#301E67', '#5B8FB9', '#B6EADA', '#FF2E63', '#252A34', '#08D9D6', '#EEEEEE'],
    31: ['#432C7A', '#80489C', '#FF8FB1', '#FCE2DB', '#E3DFFD', '#ECE8FF', '#D2DAFF', '#B1B2FF'],
    32: ['#3E2723', '#4E342E', '#5D4037', '#6D4C41', '#795548', '#8D6E63', '#A1887F', '#BCAAA4'],
    33: ['#000000', '#111111', '#CCFF00', '#00FFCC', '#FF00CC', '#6600FF', '#330066', '#FFFF00'],
    34: ['#03045E', '#023E8A', '#0077B6', '#0096C7', '#00B4D8', '#48CAE4', '#90E0EF', '#ADE8F4'],
    35: ['#4C0033', '#790252', '#AF0171', '#E80F88', '#FF78A9', '#FFB3B3', '#FFE3E3', '#52006A'],
    36: ['#556B2F', '#6B8E23', '#8FBC8F', '#BDB76B', '#E6E6FA', '#FFF8DC', '#FFE4B5', '#CD853F'],
    37: ['#0B0C10', '#1F2833', '#C5C6C7', '#66FCF1', '#45A29E', '#1A1A24', '#563D7C', '#6F42c1'],
    38: ['#FF4E50', '#FC913A', '#F9D423', '#EDE574', '#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7'],
    39: ['#006266', '#1B1464', '#5758BB', '#6F1E51', '#ED4C67', '#F79F1F', '#A3CB38', '#1289A7'],
    40: ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#FF9AA2', '#FFB7B2', '#FFC6FF'],
    41: ['#506568', '#7B9095', '#A3B1B6', '#C8D3D5', '#D3C3B1', '#BFA38A', '#A58066', '#7A553F'],
    42: ['#FF1493', '#00BFFF', '#FFD700', '#ADFF2F', '#FF4500', '#8A2BE2', '#00FF7F', '#FF69B4'],
    43: ['#2B3A42', '#3F5765', '#BDD4E7', '#FF530D', '#E82C0C', '#34495E', '#7F8C8D', '#BDC3C7'],
    44: ['#800020', '#C04000', '#FF8000', '#FFC000', '#408080', '#004040', '#804000', '#400040'],
    45: ['#FFCCD5', '#FFB3C1', '#FA8072', '#E0A96D', '#9CC3D5', '#A1C6EA', '#BBD1EA', '#D7E3FC'],
    46: ['#0B2545', '#134074', '#8DA9C4', '#EEF4F8', '#051923', '#003554', '#006494', '#0582CA'],
    47: ['#F26419', '#F6AE2D', '#86BBD8', '#33658A', '#2F4858', '#E76F51', '#F4A261', '#E9C46A'],
    48: ['#FFC6FF', '#BDB2FF', '#9BF6FF', '#CAFFBF', '#FDFFB6', '#FFD166', '#06D6A0', '#118AB2'],
    49: ['#121212', '#1F1F1F', '#292929', '#333333', '#03DAC6', '#BB86FC', '#CF6679', '#3700B3'],
    50: ['#1A365D', '#2A4365', '#2B6CB0', '#4299E1', '#63B3ED', '#90CDF4', '#CBD5E0', '#718096'],
    51: ['#9CAF88', '#C2D3CD', '#E3EBE8', '#F5EBE6', '#E0B0B0', '#C28285', '#8E5053', '#562B2D'],
    52: ['#1C1C1C', '#444444', '#7F7F7F', '#D63031', '#FA8231', '#FD9644', '#FED330', '#20BF6B'],
    53: ['#D4F1F4', '#75E6DA', '#189AB4', '#05445E', '#001F3F', '#3A6073', '#3A7BD5', '#00D2FF'],
    54: ['#FF9F1C', '#FFBF69', '#FFFFFF', '#CBF3F0', '#2EC4B6', '#FF6B6B', '#4ECDC4', '#FFE66D'],
    55: ['#1A0933', '#2E114D', '#4B1C6D', '#722F9C', '#A149FA', '#3B0000', '#660000', '#990000'],
    56: ['#556B2F', '#8FBC8F', '#E9967A', '#F4A460', '#D2B48C', '#F5F5DC', '#FFF8DC', '#A0522D'],
    57: ['#FF71CE', '#01CDFE', '#05FFA1', '#B967FF', '#FFFB96', '#000000', '#240046', '#3C096C'],
    58: ['#22252A', '#343A40', '#495057', '#6C757D', '#ADB5BD', '#CED4DA', '#DEE2E6', '#E9ECEF'],
    59: ['#4A154B', '#611F69', '#A11451', '#E01E5A', '#ECB22E', '#2EB67D', '#36C5F0', '#E57373'],
    60: ['#112233', '#254463', '#4B6584', '#778CA3', '#A5B1C2', '#D1D8E0', '#4B7BEC', '#20BF6B']
}

CATEGORY_COLORS = [
    '#A1CDE3', '#1D70B8', '#AEE296', '#269930',
    '#F79C9D', '#FDB462', '#CAB2D6', '#6A3D9A'
]
# =========================================================================================
# ======================================3.绘图函数=======================================
# =========================================================================================

def plot_advanced_forest_chart(df_real, scheme_id):
    base_colors = COLOR_SCHEMES[scheme_id]  #提取配色方案
    z_scores = df_real['z_scores']  #热图数据
    sig_mask = df_real['sig_mask']  #显著性标记
    sleep_traits = df_real['sleep_traits']  #层名
    num_sleep = len(sleep_traits)  #层数
    num_brain = z_scores.shape[1]  #扇区数
    inner_radius = 5  #最内侧圆环起始半径
    outer_radius = 13  #最外侧圆环结束半径
    rmax = 14  #最大半径范围
    r_edges = np.linspace(inner_radius, outer_radius, num_sleep + 1)  #生成每个圆环的边缘半径边界数组
    r_centers = (r_edges[:-1] + r_edges[1:]) / 2  #每个同心圆环中心线所在的半径位置数组
    theta_edges = np.linspace(0, 1.5 * np.pi, num_brain + 1)  #每个扇区的角度
    theta_centers = (theta_edges[:-1] + theta_edges[1:]) / 2  #每个扇区中心轴线对应的角度
    #创建画布
    fig = plt.figure(figsize=(15, 15))
    #极坐标轴在画布中的相对位置
    ax_rect = [0.15,#左
               0.15,#下
               0.7, #宽
               0.7]  #高
    ax = fig.add_axes(ax_rect, projection='polar')  #添加坐标轴对象

    ax.set_theta_zero_location('N')  #正北
    ax.set_theta_direction(1)  #方向
    ax.set_ylim(0, rmax)  #范围
    #映射分类
    cat_counts = [12, 12, 11, 11, 12, 12, 11, 11]
    cat_indices = np.repeat(np.arange(8), cat_counts)
    theta_width = theta_edges[1] - theta_edges[0]  #单个扇区角度宽度
    #绘制分类层
    ax.bar(theta_centers,  #角度
           height=0.6,  #厚度
           width=theta_width,  #宽度
           bottom=4.2,  #起始半径
           color=[CATEGORY_COLORS[c] for c in cat_indices],  #分配颜色
           edgecolor='white',  #边缘线颜色
           linewidth=0.5)  #边缘线粗细
    #从内到外绘制每一层圆环
    for i in range(num_sleep):
        ring_idx = num_sleep - 1 - i  #计算当前特征对应的层级索引
        c_hex = base_colors[i]  #获取当前环配色
        cmap = mcolors.LinearSegmentedColormap.from_list(f'cmap_{i}',[c_hex, 'white', c_hex])  #构建线性渐变色

        R_ring, Theta_ring = np.meshgrid(r_edges[ring_idx:ring_idx + 2],theta_edges)  #生成当前层圆环的半径边界矩阵与角度边界矩阵
        data = z_scores[i, :].reshape(1, -1).T  #提取当前特征对应数据，变形成一维列向量以匹配网格结构

        ax.pcolormesh(Theta_ring,  #角度
                      R_ring,  #半径
                      data,  #数据
                      cmap=cmap,  #颜色
                      vmin=-5,  #最小值
                      vmax=5,  #最大值
                      edgecolor='white',  #边缘线颜色
                      linewidth=0.5)  #边缘线粗细
        #显著性标记绘制
        for j in range(num_brain):
            if sig_mask[i, j]:
                ax.text(theta_centers[j],  #中心角度
                        r_centers[ring_idx],  #半径
                        '*',  #标记
                        color='white',  #字体颜色
                        ha='center',  #水平
                        va='center',  #垂直
                        fontsize=12,  #大小
                        fontweight='bold')  #加粗
    #获取外圈标注的名称
    brain_labels = df_real.get('brain_labels')
    #遍历开始绘制最外圈文本
    for j in range(num_brain):
        angle_rad = theta_centers[j]  #扇区中心角度弧度
        angle_deg = np.degrees(angle_rad)  #转换角度
        #动态设置文本旋转角度和对齐方式
        display_angle = (angle_deg + 90) % 360
        if 90 < display_angle <= 270:
            rotation = display_angle
            alignment = 'left'
        else:
            rotation = display_angle
            alignment = 'left'
        #添加外圈文本
        ax.text(angle_rad,  #角度
                outer_radius + 0.3,  #半径
                brain_labels[j],  #文本
                rotation=rotation,  #旋转角度
                ha=alignment,  #水平
                va='center',  #垂直
                fontsize=12,  #字体大小
                rotation_mode='anchor')  #文字旋转的基准坐标轴

    ax.set_axis_off()  #去掉自带的坐标轴线、网格线、刻度标签
    #图例文本描述
    legend_labels = [
        "Sleep traits to cortical surface area",
        "Sleep traits to cortical thickness",
        "Sleep traits to subcortical volume",
        "Sleep traits to longitudinal change",
        "Cortical surface area to sleep traits",
        "Cortical thickness to sleep traits",
        "Subcortical volume to sleep traits",
        "Longitudinal change to sleep traits"
    ]
    #构建图例句柄
    patches = [mpatches.Patch(color=CATEGORY_COLORS[i], label=legend_labels[i]) for i in range(8)]
    #创建图例
    legend = ax.legend(handles=patches,  #句柄
                       loc='center',  #位置
                       bbox_to_anchor=(0.5, 0.5),  #坐标
                       title="Exposure and outcome pairs",  #图例标题
                       frameon=False,  #去掉外框
                       fontsize=10,  #字体大小
                       handlelength=1.2,  #色块宽
                       handleheight=1.2)  #颜块高
    legend.get_title().set_fontweight('bold')  #文本加粗
    legend.get_title().set_fontsize(12)  #设置图例标题大小

    center_x = ax_rect[0] + ax_rect[2] / 2  #中心x
    center_y = ax_rect[1] + ax_rect[3] / 2  #中心y
    r_scale = (ax_rect[3] / 2) / rmax  #缩放比例因子

    bar_x = center_x + 0.015  #颜色条起始x
    bar_w = 0.08  #颜色条宽度
    bar_h = 0.011  #颜色条高度
    #遍历绘制颜色条
    for i in range(num_sleep):
        ring_idx = num_sleep - 1 - i  #当前特征对应层级
        r_bottom = r_edges[ring_idx]  #层对应的半径

        y_ring_center = center_y + (r_bottom + 0.5) * r_scale  #当前特征y中心坐标
        bar_y = y_ring_center - bar_h / 2 + 0.002  #颜色条左下角y坐标
        #添加颜色条轴
        ax_leg = fig.add_axes([bar_x, bar_y, bar_w, bar_h])

        cmap = mcolors.LinearSegmentedColormap.from_list(f'leg_cmap_{i}', [base_colors[i], 'white', base_colors[i]])  #创建渐变映射
        gradient = np.linspace(-5, 5, 256).reshape(1, -1)  #生成一个等距数值的行矩阵，用于模拟色条从左到右的连续颜色渐变
        ax_leg.imshow(gradient, aspect='auto', cmap=cmap)  #绘制出颜色条

        ax_leg.set_xticks([0, 128, 255])  #刻度位置
        ax_leg.set_xticklabels(['-5', '0', '5'], fontsize=11)  #刻度标注
        ax_leg.set_yticks([])  #去掉y刻度
        #设置x轴刻度线
        ax_leg.tick_params(axis='x',  # x
                           length=0,  #长
                           pad=2,  #刻度线与标签之间间距
                           direction='in')  #朝内
        #颜色条中心虚线
        ax_leg.axvline(128,  #x
                       color='black',  #颜色
                       linestyle='--',  #样式
                       linewidth=1.2,  #粗细
                       alpha=0.7)  #透明度
        #设置颜色条边框
        for spine in ax_leg.spines.values():
            spine.set_linewidth(1.2)  #粗细
            spine.set_edgecolor('black')  #颜色
        #层和颜色条标题文本
        ax_leg.text(1.15,  #x
                    0.5,  #y
                    sleep_traits[i],  #文本
                    transform=ax_leg.transAxes,  #坐标系
                    va='center',  #垂直
                    ha='left',  #水平
                    fontsize=12)  #文本大小
    #保存
    plt.savefig(fr"F:\公众号素材\20260516-环形热图\scheme_{scheme_id}.png", dpi=300,bbox_inches='tight')
    plt.savefig(fr"F:\公众号素材\20260516-环形热图\scheme_{scheme_id}.pdf",bbox_inches='tight')
    plt.close(fig)  #关闭

# =========================================================================================
# ======================================4.执行部分=======================================
# =========================================================================================
if __name__ == '__main__':
    excel_path = r"F:\公众号素材\20260516-环形热图\data.xlsx"  #原始数据路径
    df = pd.read_excel(excel_path, index_col=0)  #读取
    sleep_traits = ["Insomnia", "Sleep duration", "Long sleep", "Short sleep","Chronotype", "Morningness", "Napping frequency", "Sleepiness"]
    z_scores_list = []  #热图数据
    sig_mask_list = []  #显著性
    #遍历特征名
    for trait in sleep_traits:
        z_col = f"{trait} (Z-score)"  #热图数据对应列名
        sig_col = f"{trait} (Significant)"  #显著性性数据对应列名
        z_scores_list.append(df[z_col].values)  #保存热图数据
        sig_mask_list.append(df[sig_col].values.astype(bool))  #保存显著性性数据，转为布尔格式

    z_scores_array = np.array(z_scores_list)  #转成NumPy矩阵数组
    sig_mask_array = np.array(sig_mask_list)

    brain_labels_list = df.index.tolist()  #提取样本索引，用于外圈文本标注
    #打包
    df_real = {
        'z_scores': z_scores_array,
        'sig_mask': sig_mask_array,
        'sleep_traits': sleep_traits,
        'brain_labels': brain_labels_list
    }
    #设置是否批量绘图
    plot_all = True
    if plot_all:
        for scheme_id in COLOR_SCHEMES.keys():
            selected_hex_colors = COLOR_SCHEMES[scheme_id]
            print('正在绘制并保存方案：', scheme_id)
            plot_advanced_forest_chart(df_real,scheme_id)
    else:
        scheme_id = 1
        selected_hex_colors = COLOR_SCHEMES[scheme_id]
        print('正在绘制并保存方案：', scheme_id)
        plot_advanced_forest_chart(df_real, scheme_id)