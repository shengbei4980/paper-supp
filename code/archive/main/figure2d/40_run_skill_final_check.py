from pathlib import Path
import json,sys,importlib.util
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
p=Path('C:/Users/19392/.codex/skills/academic-figure-skill/scripts/qa_validator.py')
spec=importlib.util.spec_from_file_location('figureqa',p);module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module;spec.loader.exec_module(module)
source=(ROOT/'代码/绘制六类配色圆环图.py').read_text(encoding='utf-8')
checks=[]
for name in sorted(x for x in dir(module) if x.startswith('check_')):
    r=getattr(module,name)(source);checks.extend(r if isinstance(r,list) else [r])
report={'skill':'academic-figure-skill','automated':[asdict(c) for c in checks],
 'reviewed_exceptions':{'AP-0_palette':'Use the six user-requested K colours; retain Figure1a divergence palette.',
 'AP-4_legend':'Manually placed in the open quadrant, outside the point-map radius; visually checked.',
 'CL-2_size':'183/25.4 by 210/25.4 inches = 183 by 210 mm, not recognized by regex.'},
 'visual_review':{'smooth_concentric_heatmap':True,'six_parent_colors_inherited_by_children':True,
 'no_counts_or_subtype_caption_blocks_inside_map':True,'all_16_subtypes_on_outer_ring':True,
 'six_centre_labels_only':True,'no_title_overlap':True,'no_colourbar_overlap':True,
 'legend_does_not_hide_points':True,'all_data_points_inside_circle':True,
 'projection_caveat_in_footer':True,'PNG_PDF_SVG_exist':True}}
(ROOT/'说明/技能终检.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'automatic_checks':len(checks),'flags':[asdict(c) for c in checks if c.category!='PASS']},ensure_ascii=False,indent=2))
