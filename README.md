# CodePlot — 代码驱动的实时画图工具

CodePlot 是一个基于 Python + Tkinter + Matplotlib 的本地 GUI 工具：左侧写代码，右侧实时出图。适合快速绘制科研图表、教学演示图和可复现的数据可视化。

## 运行

```bash
cd codeplot
pip install matplotlib numpy pillow
python codeplot.py
```

## 核心功能

- **左侧代码编辑器**：行号、语法高亮感知的编辑区，支持 `Ctrl+R` 运行、`Ctrl+S` 保存脚本。
- **右侧实时渲染**：基于 Matplotlib 的 `FigureCanvasTkAgg`，代码运行后立即显示图表。
- **内置模板**：正弦波、散点图、多组折线、柱状图等，下拉选择即可加载示例。
- **图集模式（v5）**：
  - 每张图独立编辑、精细调整；
  - 点击「加入组图」把当前图收入图集；
  - 图集总览按网格自动排版，并添加 `(a)(b)(c)...` 子图标签；
  - 点击图集中的缩略图可重新加载代码继续编辑；
  - 每张图同时保存 SVG（矢量）和 PNG（显示）。
- **组合排版（v5）**：支持多段子图脚本 + 排版组合，一键生成论文级组图。
- **导出**：支持保存脚本、导出单图 PNG/SVG、导出组图 PDF/PNG。

## 文件结构

```
codeplot/
├── codeplot.py              # 当前主程序（v5，图集排版模式）
├── README.md                # 本说明
├── DEVLOG.md                # 开发日志
└── archive/                 # 历史版本
    ├── codeplot_v1.py       # 最初原型：左右分栏实时画图
    ├── codeplot_v2.py       # 增加多标签、多脚本管理
    ├── codeplot_v3.py       # 增加变量面板与模板系统
    ├── codeplot_v4.py       # 增加组合排版与批量导出
    ├── codeplot_v4_backup.py
```

## 使用示例

启动后选择「正弦波」模板，点击 ▶ 运行，即可在右侧看到曲线。修改代码后再次运行，图表会实时更新。

## 依赖

- Python 3.8+
- matplotlib
- numpy
- pillow（可选，用于缩略图显示）

## 许可证

MIT
