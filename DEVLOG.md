# CodePlot Development Log

## 2026-07-17 — v1 Prototype

- Built a left/right split interface with Python + Tkinter + Matplotlib.
- Left code editor with line numbers, right `FigureCanvasTkAgg` real-time rendering.
- Supports `Ctrl+R` to run and `Ctrl+S` to save scripts.

## 2026-07-17 — v2 Tabs and File Management

- Added multi-tab support for editing multiple scripts at the same time.
- Added file open/save dialogs.
- Optimized font configuration; defaults to Microsoft YaHei / SimHei.

## 2026-07-17 — v3 Templates and Variable Panel

- Added built-in template system (sine wave, scatter, line, bar chart, etc.).
- Added variable watch panel for debugging array variables in scripts.
- Improved error tips; displays line-number information in the status bar on runtime exceptions.

## 2026-07-20 — v4 Compose Layout and Batch Export

- Introduced the `compose_figure.py` composition engine.
- Supports multi-section sub-figure scripts + compose blocks; one-click generation of `(a)(b)(c)` labeled combined figures.
- Added batch PDF/PNG export and persistent settings panel.

## 2026-07-31 — v5 Gallery Mode

- Core refactor to a "single-figure edit + gallery collection + overview layout" workflow:
  1. Code generates only one figure for fine tuning;
  2. "Add to Gallery" saves the current figure to the gallery and generates SVG and PNG at the same time;
  3. The overview page automatically computes the best grid layout and overlays sub-figure labels.
- Gallery data is stored in the `.codeplot_gallery/` directory; the index is a JSON file.
- Clicking a gallery thumbnail reloads historical code for continued editing.
- Compose layout is preserved and can be invoked via the `# ═══ Compose Layout ═══` block.

## 2026-09-27 — v5.1 Publication Templates

- Added `publication_templates.py` with a new "Publication" template category (7 templates):
  line plot, BER curve (semilog), spectrum/frequency response, zoom inset, dual y-axis,
  heatmap + colorbar, bar + error bars.
- Unified journal style preamble fixes the recurring layout issues:
  - Fixed 3.5 in single-column figure size + explicit font sizes -> text never ends up too small;
  - Constrained layout + inward ticks + frameless legends -> no overlapping components;
  - `svg.fonttype='path'` + `pdf.fonttype=42` -> exported SVG/PDF never lose fonts;
  - Font list falls back from Arial to Microsoft YaHei / SimHei for Chinese labels.
- Every template was rendered headlessly and visually inspected for overlaps/clipping.
- Templates are merged into `BUILTIN_TEMPLATES` at runtime; existing user `templates.json`
  picks them up automatically on next launch.

## Future Improvements

- Add code autocomplete and syntax highlighting.
- Support dark theme.
- Optional DPI, image size, and font embedding on export.
- Add more statistics / machine-learning visualization templates.
