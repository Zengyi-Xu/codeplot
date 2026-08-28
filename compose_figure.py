#!/usr/bin/env python3
"""
compose_figure.py — 把多张 SVG 子图组合排版成一张总图（纯矢量）

用法:
    python compose_figure.py                     # 默认读取 .codeplot_gallery 图集
    python compose_figure.py a.svg b.svg c.svg   # 或指定 SVG 文件（按给定顺序）

所有排版参数都在下面 CONFIG 区域，直接改值后重新运行即可：
  - 序号: 字体、字号、字重、颜色、位置（四角）、衬底、编号样式
  - 布局: "grid"（网格，子图统一大小）或 "custom"（逐张指定位置和大小）
  - 输出: SVG 矢量图；若安装了 cairosvg 可同时导出 PDF/PNG

原理: 每张子图 SVG 作为嵌套 <svg x y width height viewBox> 放入容器 SVG，
全程矢量、不栅格化；序号在组合时添加，子图文件本身保持干净。
"""

import os
import re
import sys
import json

# ════════════════════════════════════════════════════════════════
# CONFIG — 排版参数（改这里）
# ════════════════════════════════════════════════════════════════

# ── 输出 ──
OUTPUT_SVG = "combined_figure.svg"   # 输出文件名
EXPORT_PDF = False                   # 同时导出 PDF（需要 pip install cairosvg）
EXPORT_PNG = False                   # 同时导出 PNG（需要 cairosvg）
PNG_DPI = 300                        # PNG 分辨率
BACKGROUND = "white"                 # 总图背景色，None 表示透明

# ── 序号 (a)(b)(c) ──
LABEL_FONT_FAMILY = "Arial"          # 序号字体，如 "Arial" / "Times New Roman" / "HONOR Sans"
LABEL_FONT_SIZE = 20                 # 字号 (pt)
LABEL_FONT_WEIGHT = "bold"           # normal / bold
LABEL_COLOR = "black"
LABEL_STYLE = "lower"                # 编号样式: "lower" (a) / "upper" (A) / "number" (1)
LABEL_BRACKETS = True                # True → (a)；False → a
LABEL_POSITION = "top-left"          # top-left / top-right / bottom-left / bottom-right
LABEL_OFFSET_X = 6                   # 距子图边缘的水平距离 (pt)
LABEL_OFFSET_Y = 6                   # 距子图边缘的垂直距离 (pt)
LABEL_BACKGROUND = True              # 序号后加白色衬底（压在复杂图上时更清晰）

# ── 布局方式: "grid" 或 "custom" ──
LAYOUT = "grid"

# grid 布局参数（子图统一大小，等比缩放到格子内居中）
GRID_ROWS = 2
GRID_COLS = 2
PANEL_WIDTH = 420                    # 每个格子的宽 (pt)
PANEL_HEIGHT = 320                   # 每个格子的高 (pt)
H_SPACING = 24                       # 列间距 (pt)
V_SPACING = 24                       # 行间距 (pt)
MARGIN = 20                          # 总图四周边距 (pt)

# custom 布局参数（LAYOUT = "custom" 时使用）
# 每张图一个 dict: x, y 为左上角坐标 (pt)，w, h 为显示尺寸 (pt，等比缩放适配)
# "label" 可覆盖自动序号；设为 None 则该图不加序号
CUSTOM_PANELS = [
    {"x": 20,  "y": 20,  "w": 420, "h": 320},
    {"x": 460, "y": 20,  "w": 420, "h": 320},
    {"x": 20,  "y": 360, "w": 420, "h": 320},
    {"x": 460, "y": 360, "w": 420, "h": 320},
]

# ════════════════════════════════════════════════════════════════
# 以下为组合逻辑，一般不需要改
# ════════════════════════════════════════════════════════════════


