"""Re-layout verified theme estimates; agency hue and absolute-shift intensity."""
from pathlib import Path
import hashlib
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_hex
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT, QA = [ROOT / name for name in ["数据", "出图", "复核"]]
STEM = "Figure5c_横排散点与主题词_NSF蓝_NSFC红_色带标签"
AGENCIES = ["NSF", "NSFC"]
COLORS = {"NSF": ["#3775BA", "#16365B"], "NSFC": ["#B64342", "#652325"]}
CMAPS = {a: LinearSegmentedColormap.from_list(a, colors, N=1025) for a, colors in COLORS.items()}
NORM = Normalize(0, 8)
W = 183.0
PLOT_X = [10, 98]
TEXT_X = [55, 143]
TEXT_W = 37.0
PLOT_W = 42.0


def main():
    paths = [DATA / "实际研究主题估计_108项.csv", DATA / "研究主题_SDG贡献_1296项.csv"]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    d, contributions = [pd.read_csv(p) for p in paths]
    assert len(d) == 108 and not d.duplicated(["agency", "theme"]).any()
    assert len(contributions) == 1296
    assert np.isfinite(d[["observed_pct", "standardized_pct", "delta_pp"]]).all().all()
    assert np.allclose(d.standardized_pct - d.observed_pct, d.delta_pp)
    assert d.delta_pp.abs().max() <= 8
    sums = contributions.groupby(["agency", "theme"]).contribution_pp.sum()
    assert np.allclose(sums.reindex(d.set_index(["agency", "theme"]).index), d.delta_pp)
    plt.rcParams.update({"font.family": "Arial", "font.size": 6.3,
        "svg.fonttype": "none", "pdf.fonttype": 42, "axes.linewidth": .6})
    fig = plt.figure(figsize=(W/25.4, 100/25.4), dpi=300, facecolor="white")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    selected, labels, records = {}, [], []
    row_heights = np.zeros((2,4))
    max_shift = d.delta_pp.abs().max()
    for i, agency in enumerate(AGENCIES):
        t = d[d.agency.eq(agency)]
        assert len(t) == 54
        assert np.allclose([t.observed_pct.sum(), t.standardized_pct.sum(), t.delta_pp.sum()], [100,100,0])
        parts = []
        for group, sign in enumerate([-1,1]):
            s = t[t.delta_pp * sign > 0].assign(magnitude=lambda v: v.delta_pp.abs())
            s = s.sort_values(["magnitude", "theme"], ascending=[False,True]).head(4)
            parts.append(s)
            for rank, row in enumerate(s.itertuples()):
                fs = 6.2 + 2.0 * (abs(row.delta_pp)/max_shift)**2
                color = CMAPS[agency](NORM(abs(row.delta_pp)))
                text = fig.text(TEXT_X[i]/W, .5, "", ha="left", va="top", fontsize=fs,
                    fontweight="bold" if rank == 0 else "normal", linespacing=1.02, color=color)
                options = []
                for width in range(16, 55):
                    phrase = textwrap.fill(row.full_theme_name, width=width, break_long_words=False, break_on_hyphens=False)
                    text.set_text(phrase)
                    box = text.get_window_extent(renderer)
                    if box.width <= TEXT_W/25.4*fig.dpi:
                        options.append((phrase.count("\n"), -box.width, phrase))
                assert options, row.full_theme_name
                text.set_text(min(options)[2])
                text.set_gid(f"theme_label_{agency}_{row.theme}")
                height = text.get_window_extent(renderer).height*25.4/fig.dpi
                row_heights[group,rank] = max(row_heights[group,rank], height)
                labels.append((i, group, rank, text))
                record = row._asdict()
                record.pop("Index"); record.pop("magnitude")
                record.update(direction="Observed > benchmark" if sign < 0 else "Observed < benchmark",
                    rank_in_direction=rank+1, font_size_pt=fs, color=to_hex(color))
                records.append(record)
        selected[agency] = pd.concat(parts)
    old = pd.read_csv(DATA / "规整词云_16个完整主题标注.csv")
    assert {(r["agency"],r["theme"]) for r in records} == set(zip(old.agency,old.theme))
    group_heights = row_heights.sum(axis=1) + 3*.8 + 3.8
    content_height = float(group_heights.sum() + 3.0)
    H = round(max(content_height, PLOT_W+8) + 30, 2)
    fig.set_size_inches(W/25.4, H/25.4)
    top = H-9
    anchors, heading_y = {}, []
    cursor = top
    for group in range(2):
        heading_y.append(cursor)
        cursor -= 3.8
        for rank in range(4):
            anchors[group,rank] = cursor
            cursor -= row_heights[group,rank] + (.8 if rank < 3 else 0)
        cursor -= 3.0
    for i,group,rank,text in labels:
        text.set_position((TEXT_X[i]/W, anchors[group,rank]/H))
    fig.text(2/W, (H-2)/H, "c", fontsize=9, fontweight="bold", va="top")
    mapping, circles, axes = [], [], []
    for i,agency in enumerate(AGENCIES):
        fig.text((PLOT_X[i]+41)/W, (H-2)/H, agency, ha="center", va="top",
            fontsize=8.5, fontweight="bold", color=COLORS[agency][0])
        for group,heading in enumerate(["Observed > benchmark", "Observed < benchmark"]):
            fig.text(TEXT_X[i]/W, heading_y[group]/H, heading, fontsize=6.2,
                     color="#41464C", va="top", fontweight="bold")
        t = d[d.agency.eq(agency)]
        s = selected[agency]
        keys = set(s.theme)
        y = top - content_height/2 - PLOT_W/2
        ax = fig.add_axes([PLOT_X[i]/W,y/H,PLOT_W/W,PLOT_W/H])
        ax.set_aspect("equal")
        xy = s[["observed_pct", "standardized_pct"]].to_numpy()
        center = (xy.min(axis=0)+xy.max(axis=0))/2
        radius = np.linalg.norm(xy-center,axis=1).max()+.20
        circle = Circle(center,radius,facecolor="#E8E8E8",edgecolor="none",zorder=0)
        circle.set_gid(f"selected_region_{agency}")
        ax.add_patch(circle)
        circles.append(dict(agency=agency,center_x=center[0],center_y=center[1],radius=radius))
        assert np.all(np.linalg.norm(xy-center,axis=1)<radius)
        for row in t.itertuples():
            chosen = row.theme in keys
            color = to_hex(CMAPS[agency](NORM(abs(row.delta_pp)))) if chosen else "#242424"
            point = ax.scatter(row.observed_pct,row.standardized_pct,s=10 if chosen else 4.5,
                c=color,linewidths=0,zorder=3 if chosen else 2)
            point.set_gid(f"full_point_{agency}_{row.theme}")
            mapping.append(dict(agency=agency,theme=row.theme,full_theme_name=row.full_theme_name,
                observed_pct=row.observed_pct,standardized_pct=row.standardized_pct,
                delta_pp=row.delta_pp,selected=chosen,color=color))
        ax.plot([0,16],[0,16],color="#AEB3B8",ls="--",lw=.6,zorder=1)
        ax.set(xlim=(0,16),ylim=(0,16),xticks=[0,4,8,12,16],yticks=[0,4,8,12,16])
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(labelsize=6,length=2,pad=2,width=.5)
        ax.set_xlabel("Observed research share (%)",fontsize=6.2,labelpad=3)
        if i==0:
            ax.set_ylabel("Challenge-standardized share (%)",fontsize=6.2,labelpad=3)
        axes.append(ax)
        cax = fig.add_axes([(PLOT_X[i]+12)/W,9/H,53/W,1.8/H])
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM,cmap=CMAPS[agency]),cax=cax,orientation="horizontal",ticks=[0,4,8])
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=6,length=1.8,pad=1.5,width=.5)
        title = fig.text((PLOT_X[i]+38.5)/W,13.3/H,"Absolute share shift (pp)",
            ha="center",va="center",fontsize=6.2,color="#41464C")
        title.set_gid(f"colorbar_label_{agency}")
        fig.text((PLOT_X[i]+10)/W,9.9/H,agency,ha="right",va="center",fontsize=6.2,color=COLORS[agency][0])
    fig.text(.5,2/H,"Color intensity and label size: |challenge-standardized − observed share| (pp)",
        ha="center",va="center",fontsize=6.2)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    texts=[t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text()]
    boxes=[t.get_window_extent(renderer) for t in texts]
    for t,b in zip(texts,boxes):
        assert b.x0>=-1 and b.y0>=-1 and b.x1<=fig.bbox.width+1 and b.y1<=fig.bbox.height+1, f"Clipped: {t.get_text()}"
    for i,b in enumerate(boxes):
        for j,other in enumerate(boxes[i+1:],i+1):
            assert not b.overlaps(other), f"Overlap: {texts[i].get_text()} / {texts[j].get_text()}"
    for row,(_,_,_,text) in zip(records,labels):
        assert text.get_text().replace("\n"," ")==row["full_theme_name"]
        row.update(label_x_mm=text.get_position()[0]*W,label_y_mm=text.get_position()[1]*H)
        rgb=np.array(matplotlib.colors.to_rgb(row["color"]))
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        contrast=1.05/(linear@[.2126,.7152,.0722]+.05)
        assert contrast>=4.5
        row["text_contrast_ratio"]=float(contrast)
    assert len(mapping)==108 and sum(r["selected"] for r in mapping)==16
    assert hashes=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    pd.DataFrame(records).to_csv(DATA/"横排机构配色_16个完整主题.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(mapping).to_csv(DATA/"横排机构配色_108个散点映射.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(circles).to_csv(DATA/"横排机构配色_灰圈范围.csv",index=False,encoding="utf-8-sig")
    fig.savefig(OUT/f"{STEM}.pdf",dpi=600,facecolor="white")
    fig.savefig(OUT/f"{STEM}.svg",dpi=600,facecolor="white")
    fig.savefig(OUT/f"{STEM}.png",dpi=600,facecolor="white")
    fig.savefig(OUT/f"{STEM}.tiff",dpi=600,facecolor="white",pil_kwargs={"compression":"tiff_lzw"})
    fig.savefig(OUT/f"{STEM}_预览.png",dpi=300,facecolor="white")
    report=dict(size_mm=[W,H],source_sha256=hashes,all_108_estimates_unchanged=True,
        complete_theme_labels=16,selected_points=16,context_points=92,agency_palette=COLORS,
        magnitude_color_scale_pp=[0,8],direction_encoded_by_group_headings=True,
        individual_colorbar_labels="Absolute share shift (pp)",
        selected_names_unchanged=True,gray_circles_are_selection_highlights=True,
        word_positions_are_editorial=True,no_leaders=True,no_word_background_frames=True,
        no_overlap=True,no_clipping=True,minimum_text_contrast=min(r["text_contrast_ratio"] for r in records),
        label_font_size_range=[min(r["font_size_pt"] for r in records),max(r["font_size_pt"] for r in records)])
    (QA/"横排机构配色_画面与数据复核.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    plt.close(fig)

if __name__=="__main__":
    main()
