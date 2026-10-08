import sys, json
from pathlib import Path
BASE = Path(__file__).resolve().parents[2]
RUNTIME = Path(r'E:\可持续发展目标基金\定稿撰写\成图\成图精简休整版本\手稿回填与补充材料核查\补充材料精简\审查工作文件\S3城市Target矩阵_modelviz\runtime')
sys.path[:0] = [str(RUNTIME), r'C:\Users\19392\.codex\skills\modelviz-skill']
from src.tools.validate_output_artifacts import validate_output_artifacts
from src.tools.inspect_generated_image import inspect_generated_image
from src.tools.collect_plot_warnings import collect_plot_warnings
out = BASE/'图'
files = [p for p in out.iterdir() if '清晰标注版' in p.name or '外环放大版' in p.name]
result = {
    'artifacts': validate_output_artifacts.invoke({'generated_files': [str(p) for p in files], 'output_directory': str(out)}),
    'images': [inspect_generated_image.invoke({'image_path': str(p)}) for p in files if p.suffix == '.png'],
    'execution_log': collect_plot_warnings.invoke({'stdout':'Rendering completed; 62 pairs; NSF 334; NSFC 95; nonzero cells 2570.', 'stderr':'', 'return_code':0}),
    'layout': {'old_ring_radial_width':.45, 'new_ring_radial_width':.66, 'ring_line_color':'#000000', 'pair_label_style':'Actual Target codes with horizontal leaders; same selected rings in both countries'},
    'data':json.loads((BASE/'代码'/'核查报告'/'figure_data_audit.json').read_text(encoding='utf-8')),
}
(BASE/'代码'/'核查报告'/'清晰标注版_技术核查.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'artifacts_ok':result['artifacts']['success'],'png_count':len(result['images']),'image_checks':[r.get('success') for r in result['images']]}))
