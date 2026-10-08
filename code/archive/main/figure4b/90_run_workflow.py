"""Modelviz services, with this session's explicit model decisions as structured runnables.
No external LLM is simulated: decisions and visual observations are supplied by Codex.
"""
import json
import sys
import os
from pathlib import Path
import pandas as pd
from langchain_core.runnables import RunnableLambda

ROOT = Path(__file__).resolve().parent
SKILL = Path(r'C:\Users\19392\.codex\skills\modelviz-skill')
sys.path.insert(0, str(SKILL))
W = ROOT / 'workspace'
W.mkdir(exist_ok=True)
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
SOURCE = ROOT.parent / '数据'
INPUT = DATA / 'paired_target_metrics.csv'

def save(name, obj):
    (W / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def runnable(obj):
    return RunnableLambda(lambda _: obj)

def prepare():
    shares = pd.read_csv(SOURCE / 'target_country_shares.csv', dtype={'target':str})
    tasks = pd.read_csv(SOURCE / 'conditional_task_profiles.csv', dtype={'target':str})
    rows = []
    for _, r in shares.iterrows():
        rows.append(dict(sdg=r.sdg, target=r.target, country=r.country, metric='Share', value=r.target_share,
                         low_support=r.low_support, observed=r.observed))
    for _, r in tasks.iterrows():
        rows.append(dict(sdg=r.sdg, target=r.target, country=r.country, metric=r.task, value=r.conditional_share,
                         low_support=r.low_support, observed=r.observed))
    long = pd.DataFrame(rows)
    a = long[long.country=='NSF'].drop(columns='country')
    b = long[long.country=='NSFC'].drop(columns='country')
    paired = a.merge(b, on=['sdg','target','metric'], suffixes=('_nsf','_nsfc'), validate='one_to_one')
    assert len(paired)==595 and paired.target.nunique()==85
    paired.to_csv(INPUT, index=False, encoding='utf-8-sig')
    from src.services.requirement_parser import parse_and_save_requirement
    from src.services.candidate_matching_pipeline import run_candidate_matching_pipeline
    request = '使用modelviz-skill全流程完全重构Figure4d，全量展示85个Target的供给份额和六类知识任务组合，对比NSF与NSFC；简洁直观，正文版面183×110 mm。'
    req = dict(original_request=request, goal='全量类别的双国组成比较：85个Target供给份额与六类任务组合，紧凑矩阵布局',
               functional_keywords=['比较','多变量','双变量编码'], chart_types=[], style_keywords=['科研风','简洁'],
               use_case='论文正文：双变量逐单元比较，183×110 mm',
               negative_requirements=['不删除观测Target','不将未观测当作零','不使用长达85行的竖向排版'],
               explicit_template=False, is_ambiguous=False, clarification_question='')
    r = parse_and_save_requirement(request, runnable(req), vocabulary_path=SKILL/'docs/requirement_vocabulary.yaml', output_path=W/'user_requirement.json')
    print('requirement', str(r)[:200])
    r = run_candidate_matching_pipeline(requirement_path=str(W/'user_requirement.json'), catalog_path=str(SKILL/'docs/template_catalog.yaml'), output_path=str(W/'candidate_templates.json'), top_k=10, min_score=0.01)
    print(json.dumps(r, ensure_ascii=False))

def select_and_render():
    from src.services.final_template_selection_pipeline import run_final_template_selection_pipeline
    from src.services.template_adaptation_pipeline import run_template_adaptation_pipeline
    candidates = json.loads((W/'candidate_templates.json').read_text(encoding='utf-8'))['candidates']
    tid = 'rel_diagonal_split_triangular_heatmap'
    selected = next(x for x in candidates if x['template_id']==tid)
    columns = list(pd.read_csv(INPUT, nrows=1).columns)
    comparisons = []
    for c in candidates:
        chosen = c['template_id']==tid
        comparisons.append(dict(template_id=c['template_id'], suitable=chosen,
            advantages=['同一单元并列两个国家的实际份额；比重复两套85行矩阵节省空间'] if chosen else ['提供类别比较的可视化参照'],
            limitations=['原模板三角外轮廓改为矩形；颜色端点改为Figure1a；无相关性或显著性含义'] if chosen else ['不适合在183×110 mm中逐项保留85个Target和两国六任务组合'],
            data_compatibility='595个成对单元，分别含NSF和NSFC实际份额' if chosen else '部分比较功能可用，需更大改动',
            requirement_compatibility='满足全量和紧凑正文尺寸' if chosen else '空间利用或逐项可比性较差'))
    selection = dict(dataset_summary='85 observed Targets, 12 SDGs, 595 paired cells: one Target-share metric and six conditional task shares.',
        observed_data_features=['Two country values per cell','22 absent country–Target profiles','Fractions in [0,1]','Share and task rows have different denominators'],
        relevant_columns=columns,candidate_comparisons=comparisons,selected_template_id=tid,selected_template_name=selected['template_name'],
        alternative_template_ids=['rel_bar_association_matrix'],selection_reason='Dual triangles compare two countries in each compact cell; all targets fit two horizontal bands.',
        data_support_reason='Paired numerical values and explicit missing/support flags exist for every cell.',
        data_warnings=['No inference from color differences alone. Confidence intervals remain in companion data.'],confidence=.93,needs_clarification=False,clarification_question='')
    r=run_final_template_selection_pipeline(runnable(selection), data_path=str(INPUT),requirement_path=str(W/'user_requirement.json'),candidate_path=str(W/'candidate_templates.json'),output_path=str(W/'final_template_selection.json'),dataset_context_path=str(W/'dataset_context.json'))
    assert r['success'], r
    plan=dict(template_id=tid,template_name=selected['template_name'],plot_goal='85 Target全量，183×110 mm同格双国矩阵',selected_columns=columns,
        column_mappings=[dict(data_column=c,template_role=('column category' if c=='target' else 'metric row' if c=='metric' else 'group' if c=='sdg' else 'value or evidence flag')) for c in columns],
        required_preprocessing=['Retain string Target IDs','Split at SDG10: 40 and 45 columns','Keep missing distinct from zero'],
        required_dependencies=['numpy','pandas','matplotlib'],layout_elements_to_preserve=['Two triangles in each cell','Paired sequential color scales','Matrix alignment'],
        style_elements_to_preserve=['White background','Thin grid','Direct labels'],elements_allowed_to_change=['Rectangular rather than triangular matrix','Figure1a palette','Two horizontal bands','183×110 mm canvas'],
        title_plan='Target carriers and knowledge-task profiles',axis_plan='Targets in columns, Share and K01–K06 in rows',legend_plan='Country triangle key and paired 0–100% shade legend',annotation_plan='Low-support Target dagger; absent triangle dash',output_formats=['png','pdf','svg','tiff'],can_proceed=True)
    result=dict(adapted_code=(ROOT/'render_figure4d.py').read_text(encoding='utf-8'),
        changes_summary=['Transpose and wrap all Targets into two bands','Replace size encoding with same-scale paired color cells'],
        preserved_style_elements=['Split polygons','Matrix coordinates','Dual percentage scales'],changed_elements=['Rectangular layout','User country palette','Reduced typography'],
        data_columns_used=columns,dependencies_used=['numpy','pandas','matplotlib'],additional_dependencies_requested=[],assumptions=['All shares are fractional estimates, not funding amounts.'],warnings=[])
    r=run_template_adaptation_pipeline(runnable(plan),runnable(result),data_path=str(INPUT),final_selection_path=str(W/'final_template_selection.json'),requirement_path=str(W/'user_requirement.json'),dataset_context_path=str(W/'dataset_context.json'),catalog_path=str(SKILL/'docs/template_catalog.yaml'),workspace_dir=str(W),outputs_dir=str(ROOT/'图'),python_executable=sys.executable,auto_install=False,timeout_seconds=120)
    save('adaptation_service_result.json',r)
    print(json.dumps({k:v for k,v in r.items() if k not in ['adaptation_result','adaptation_plan']},ensure_ascii=False)[:4000])
    assert r['success'], r

def quality():
    from src.services.plot_quality_pipeline import run_plot_quality_pipeline
    visual=json.loads((W/'codex_visual_observation.json').read_text(encoding='utf-8'))
    os.chdir(ROOT)
    r=run_plot_quality_pipeline(runnable(visual),runnable({}),script_path=str(W/'adapted_plot.py'),data_path=str(INPUT),output_directory=str(ROOT/'图'),max_repair_attempts=0)
    print(json.dumps(r,ensure_ascii=False))
    assert r['success'],r

if __name__=='__main__':
    os.chdir(SKILL)
    {'prepare':prepare,'render':select_and_render,'quality':quality}[sys.argv[1] if len(sys.argv)>1 else 'prepare']()
