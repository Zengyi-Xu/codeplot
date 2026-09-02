# CodePlot — Code-Driven Real-Time Plotting Tool

CodePlot is a local GUI tool based on Python + Tkinter + Matplotlib: write code on the left, see the plot on the right in real time. It is suitable for quick scientific charts, teaching demonstrations, and reproducible data visualization.

## Run

```bash
cd codeplot
pip install matplotlib numpy pillow
python codeplot.py
```

## Core Features

- **Left code editor**: line-numbered, syntax-highlight-aware editing area; supports `Ctrl+R` to run and `Ctrl+S` to save the script.
- **Right real-time rendering**: based on Matplotlib's `FigureCanvasTkAgg`; the chart updates immediately after running the code.
- **Built-in templates**: sine wave, scatter plot, multi-line plot, bar chart, etc.; select from the dropdown to load an example.
- **Gallery mode (v5)**:
  - Each figure is edited independently and fine-tuned;
  - Click "Add to Gallery" to save the current figure to the gallery;
  - The overview arranges all figures in a grid and adds `(a)(b)(c)...` sub-figure labels automatically;
  - Click a gallery thumbnail to reload its code and continue editing;
  - Each figure is saved as SVG (vector) and PNG (display).
- **Compose layout (v5)**: supports multi-section sub-figure scripts + layout composition; one-click generation of publication-ready combined figures.
- **Export**: supports saving scripts, exporting single figures as PNG/SVG, and exporting combined figures as PDF/PNG.

## Package as Windows Executable (with Start Menu shortcut)

```bat
build_exe.bat
```

Build steps:
1. Auto-generate `icon.ico` (using 📊 emoji).
2. Use PyInstaller to produce `dist/CodePlot/CodePlot.exe` (no console window).
3. Run `create_shortcut.ps1` to create a `CodePlot` shortcut in the Start Menu.

After packaging, CodePlot can be launched directly from the Start Menu.

## File Structure

```
codeplot/
├── codeplot.py              # Current main program (v5, gallery layout mode)
├── compose_figure.py        # Composition layout engine
├── compose_settings.json    # Default compose layout settings
├── icon.ico                 # App icon (📊 emoji)
├── make_icon.py             # Icon generation script
├── build_exe.bat            # Windows packaging script
├── create_shortcut.ps1      # Create Start Menu shortcut
├── README.md                # This file
├── DEVLOG.md                # Development log
└── archive/                 # Historical versions
    ├── codeplot_v1.py       # First prototype: left/right split real-time plotting
    ├── codeplot_v2.py       # Added tabs and multi-script management
    ├── codeplot_v3.py       # Added variable panel and template system
    ├── codeplot_v4.py       # Added compose layout and batch export
    └── codeplot_v4_backup.py
```

## Usage Example

After launch, select the "Sine Wave" template and click ▶ Run to see the curve on the right. Modify the code and run again; the chart will update in real time.

## Dependencies

- Python 3.8+
- matplotlib
- numpy
- pillow (optional, for thumbnail display)

## License

MIT
