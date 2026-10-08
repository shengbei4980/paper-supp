"""Actual exported PDF page/text validation and visual-review render."""
from pathlib import Path
import csv,json
from collections import Counter
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'数据';Q=D/'图面复核';Q.mkdir(exist_ok=True)
doc=fitz.open(ROOT/'图/Figure3c_固定主要科研承担地的跨目标贡献.pdf')
assert len(doc)==1
page=doc[0];spans=[];outside=[]
for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
        for s in line['spans']:
            box=fitz.Rect(s['bbox']);spans.append((s['text'],box))
            if not page.rect.contains(box):outside.append(s['text'])
assert not outside,outside
overlaps=[]
for i,(a,ra) in enumerate(spans):
    for b,rb in spans[:i]:
        inter=ra & rb
        if inter.width>.2 and inter.height>.2 and inter.get_area()>.5:overlaps.append([a,b])
assert not overlaps,overlaps
text=page.get_text()
for g in [2,3,6,7,9,10,11,12,13,15,16,17]:assert f'SDG {g}\n' in text
assert '18 project families' in text and 'all 12 SDGs' in text
with (D/'Figure3c_点位绘制对应.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
observed=Counter(t.strip() for t,box in spans)
expected=Counter(r['display_value'] for r in rows)
assert all(observed[k]>=v for k,v in expected.items()),(observed,expected)
page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(Q/'PDF实际导出复核.png')
report={'page_count':len(doc),'page_size_points':list(page.rect),'text_spans_outside_page':outside,
        'text_span_overlaps':overlaps,'all_12_goal_labels_present':True,'all_24_numeric_labels_present':True,
        'selectable_text_characters':len(text)}
(Q/'PDF复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
