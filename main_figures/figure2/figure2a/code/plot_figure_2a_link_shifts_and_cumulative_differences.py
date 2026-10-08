"""兼容入口：运行当前单框红蓝版。"""
from pathlib import Path
import runpy
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('plot_figure_2a_single_frame_red_blue.py')), run_name='__main__')