def load_svg_entry(path):
    """读取 SVG 文件，返回 {viewBox, aspect, inner}；失败返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    mv = re.search(r'viewBox="([^"]+)"', content)
    if mv:
        nums = [float(v) for v in mv.group(1).replace(",", " ").split()]
        if len(nums) == 4 and nums[2] > 0 and nums[3] > 0:
            vb, vb_w, vb_h = mv.group(1), nums[2], nums[3]
        else:
            return None
    else:
        # 没有 viewBox 时退化为用 width/height 属性估算
        mw = re.search(r'width="([\d.]+)', content)
        mh = re.search(r'height="([\d.]+)', content)
        if not (mw and mh):
            return None
        vb_w, vb_h = float(mw.group(1)), float(mh.group(1))
        vb = f"0 0 {vb_w} {vb_h}"
    try:
        start = content.index(">", content.index("<svg")) + 1
        inner = content[start:content.rindex("</svg>")]
    except ValueError:
        return None
    return {"vb": vb, "aspect": vb_w / vb_h, "inner": inner}


def default_gallery_svgs():
    """按图集索引顺序返回 .codeplot_gallery 中的 SVG 路径"""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".codeplot_gallery")
    idx_path = os.path.join(base, "gallery_index.json")
    paths = []
    if os.path.exists(idx_path):
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                items = json.load(f).get("items", [])
            for it in items:
                p = it.get("svg_path", "")
                if p and os.path.exists(p):
                    paths.append(p)
        except Exception:
            pass
    if not paths and os.path.isdir(base):
        paths = sorted(
            os.path.join(base, f) for f in os.listdir(base)
            if f.lower().endswith(".svg") and f != "composed.svg"
        )
    return paths


def make_label(i):
    if LABEL_STYLE == "upper":
        s = chr(65 + i)
    elif LABEL_STYLE == "number":
        s = str(i + 1)
    else:
        s = chr(97 + i)
    return f"({s})" if LABEL_BRACKETS else s


def label_elements(label, px, py, pw, ph):
    """生成序号的 SVG 元素（可选白色衬底），px,py,pw,ph 为子图显示区域"""
    fs = LABEL_FONT_SIZE
    if LABEL_POSITION.endswith("right"):
        lx = px + pw - LABEL_OFFSET_X
        anchor = "end"
    else:
        lx = px + LABEL_OFFSET_X
        anchor = "start"
    if LABEL_POSITION.startswith("bottom"):
        ly = py + ph - LABEL_OFFSET_Y          # 基线
    else:
        ly = py + LABEL_OFFSET_Y + fs          # 基线

    parts = []
    if LABEL_BACKGROUND:
        est_w = len(label) * fs * 0.62 + 6
        if anchor == "end":
            rx = lx - est_w + 3
        else:
            rx = lx - 3
        if LABEL_POSITION.startswith("bottom"):
            ry = ly - fs - 3
        else:
            ry = ly - fs - 3
        parts.append(
            f'<rect x="{rx:.2f}" y="{ry:.2f}" width="{est_w:.2f}" height="{fs + 6:.2f}" '
            f'fill="white" fill-opacity="0.75"/>'
        )
    parts.append(
        f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{anchor}" '
        f'font-family="{LABEL_FONT_FAMILY}" font-size="{fs}" '
        f'font-weight="{LABEL_FONT_WEIGHT}" fill="{LABEL_COLOR}">{label}</text>'
    )
    return "\n".join(parts)


def compute_layout(n):
    """返回 (panels, total_w, total_h)；panels 为 [{x,y,w,h,label}]"""
    if LAYOUT == "custom":
        if n > len(CUSTOM_PANELS):
            raise SystemExit(
                f"custom 布局只定义了 {len(CUSTOM_PANELS)} 个位置，但有 {n} 张图，"
                f"请在 CUSTOM_PANELS 中补齐")
        panels = []
        for i in range(n):
            p = dict(CUSTOM_PANELS[i])
            p.setdefault("label", make_label(i))
            panels.append(p)
        total_w = max(p["x"] + p["w"] for p in panels) + MARGIN
        total_h = max(p["y"] + p["h"] for p in panels) + MARGIN
        return panels, total_w, total_h

    # grid 布局
    rows, cols = GRID_ROWS, GRID_COLS
    if rows * cols < n:
        raise SystemExit(f"网格 {rows}×{cols} 放不下 {n} 张图，请调整 GRID_ROWS/COLS")
    panels = []
    for i in range(n):
        r, c = divmod(i, cols)
        panels.append({
            "x": MARGIN + c * (PANEL_WIDTH + H_SPACING),
            "y": MARGIN + r * (PANEL_HEIGHT + V_SPACING),
            "w": PANEL_WIDTH,
            "h": PANEL_HEIGHT,
            "label": make_label(i),
        })
    total_w = MARGIN * 2 + cols * PANEL_WIDTH + (cols - 1) * H_SPACING
    total_h = MARGIN * 2 + rows * PANEL_HEIGHT + (rows - 1) * V_SPACING
    return panels, total_w, total_h


def compose(svg_paths, out_path):
    entries = []
    for p in svg_paths:
        e = load_svg_entry(p)
        if e is None:
            print(f"[警告] 无法解析，已跳过: {p}")
        else:
            entries.append(e)
    if not entries:
        raise SystemExit("没有可用的 SVG 子图")

    panels, total_w, total_h = compute_layout(len(entries))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{total_w:.1f}pt" height="{total_h:.1f}pt" '
        f'viewBox="0 0 {total_w:.2f} {total_h:.2f}">',
    ]
    if BACKGROUND:
        parts.append(f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>')

    for e, p in zip(entries, panels):
        # 等比缩放到格子内并居中
        if p["w"] / p["h"] > e["aspect"]:
            dh = p["h"]
            dw = dh * e["aspect"]
        else:
            dw = p["w"]
            dh = dw / e["aspect"]
        ox = p["x"] + (p["w"] - dw) / 2
        oy = p["y"] + (p["h"] - dh) / 2
        parts.append(
            f'<svg x="{ox:.2f}" y="{oy:.2f}" width="{dw:.2f}" height="{dh:.2f}" '
            f'viewBox="{e["vb"]}">{e["inner"]}</svg>'
        )
        if p.get("label"):
            parts.append(label_elements(p["label"], ox, oy, dw, dh))

    parts.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return total_w, total_h


def export_extra(svg_path):
    """可选：用 cairosvg 导出 PDF/PNG"""
    try:
        import cairosvg
    except ImportError:
        print("[提示] 未安装 cairosvg，跳过 PDF/PNG 导出（pip install cairosvg 可开启）")
        return
    base = os.path.splitext(svg_path)[0]
    if EXPORT_PDF:
        cairosvg.svg2pdf(url=svg_path, write_to=base + ".pdf")
        print(f"已导出: {base}.pdf")
    if EXPORT_PNG:
        cairosvg.svg2png(url=svg_path, write_to=base + ".png", dpi=PNG_DPI)
        print(f"已导出: {base}.png")


def main():
    svg_paths = sys.argv[1:] or default_gallery_svgs()
    if not svg_paths:
        raise SystemExit(
            "没有找到子图 SVG。请先运行 codeplot_v5.py 加入组图，"
            "或手动指定: python compose_figure.py a.svg b.svg ...")
    print(f"共 {len(svg_paths)} 张子图 | 布局: {LAYOUT}")
    w, h = compose(svg_paths, OUTPUT_SVG)
    print(f"已生成: {OUTPUT_SVG}  ({w:.0f} × {h:.0f} pt)")
    if EXPORT_PDF or EXPORT_PNG:
        export_extra(OUTPUT_SVG)


if __name__ == "__main__":
    main()
