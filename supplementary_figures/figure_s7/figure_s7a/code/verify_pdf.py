"""Check actual vector export text and render a PDF review image."""
from pathlib import Path
import json
import fitz

ROOT = Path(__file__).resolve().parents[1]
path = ROOT/'图/Figure3_location_supply_lorenz_curves.pdf'
doc = fitz.open(path)
assert len(doc)==1
p = doc[0]
spans = [s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
text = p.get_text()
for token in ['0.683','0.810','21.55%','64.32%','352','126','Equal distribution']:
    assert token in text, token
outside = [s['text'] for s in spans if not p.rect.contains(fitz.Rect(s['bbox']))]
assert not outside, outside
overlaps=[]
for i,a in enumerate(spans):
    for b in spans[i+1:]:
        ra,rb=fitz.Rect(a['bbox']),fitz.Rect(b['bbox'])
        intersection=ra & rb
        if not intersection.is_empty and intersection.get_area()>.15*min(ra.get_area(),rb.get_area()):
            overlaps.append([a['text'],b['text']])
assert not overlaps,overlaps
p.get_pixmap(matrix=fitz.Matrix(3,3),alpha=False).save(ROOT/'图/QA_PDF_render.png')
report={'passed':True,'page_mm':[p.rect.width*25.4/72,p.rect.height*25.4/72], 'text_spans':len(spans),'missing_numeric_labels':[], 'text_outside_page':outside,'overlapping_text':overlaps,'min_font_pt':min(s['size'] for s in spans)}
(ROOT/'数据/PDF_visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
