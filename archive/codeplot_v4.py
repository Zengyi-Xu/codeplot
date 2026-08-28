"""
CodePlot v4 — 代码驱动实时画图工具（子图导航增强版）
用法: python codeplot_v4.py

新增功能:
  1. 子图导航 — 多子图自动检测，缩略图导航栏一键切换单图/总览
  2. 图表尺寸控制 — 直接设置 Figure 宽/高（英寸）+ 一键缩放
  3. 快速标注工具 — 箭头/圆圈/文本/矩形/辅助线，点击即插入代码
  4. 实时渲染 — 代码变更后自动延迟刷新，边写边看
  5. 保留 v2/v3 全部模板库功能

模板数据存储: templates.json（同目录）
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")

# ── 配置中文字体 ──
import matplotlib.font_manager as fm
_chinese_font_candidates = [
    'Microsoft YaHei', 'SimHei', 'SimSun', 'STSong',
    'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Source Han Sans SC'
]
_chinese_font_found = None
for _font in _chinese_font_candidates:
    try:
        fm.findfont(_font, fallback_to_default=False)
        _chinese_font_found = _font
        break
    except Exception:
        continue

if _chinese_font_found:
    matplotlib.rcParams['font.sans-serif'] = [_chinese_font_found, 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import traceback
import os
import json
import io

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ════════════════════════════════════════
# 内置模板
# ════════════════════════════════════════

BUILTIN_TEMPLATES = {
    "基础图表": {
        "正弦波": {
            "desc": "绘制正弦曲线，展示最基本的线图用法",
            "code": """# 正弦波
x = np.linspace(0, 4*np.pi, 500)
y = np.sin(x)

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y, color='tab:blue', linewidth=2)
ax.set_title('正弦波', fontsize=14)
ax.set_xlabel('x (rad)')
ax.set_ylabel('sin(x)')
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""
        },
        "正弦+余弦波": {
            "desc": "同图绘制正弦和余弦，包含图例",
            "code": """# 正弦波 + 余弦波
x = np.linspace(0, 4*np.pi, 500)
y1 = np.sin(x)
y2 = np.cos(x)

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y1, label='sin(x)', linewidth=2)
ax.plot(x, y2, label='cos(x)', linewidth=2, linestyle='--')
ax.set_title('正弦波与余弦波', fontsize=14)
ax.set_xlabel('x (rad)')
ax.set_ylabel('y')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""
        },
        "多组折线": {
            "desc": "多组数据折线对比，带不同标记",
            "code": """# 多组折线对比
x = np.arange(0, 10, 0.5)
y1 = np.sin(x) * 2 + 3
y2 = np.cos(x) * 2 + 3
y3 = np.sin(x) * np.cos(x) + 3

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y1, 'o-', label='sin', linewidth=2, markersize=4)
ax.plot(x, y2, 's--', label='cos', linewidth=2, markersize=4)
ax.plot(x, y3, '^:', label='sin*cos', linewidth=2, markersize=4)
ax.set_title('多组折线对比', fontsize=14)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""
        },
        "随机散点图": {
            "desc": "带颜色和大小映射的散点图",
            "code": """# 随机散点图
np.random.seed(42)
x = np.random.randn(200)
y = np.random.randn(200)
colors = np.random.rand(200)
sizes = 100 * np.random.rand(200)

ax = fig.add_subplot(111)
ax.clear()
scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, cmap='viridis')
ax.set_title('随机散点图', fontsize=14)
ax.set_xlabel('x')
ax.set_ylabel('y')
fig.colorbar(scatter, ax=ax, label='颜色值')
fig.tight_layout()
"""
        },
        "分组柱状图": {
            "desc": "两组数据的分组柱状图对比",
            "code": """# 分组柱状图
categories = ['A', 'B', 'C', 'D', 'E']
values1 = [23, 45, 56, 78, 32]
values2 = [15, 30, 45, 60, 25]

x = np.arange(len(categories))
width = 0.35

ax = fig.add_subplot(111)
ax.clear()
ax.bar(x - width/2, values1, width, label='组1', color='tab:blue')
ax.bar(x + width/2, values2, width, label='组2', color='tab:orange')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.set_title('分组柱状图', fontsize=14)
ax.set_ylabel('数值')
ax.legend()
fig.tight_layout()
"""
        },
        "水平柱状图": {
            "desc": "水平方向柱状图，适合类别较多的场景",
            "code": """# 水平柱状图
categories = ['类别1', '类别2', '类别3', '类别4', '类别5']
values = [85, 62, 47, 73, 91]

ax = fig.add_subplot(111)
ax.clear()
colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
ax.barh(categories, values, color=colors)
ax.set_title('水平柱状图', fontsize=14)
ax.set_xlabel('数值')
for i, v in enumerate(values):
    ax.text(v + 1, i, str(v), va='center', fontsize=10)
fig.tight_layout()
"""
        },
        "堆叠面积图": {
            "desc": "多组数据堆叠面积图",
            "code": """# 堆叠面积图
x = np.arange(1, 7)
y1 = np.array([1, 4, 6, 8, 9, 12])
y2 = np.array([2, 3, 5, 7, 10, 11])
y3 = np.array([3, 5, 4, 6, 8, 9])

ax = fig.add_subplot(111)
ax.clear()
ax.stackplot(x, y1, y2, y3, labels=['系列A', '系列B', '系列C'],
             colors=['#ff9999', '#66b3ff', '#99ff99'], alpha=0.8)
ax.set_title('堆叠面积图', fontsize=14)
ax.set_xlabel('时间')
ax.set_ylabel('数值')
ax.legend(loc='upper left')
fig.tight_layout()
"""
        },
        "饼图": {
            "desc": "经典饼图，带百分比标签",
            "code": """# 饼图
labels = ['A', 'B', 'C', 'D', 'E']
sizes = [30, 25, 20, 15, 10]
explode = (0.05, 0, 0, 0, 0)

ax = fig.add_subplot(111)
ax.clear()
ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
       shadow=True, startangle=90, colors=plt.cm.Pastel1.colors)
ax.set_title('饼图', fontsize=14)
fig.tight_layout()
"""
        },
        "环形图": {
            "desc": "中间留空的环形图",
            "code": """# 环形图
labels = ['类别1', '类别2', '类别3', '类别4']
sizes = [35, 30, 20, 15]
colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']

ax = fig.add_subplot(111)
ax.clear()
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                    colors=colors, startangle=90,
                                    wedgeprops=dict(width=0.4, edgecolor='w'))
ax.set_title('环形图', fontsize=14)
fig.tight_layout()
"""
        },
    },
    "统计图表": {
        "直方图+密度": {
            "desc": "数据分布直方图叠加核密度估计",
            "code": """# 直方图 + 密度曲线
np.random.seed(42)
data = np.random.normal(100, 15, 1000)

ax = fig.add_subplot(111)
ax.clear()
n, bins, patches = ax.hist(data, bins=30, density=True, alpha=0.7, color='tab:blue', edgecolor='white')
# 叠加正态分布曲线
mu, sigma = np.mean(data), np.std(data)
x_line = np.linspace(data.min(), data.max(), 100)
ax.plot(x_line, 1/(sigma*np.sqrt(2*np.pi)) * np.exp(-(x_line-mu)**2/(2*sigma**2)),
        'r-', linewidth=2, label='正态拟合')
ax.set_title('直方图与密度曲线', fontsize=14)
ax.set_xlabel('数值')
ax.set_ylabel('密度')
ax.legend()
fig.tight_layout()
"""
        },
        "箱线图": {
            "desc": "多组数据箱线图对比",
            "code": """# 箱线图
np.random.seed(42)
data = [np.random.normal(0, std, 100) for std in range(1, 5)]
labels = ['A', 'B', 'C', 'D']

ax = fig.add_subplot(111)
ax.clear()
bp = ax.boxplot(data, labels=labels, patch_artist=True)
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_title('箱线图', fontsize=14)
ax.set_ylabel('数值')
ax.grid(True, axis='y', alpha=0.3)
fig.tight_layout()
"""
        },
        "小提琴图": {
            "desc": "小提琴图展示数据分布形态",
            "code": """# 小提琴图
np.random.seed(42)
data = [np.random.normal(0, std, 100) for std in range(1, 5)]

ax = fig.add_subplot(111)
ax.clear()
positions = [1, 2, 3, 4]
for i, (d, pos) in enumerate(zip(data, positions)):
    from scipy import stats
    kde = stats.gaussian_kde(d)
    x_range = np.linspace(d.min(), d.max(), 100)
    kde_vals = kde(x_range)
    kde_vals = kde_vals / kde_vals.max() * 0.4
    ax.fill_betweenx(x_range, pos - kde_vals, pos + kde_vals, alpha=0.6, color=plt.cm.Set2(i))
    q1, median, q3 = np.percentile(d, [25, 50, 75])
    ax.plot([pos - 0.05, pos + 0.05], [median, median], 'k-', linewidth=2)
    ax.plot(pos, median, 'wo', markersize=5)

ax.set_xticks(positions)
ax.set_xticklabels(['A', 'B', 'C', 'D'])
ax.set_title('小提琴图', fontsize=14)
ax.set_ylabel('数值')
fig.tight_layout()
"""
        },
        "误差条图": {
            "desc": "带误差条的数据点图",
            "code": """# 误差条图
x = np.arange(1, 6)
y = np.array([2.0, 3.5, 4.1, 5.8, 6.2])
error = np.array([0.3, 0.4, 0.2, 0.5, 0.3])

ax = fig.add_subplot(111)
ax.clear()
ax.errorbar(x, y, yerr=error, fmt='o', capsize=5, capthick=2,
            elinewidth=2, markersize=8, color='tab:blue', ecolor='tab:red')
ax.set_title('误差条图', fontsize=14)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_xticks(x)
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""
        },
        "阶梯图": {
            "desc": "阶梯风格的折线图，适合离散数据",
            "code": """# 阶梯图
x = np.arange(0, 10)
y = np.array([3, 1, 4, 1, 5, 9, 2, 6, 5, 3])

ax = fig.add_subplot(111)
ax.clear()
ax.step(x, y, where='mid', linewidth=2, color='tab:green', marker='o', markersize=6)
ax.set_title('阶梯图', fontsize=14)
ax.set_xlabel('Index')
ax.set_ylabel('Value')
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""
        },
    },
    "科学图表": {
        "三维曲面": {
            "desc": "3D 曲面图，展示二元函数",
            "code": """# 三维曲面图
from mpl_toolkits.mplot3d import Axes3D

X = np.linspace(-5, 5, 50)
Y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(X, Y)
Z = np.sin(np.sqrt(X**2 + Y**2))

ax = fig.add_subplot(111, projection='3d')
ax.clear()
surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9, edgecolor='none')
ax.set_title('三维曲面: z = sin(√(x²+y²))', fontsize=14)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
fig.tight_layout()
"""
        },
        "等高线图": {
            "desc": "等高线填充图，适合地形/势能面",
            "code": """# 等高线图
x = np.linspace(-3, 3, 100)
y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = np.exp(-(X**2 + Y**2))

ax = fig.add_subplot(111)
ax.clear()
contourf = ax.contourf(X, Y, Z, levels=20, cmap='RdYlBu_r')
contour = ax.contour(X, Y, Z, levels=10, colors='black', linewidths=0.5)
ax.clabel(contour, inline=True, fontsize=8)
ax.set_title('等高线图: z = exp(-(x²+y²))', fontsize=14)
ax.set_xlabel('X')
ax.set_ylabel('Y')
fig.colorbar(contourf, ax=ax, label='Z 值')
fig.tight_layout()
"""
        },
        "热力图": {
            "desc": "矩阵热力图，展示相关性或数据强度",
            "code": """# 热力图
np.random.seed(42)
data = np.random.rand(10, 10)
row_labels = [f'R{i}' for i in range(1, 11)]
col_labels = [f'C{i}' for i in range(1, 11)]

ax = fig.add_subplot(111)
ax.clear()
im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
ax.set_xticks(np.arange(len(col_labels)))
ax.set_yticks(np.arange(len(row_labels)))
ax.set_xticklabels(col_labels)
ax.set_yticklabels(row_labels)
for i in range(10):
    for j in range(10):
        text = ax.text(j, i, f'{data[i, j]:.2f}',
                       ha="center", va="center", color="black", fontsize=8)
ax.set_title('热力图', fontsize=14)
fig.colorbar(im, ax=ax, label='强度')
fig.tight_layout()
"""
        },
        "矢量场图": {
            "desc": "箭头矢量场，展示方向与大小",
            "code": """# 矢量场图 (quiver)
X, Y = np.meshgrid(np.arange(0, 2*np.pi, 0.2), np.arange(0, 2*np.pi, 0.2))
U = np.cos(X)
V = np.sin(Y)

ax = fig.add_subplot(111)
ax.clear()
ax.quiver(X, Y, U, V, np.sqrt(U**2 + V**2), cmap='plasma', scale=15)
ax.set_title('矢量场图', fontsize=14)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_aspect('equal')
fig.tight_layout()
"""
        },
        "极坐标图": {
            "desc": "极坐标下的玫瑰线",
            "code": """# 极坐标图
theta = np.linspace(0, 2*np.pi, 1000)
r = 2 * np.sin(4 * theta)

ax = fig.add_subplot(111, projection='polar')
ax.clear()
ax.plot(theta, r, linewidth=2, color='tab:purple')
ax.fill(theta, r, alpha=0.3, color='tab:purple')
ax.set_title('极坐标玫瑰线: r = 2sin(4θ)', fontsize=14, pad=20)
fig.tight_layout()
"""
        },
    },
    "高级功能": {
        "双Y轴图": {
            "desc": "共享X轴的双Y轴图，适合不同量纲数据",
            "code": """# 双Y轴图
x = np.arange(1, 11)
y1 = np.array([20, 25, 30, 35, 40, 45, 50, 55, 60, 65])
y2 = np.array([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])

ax1 = fig.add_subplot(111)
ax1.clear()
color1 = 'tab:blue'
ax1.set_xlabel('时间 (月)', fontsize=12)
ax1.set_ylabel('温度 (°C)', color=color1, fontsize=12)
ax1.plot(x, y1, color=color1, linewidth=2, marker='o', label='温度')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('销售额 (万元)', color=color2, fontsize=12)
ax2.plot(x, y2, color=color2, linewidth=2, marker='s', linestyle='--', label='销售额')
ax2.tick_params(axis='y', labelcolor=color2)

ax1.set_title('温度与销售额双Y轴图', fontsize=14)
fig.tight_layout()
"""
        },
        "子图布局": {
            "desc": "2×2 子图网格布局示例",
            "code": """# 2x2 子图布局
fig.clf()

# 子图1: 线图
ax1 = fig.add_subplot(2, 2, 1)
x = np.linspace(0, 10, 100)
ax1.plot(x, np.sin(x), color='tab:blue')
ax1.set_title('正弦波')
ax1.grid(True, alpha=0.3)

# 子图2: 散点
ax2 = fig.add_subplot(2, 2, 2)
np.random.seed(0)
ax2.scatter(np.random.rand(50), np.random.rand(50), alpha=0.6, c='tab:orange')
ax2.set_title('散点图')
ax2.grid(True, alpha=0.3)

# 子图3: 柱状图
ax3 = fig.add_subplot(2, 2, 3)
ax3.bar(['A', 'B', 'C', 'D'], [3, 7, 2, 5], color='tab:green')
ax3.set_title('柱状图')
ax3.grid(True, axis='y', alpha=0.3)

# 子图4: 直方图
ax4 = fig.add_subplot(2, 2, 4)
ax4.hist(np.random.randn(1000), bins=20, color='tab:red', alpha=0.7, edgecolor='white')
ax4.set_title('直方图')
ax4.grid(True, axis='y', alpha=0.3)

fig.suptitle('2x2 子图布局示例', fontsize=16, y=1.02)
fig.tight_layout()
"""
        },
        "对数坐标图": {
            "desc": "双对数坐标下的幂律关系",
            "code": """# 对数坐标图
x = np.logspace(0, 3, 100)
y1 = x**0.5
y2 = x
y3 = x**2

ax = fig.add_subplot(111)
ax.clear()
ax.loglog(x, y1, label='y = x^0.5', linewidth=2)
ax.loglog(x, y2, label='y = x', linewidth=2)
ax.loglog(x, y3, label='y = x^2', linewidth=2)
ax.set_title('双对数坐标图', fontsize=14)
ax.set_xlabel('X (对数)')
ax.set_ylabel('Y (对数)')
ax.legend()
ax.grid(True, which='both', linestyle='--', alpha=0.5)
fig.tight_layout()
"""
        },
        "科学论文样式": {
            "desc": "符合学术论文发表要求的图表样式",
            "code": """# 科学论文样式
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 150,
})

x = np.linspace(0, 10, 200)
y_exp = np.exp(-x/3) * np.sin(2*x)
y_theory = np.exp(-x/3)

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y_exp, 'o', markersize=3, label='实验数据', color='tab:blue', alpha=0.8)
ax.plot(x, y_theory, '-', linewidth=2, label='理论模型', color='tab:red')
ax.fill_between(x, -y_theory, y_theory, alpha=0.1, color='tab:red')
ax.set_title('阻尼振荡: 实验与理论对比', fontsize=14)
ax.set_xlabel('时间 (s)')
ax.set_ylabel('振幅')
ax.legend(frameon=True, fancybox=False, edgecolor='black')
ax.grid(True, alpha=0.3, linestyle='--')
fig.tight_layout()
"""
        },
    },
}


# ════════════════════════════════════════
# 模板管理器
# ════════════════════════════════════════

class TemplateManager:
    def __init__(self, filepath=None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.filepath = os.path.join(base_dir, "templates.json")
        else:
            self.filepath = filepath
        self.templates = self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["builtin"] = self._merge_builtin(data.get("builtin", {}))
                return data
            except Exception:
                pass
        data = {"builtin": dict(BUILTIN_TEMPLATES), "user": {}}
        self._save(data)
        return data

    def _merge_builtin(self, existing):
        merged = {}
        for category, items in BUILTIN_TEMPLATES.items():
            merged[category] = {}
            for name, tmpl in items.items():
                if category in existing and name in existing[category]:
                    existing_code = existing[category][name].get("code", "")
                    if existing_code == tmpl["code"]:
                        merged[category][name] = existing[category][name]
                    else:
                        merged[category][name] = existing[category][name]
                else:
                    merged[category][name] = dict(tmpl)
        return merged

    def _save(self, data=None):
        if data is None:
            data = self.templates
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_builtin(self):
        return self.templates.get("builtin", {})

    def get_user(self):
        return self.templates.get("user", {})

    def add_user_template(self, category, name, desc, code):
        if category not in self.templates["user"]:
            self.templates["user"][category] = {}
        self.templates["user"][category][name] = {"desc": desc, "code": code}
        self._save()

    def delete_user_template(self, category, name):
        user = self.templates.get("user", {})
        if category in user and name in user[category]:
            del user[category][name]
            if not user[category]:
                del user[category]
            self._save()
            return True
        return False

    def get_template_code(self, source, category, name):
        section = self.templates.get(source, {})
        cat = section.get(category, {})
        tmpl = cat.get(name, {})
        return tmpl.get("code", "")

    def get_template_info(self, source, category, name):
        section = self.templates.get(source, {})
        cat = section.get(category, {})
        return cat.get(name, {})

    def export_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    def import_from_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            imported = json.load(f)
        imported_user = imported.get("user", {})
        for cat, items in imported_user.items():
            if cat not in self.templates["user"]:
                self.templates["user"][cat] = {}
            for name, tmpl in items.items():
                self.templates["user"][cat][name] = tmpl
        self._save()
        return True


# ════════════════════════════════════════
# 行号画布
# ════════════════════════════════════════

class LineNumberCanvas(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.config(width=40, bg="#f0f0f0", highlightthickness=0)
        for ev in ("<Configure>", "<KeyRelease>", "<ButtonRelease>", "<MouseWheel>"):
            text_widget.bind(ev, lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        index = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(index)
            if dline is None:
                break
            y = dline[1]
            line_num = str(int(float(index)))
            self.create_text(35, y, anchor="ne", text=line_num,
                             font=("Consolas", 10), fill="#555555")
            index = self.text_widget.index(f"{index}+1line")


# ════════════════════════════════════════
# 主应用 v4
# ════════════════════════════════════════

class CodePlotAppV4:
    def __init__(self, root):
        self.root = root
        self.root.title("CodePlot v4 — 代码驱动实时画图")
        self.root.geometry("1650x1050")
        self.root.minsize(1150, 750)
        self.script_path = None
        self.tmpl_mgr = TemplateManager()

        # 视图模式
        self.view_mode = "overview"        # "overview" | "single"
        self.current_single_index = None   # 当前单图模式的子图索引
        self.thumbnail_photos = []         # 保持 PhotoImage 引用
        self._live_after_id = None         # 实时渲染 debounce

        self._build_ui()
        self._bind_shortcuts()
        self._load_default_template()

    # ────────────────── UI 构建 ──────────────────

    def _build_ui(self):
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ══════ 左侧面板 ══════
        left_outer = ttk.Frame(main_paned)
        main_paned.add(left_outer, weight=1)

        left_paned = ttk.PanedWindow(left_outer, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)

        # ── 模板面板 ──
        tmpl_frame = ttk.LabelFrame(left_paned, text="模板库", padding=4)
        left_paned.add(tmpl_frame, weight=1)

        tmpl_tb = ttk.Frame(tmpl_frame)
        tmpl_tb.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(tmpl_tb, text="➕ 保存为模板", command=self._save_as_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="🗑️ 删除", command=self._delete_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="📤 导出", command=self._export_templates).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="📥 导入", command=self._import_templates).pack(side=tk.LEFT, padx=2)

        self.tmpl_tree = ttk.Treeview(tmpl_frame, show="tree", selectmode="browse")
        self.tmpl_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tmpl_tree.bind("<<TreeviewSelect>>", self._on_tmpl_select)
        self.tmpl_tree.bind("<Double-1>", self._on_tmpl_double)

        tmpl_vsb = ttk.Scrollbar(tmpl_frame, orient=tk.VERTICAL, command=self.tmpl_tree.yview)
        tmpl_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tmpl_tree.config(yscrollcommand=tmpl_vsb.set)

        self._refresh_template_tree()

        self.tmpl_desc = ttk.Label(left_outer,
            text="提示: 单击查看描述, 双击加载模板代码",
            wraplength=300, foreground="#666666", font=("微软雅黑", 9))
        self.tmpl_desc.pack(fill=tk.X, padx=4, pady=2)

        # ── 代码编辑面板 ──
        code_frame = ttk.LabelFrame(left_paned, text="代码编辑器", padding=4)
        left_paned.add(code_frame, weight=2)

        code_tb = ttk.Frame(code_frame)
        code_tb.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(code_tb, text="▶ 运行", command=self.run_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="💾 保存脚本", command=self.save_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="📂 加载脚本", command=self.load_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="🔄 重置", command=self._load_default_template).pack(side=tk.LEFT, padx=2)

        self.live_var = tk.BooleanVar(value=False)
        live_cb = ttk.Checkbutton(code_tb, text="⚡ 实时渲染", variable=self.live_var,
                                   command=self._on_live_toggle)
        live_cb.pack(side=tk.RIGHT, padx=6)
        ttk.Label(code_tb, text="延迟 400ms", foreground="#888", font=("微软雅黑", 8)).pack(side=tk.RIGHT)

        # 快速标注工具栏
        anno_frame = ttk.LabelFrame(code_frame, text="快速标注工具（点击插入代码）", padding=2)
        anno_frame.pack(fill=tk.X, pady=(0, 2))

        anno_items = [
            ("➡️ 箭头", self._insert_arrow),
            ("⭕ 圆圈", self._insert_circle),
            ("📝 文本", self._insert_text),
            ("▭ 矩形", self._insert_rectangle),
            ("⎯ 水平线", self._insert_hline),
            ("⏐ 垂直线", self._insert_vline),
            ("🌟 高亮区", self._insert_highlight),
        ]
        for text, cmd in anno_items:
            ttk.Button(anno_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2, pady=1)

        # 代码编辑器
        editor_frame = ttk.Frame(code_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self.code_text = tk.Text(editor_frame, wrap=tk.NONE, undo=True,
                                  font=("Consolas", 11), padx=6, pady=4,
                                  bg="#fafafa", fg="#333333",
                                  insertbackground="#333333",
                                  selectbackground="#b4d7ff")
        self.code_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.code_text.bind("<KeyRelease>", self._on_code_key)

        line_canvas = LineNumberCanvas(editor_frame, self.code_text)
        line_canvas.pack(side=tk.LEFT, fill=tk.Y)

        vsb = ttk.Scrollbar(code_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.config(yscrollcommand=vsb.set)

        # ══════ 右侧面板 ══════
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # 图表工具栏
        ptb = ttk.Frame(right_frame)
        ptb.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(ptb, text="DPI:").pack(side=tk.LEFT, padx=(4, 0))
        self.dpi_var = tk.StringVar(value="100")
        dpi_c = ttk.Combobox(ptb, textvariable=self.dpi_var,
                             values=["80", "100", "120", "150", "200"], width=6, state="readonly")
        dpi_c.pack(side=tk.LEFT)
        dpi_c.bind("<<ComboboxSelected>>", lambda e: self.run_code())
        ttk.Separator(ptb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        ttk.Label(ptb, text="尺寸(英寸):").pack(side=tk.LEFT)
        self.fig_w_var = tk.StringVar(value="8")
        self.fig_h_var = tk.StringVar(value="6")
        ttk.Entry(ptb, textvariable=self.fig_w_var, width=4, justify=tk.CENTER).pack(side=tk.LEFT, padx=2)
        ttk.Label(ptb, text="×").pack(side=tk.LEFT)
        ttk.Entry(ptb, textvariable=self.fig_h_var, width=4, justify=tk.CENTER).pack(side=tk.LEFT, padx=2)
        ttk.Button(ptb, text="应用", command=self._apply_figsize).pack(side=tk.LEFT, padx=4)

        ttk.Separator(ptb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        ttk.Label(ptb, text="缩放:").pack(side=tk.LEFT)
        ttk.Button(ptb, text="🔍+", width=3, command=self._zoom_in).pack(side=tk.LEFT, padx=1)
        ttk.Button(ptb, text="🔍−", width=3, command=self._zoom_out).pack(side=tk.LEFT, padx=1)
        ttk.Button(ptb, text="重置", command=self._reset_figsize).pack(side=tk.LEFT, padx=4)

        ttk.Button(ptb, text="📥 保存图片", command=self.save_figure).pack(side=tk.RIGHT, padx=4)
        ttk.Button(ptb, text="🔧 清除图表", command=self.clear_figure).pack(side=tk.RIGHT, padx=2)

        # 内容区域：导航栏 + 图表并排
        self.content_frame = ttk.Frame(right_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # 子图导航栏（动态显示/隐藏）— 放在左侧
        self.subplot_nav_frame = ttk.LabelFrame(self.content_frame, text="子图导航", padding=2)
        # 默认不 pack，有多个子图时才显示

        # 图表容器
        self.canvas_frame = ttk.Frame(self.content_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 图表画布
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        nav = NavigationToolbar2Tk(self.canvas, self.canvas_frame, pack_toolbar=False)
        nav.pack(fill=tk.X)

        # 状态栏
        self.status = ttk.Label(self.root,
            text="就绪 | Ctrl+R 运行 | 多子图自动启用导航栏",
            relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ────────────────── 子图导航 ──────────────────

    def _update_subplot_nav(self):
        """检测 figure 中的子图数量并更新导航栏"""
        # 清除旧导航栏
        for w in self.subplot_nav_frame.winfo_children():
            w.destroy()

        n_axes = len(self.fig.axes)
        if n_axes <= 1 or self.view_mode == "single":
            self.subplot_nav_frame.pack_forget()
            return

        # 显示导航栏 — 放在 content_frame 左侧
        self.subplot_nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2), before=self.canvas_frame)

        # 生成缩略图 — 垂直排列
        self.thumbnail_photos = []
        for i, ax in enumerate(self.fig.axes):
            if HAS_PIL:
                photo = self._create_thumbnail(ax)
                if photo:
                    btn = tk.Button(self.subplot_nav_frame, image=photo,
                                    command=lambda idx=i: self._show_single_subplot(idx),
                                    relief=tk.RIDGE, bd=2)
                    btn.pack(side=tk.TOP, padx=2, pady=1)
                    self.thumbnail_photos.append(photo)
                    continue
            # 无 PIL 或缩略图生成失败时回退到文本按钮
            ttk.Button(self.subplot_nav_frame, text=f"子图{i+1}",
                       command=lambda idx=i: self._show_single_subplot(idx)).pack(side=tk.TOP, padx=2, pady=1)

    def _create_thumbnail(self, source_ax):
        """为指定 axes 生成缩略图 PhotoImage"""
        try:
            tmp_fig = Figure(figsize=(1.6, 1.2), dpi=60)
            tmp_ax = tmp_fig.add_subplot(111)
            self._clone_axes(source_ax, tmp_ax)
            tmp_fig.tight_layout()

            buf = io.BytesIO()
            tmp_fig.savefig(buf, format='png', dpi=60, facecolor='white')
            buf.seek(0)

            img = Image.open(buf)
            photo = ImageTk.PhotoImage(img)

            plt.close(tmp_fig)
            return photo
        except Exception:
            return None

    def _clone_axes(self, src_ax, dst_ax):
        """将 src_ax 的关键绘图元素复制到 dst_ax"""
        # 复制 lines (plot)
        for line in src_ax.get_lines():
            dst_ax.plot(line.get_xdata(), line.get_ydata(),
                        color=line.get_color(),
                        linewidth=line.get_linewidth(),
                        linestyle=line.get_linestyle(),
                        marker=line.get_marker(),
                        markersize=line.get_markersize(),
                        label=line.get_label(),
                        alpha=line.get_alpha() if line.get_alpha() is not None else 1.0)

        # 复制 collections (scatter, contourf 等)
        for coll in src_ax.collections:
            if hasattr(coll, 'get_offsets'):
                offsets = coll.get_offsets()
                if len(offsets) > 0:
                    facecolors = coll.get_facecolor()
                    sizes = coll.get_sizes() if hasattr(coll, 'get_sizes') else None
                    alpha = coll.get_alpha()
                    dst_ax.scatter(offsets[:, 0], offsets[:, 1],
                                   c=facecolors, s=sizes, alpha=alpha)

        # 复制 images (imshow)
        for img in src_ax.images:
            arr = img.get_array()
            extent = img.get_extent()
            cmap = img.get_cmap()
            alpha = img.get_alpha()
            norm = img.norm
            dst_ax.imshow(arr, extent=extent, cmap=cmap, alpha=alpha,
                          vmin=norm.vmin, vmax=norm.vmax)

        # 复制 patches (矩形、圆等)
        for patch in src_ax.patches:
            try:
                from matplotlib.patches import Rectangle, Circle
                if isinstance(patch, Rectangle):
                    new_patch = Rectangle(
                        patch.get_xy(), patch.get_width(), patch.get_height(),
                        facecolor=patch.get_facecolor(), edgecolor=patch.get_edgecolor(),
                        linewidth=patch.get_linewidth(), linestyle=patch.get_linestyle(),
                        alpha=patch.get_alpha(), fill=patch.get_fill())
                    dst_ax.add_patch(new_patch)
                elif isinstance(patch, Circle):
                    new_patch = Circle(
                        patch.center, patch.radius,
                        facecolor=patch.get_facecolor(), edgecolor=patch.get_edgecolor(),
                        linewidth=patch.get_linewidth(), linestyle=patch.get_linestyle(),
                        alpha=patch.get_alpha(), fill=patch.get_fill())
                    dst_ax.add_patch(new_patch)
            except Exception:
                pass

        # 复制文本标注
        for text in src_ax.texts:
            dst_ax.text(text.get_position()[0], text.get_position()[1],
                        text.get_text(), fontsize=text.get_fontsize(),
                        color=text.get_color(), ha=text.get_ha(), va=text.get_va(),
                        rotation=text.get_rotation(), alpha=text.get_alpha())

        # 复制基本属性
        dst_ax.set_title(src_ax.get_title())
        dst_ax.set_xlabel(src_ax.get_xlabel())
        dst_ax.set_ylabel(src_ax.get_ylabel())
        dst_ax.set_xlim(src_ax.get_xlim())
        dst_ax.set_ylim(src_ax.get_ylim())

        # 刻度标签
        xticklabels = [t.get_text() for t in src_ax.get_xticklabels()]
        yticklabels = [t.get_text() for t in src_ax.get_yticklabels()]
        if any(xticklabels):
            dst_ax.set_xticklabels(xticklabels)
        if any(yticklabels):
            dst_ax.set_yticklabels(yticklabels)

        # 网格与图例
        xgrid = src_ax.xaxis._major_tick_kw.get('gridOn', False)
        ygrid = src_ax.yaxis._major_tick_kw.get('gridOn', False)
        dst_ax.grid(xgrid or ygrid, alpha=0.3)
        if src_ax.get_legend() is not None:
            dst_ax.legend()

        # 比例
        dst_ax.set_aspect(src_ax.get_aspect())

    def _show_single_subplot(self, index):
        """切换到单图模式：只显示第 index 个子图"""
        if index >= len(self.fig.axes):
            return

        self.view_mode = "single"
        self.current_single_index = index

        try:
            dpi = int(self.dpi_var.get())
        except ValueError:
            dpi = 100
        try:
            w = float(self.fig_w_var.get())
            h = float(self.fig_h_var.get())
        except ValueError:
            w, h = 8, 6

        # 创建新的单图 figure
        self._overview_fig = self.fig  # 保存总览引用
        self.fig = Figure(figsize=(w, h), dpi=dpi)
        new_ax = self.fig.add_subplot(111)

        # 复制选中子图的内容
        src_ax = self._overview_fig.axes[index]
        self._clone_axes(src_ax, new_ax)
        self.fig.tight_layout()

        # 更新画布
        self.canvas.figure = self.fig
        self.canvas.draw()

        # 更新导航栏为返回按钮
        self._update_single_nav(index)

        self.status.config(text=f"单图模式: 子图 {index+1}/{len(self._overview_fig.axes)} | 点击 🔙 返回总览")

    def _update_single_nav(self, current_index):
        """单图模式下显示返回按钮 — 垂直排列在左侧"""
        for w in self.subplot_nav_frame.winfo_children():
            w.destroy()
        self.subplot_nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2), before=self.canvas_frame)

        ttk.Label(self.subplot_nav_frame,
                  text=f"子图 {current_index+1}").pack(side=tk.TOP, padx=4, pady=2)

        # 左右切换按钮 — 垂直排列
        if current_index > 0:
            ttk.Button(self.subplot_nav_frame, text="◀ 上一个",
                       command=lambda: self._show_single_subplot(current_index - 1)).pack(side=tk.TOP, padx=2, pady=1)
        if current_index < len(self._overview_fig.axes) - 1:
            ttk.Button(self.subplot_nav_frame, text="下一个 ▶",
                       command=lambda: self._show_single_subplot(current_index + 1)).pack(side=tk.TOP, padx=2, pady=1)

        ttk.Button(self.subplot_nav_frame, text="🔙 返回总览",
                   command=self._show_overview).pack(side=tk.TOP, padx=2, pady=(10, 2))

    def _show_overview(self):
        """返回总览模式"""
        self.view_mode = "overview"
        self.current_single_index = None

        # 恢复原始 figure
        if hasattr(self, '_overview_fig'):
            self.fig = self._overview_fig
            self.canvas.figure = self.fig
            del self._overview_fig

        self.canvas.draw()
        self._update_subplot_nav()
        self.status.config(text="总览模式 | 所有子图")

    # ────────────────── 尺寸与缩放 ──────────────────

    def _apply_figsize(self):
        """应用新的 Figure 尺寸，同时通知 canvas 重新分配绘制缓冲区"""
        try:
            w = float(self.fig_w_var.get())
            h = float(self.fig_h_var.get())
            if w < 1 or h < 1 or w > 30 or h > 30:
                raise ValueError("尺寸范围 1~30 英寸")
        except ValueError as e:
            self.status.config(text=f"尺寸格式错误: {e}")
            return

        self.fig.set_size_inches(w, h)
        # 关键：通知 TkAgg backend 尺寸已改变，否则旧图像会残留在画布上
        self.canvas.resize_event()
        self.canvas.draw_idle()
        self.status.config(text=f"Figure 尺寸已设为 {w:.1f} × {h:.1f} 英寸")

    def _zoom_in(self):
        try:
            w = float(self.fig_w_var.get()) * 1.2
            h = float(self.fig_h_var.get()) * 1.2
            self.fig_w_var.set(f"{w:.1f}")
            self.fig_h_var.set(f"{h:.1f}")
            self._apply_figsize()
        except ValueError:
            pass

    def _zoom_out(self):
        try:
            w = float(self.fig_w_var.get()) * 0.8
            h = float(self.fig_h_var.get()) * 0.8
            if w < 1: w = 1
            if h < 1: h = 1
            self.fig_w_var.set(f"{w:.1f}")
            self.fig_h_var.set(f"{h:.1f}")
            self._apply_figsize()
        except ValueError:
            pass

    def _reset_figsize(self):
        self.fig_w_var.set("8")
        self.fig_h_var.set("6")
        self._apply_figsize()

    # ────────────────── 实时渲染 ──────────────────

    def _on_live_toggle(self):
        if self.live_var.get():
            self.status.config(text="⚡ 实时渲染已开启 | 停止输入 400ms 后自动刷新")
            self._trigger_live_run()
        else:
            self.status.config(text="实时渲染已关闭 | 按 Ctrl+R 手动运行")
            if self._live_after_id is not None:
                self.root.after_cancel(self._live_after_id)
                self._live_after_id = None

    def _on_code_key(self, event=None):
        if not self.live_var.get():
            return
        if event and event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                                       "Alt_L", "Alt_R", "Up", "Down", "Left", "Right",
                                       "Prior", "Next", "Home", "End", "Caps_Lock"):
            return
        self._trigger_live_run()

    def _trigger_live_run(self):
        if self._live_after_id is not None:
            self.root.after_cancel(self._live_after_id)
        self._live_after_id = self.root.after(400, self._live_run)

    def _live_run(self):
        self._live_after_id = None
        self.run_code(silent=True)

    # ────────────────── 标注工具 ──────────────────

    def _insert_at_cursor(self, snippet):
        self.code_text.insert(tk.INSERT, snippet)
        self.status.config(text="已插入标注代码")
        if self.live_var.get():
            self._trigger_live_run()

    def _insert_arrow(self):
        snippet = """# 添加箭头标注 (如有多子图，plt.gca() 自动指向最后操作的子图)
plt.gca().annotate('', xy=(0.5, 0.5), xytext=(0.2, 0.2),
            arrowprops=dict(arrowstyle='->', color='red', lw=2))
"""
        self._insert_at_cursor(snippet)

    def _insert_circle(self):
        snippet = """# 添加圆圈 (如有多子图，plt.gca() 自动指向最后操作的子图)
from matplotlib.patches import Circle
circle = Circle((0.5, 0.5), 0.1, fill=False, edgecolor='red', linewidth=2)
plt.gca().add_patch(circle)
"""
        self._insert_at_cursor(snippet)

    def _insert_text(self):
        snippet = """# 添加文本标注 (如有多子图，plt.gca() 自动指向最后操作的子图)
plt.gca().text(0.5, 0.5, '你的文本', fontsize=12, color='red',
        ha='center', va='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
"""
        self._insert_at_cursor(snippet)

    def _insert_rectangle(self):
        snippet = """# 添加矩形框 (如有多子图，plt.gca() 自动指向最后操作的子图)
from matplotlib.patches import Rectangle
rect = Rectangle((0.3, 0.3), 0.4, 0.4, fill=False, edgecolor='blue', linewidth=2, linestyle='--')
plt.gca().add_patch(rect)
"""
        self._insert_at_cursor(snippet)

    def _insert_hline(self):
        snippet = """# 添加水平参考线 (如有多子图，plt.gca() 自动指向最后操作的子图)
plt.gca().axhline(y=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.7, label='参考线')
"""
        self._insert_at_cursor(snippet)

    def _insert_vline(self):
        snippet = """# 添加垂直参考线 (如有多子图，plt.gca() 自动指向最后操作的子图)
plt.gca().axvline(x=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.7, label='参考线')
"""
        self._insert_at_cursor(snippet)

    def _insert_highlight(self):
        snippet = """# 添加高亮区域 (如有多子图，plt.gca() 自动指向最后操作的子图)
plt.gca().axvspan(0.3, 0.7, color='yellow', alpha=0.2, label='高亮区')
# 或水平区域: plt.gca().axhspan(ymin, ymax, ...)
"""
        self._insert_at_cursor(snippet)

    # ────────────────── 模板相关 ──────────────────

    def _refresh_template_tree(self):
        for item in self.tmpl_tree.get_children():
            self.tmpl_tree.delete(item)
        builtin_node = self.tmpl_tree.insert("", tk.END, text="📚 内置模板", open=True)
        for category, items in self.tmpl_mgr.get_builtin().items():
            cat_node = self.tmpl_tree.insert(builtin_node, tk.END, text=f"  {category}", open=False)
            for name in items:
                self.tmpl_tree.insert(cat_node, tk.END, text=f"    {name}",
                                      values=("builtin", category, name))
        user_node = self.tmpl_tree.insert("", tk.END, text="👤 我的模板", open=True)
        for category, items in self.tmpl_mgr.get_user().items():
            cat_node = self.tmpl_tree.insert(user_node, tk.END, text=f"  {category}", open=False)
            for name in items:
                self.tmpl_tree.insert(cat_node, tk.END, text=f"    {name}",
                                      values=("user", category, name))
        if not self.tmpl_mgr.get_user():
            self.tmpl_tree.insert(user_node, tk.END, text="    (暂无自定义模板)")

    def _on_tmpl_select(self, event=None):
        sel = self.tmpl_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.tmpl_tree.item(item, "values")
        if not vals or len(vals) < 3:
            return
        source, category, name = vals[0], vals[1], vals[2]
        info = self.tmpl_mgr.get_template_info(source, category, name)
        desc = info.get("desc", "无描述")
        self.tmpl_desc.config(text=f"【{name}】{desc}  |  双击加载此模板")

    def _on_tmpl_double(self, event=None):
        sel = self.tmpl_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.tmpl_tree.item(item, "values")
        if not vals or len(vals) < 3:
            return
        source, category, name = vals[0], vals[1], vals[2]
        code = self.tmpl_mgr.get_template_code(source, category, name)
        if code:
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", code)
            self.status.config(text=f"已加载模板: {category} / {name}")
            self.run_code()

    def _save_as_template(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("提示", "代码为空，无法保存为模板")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("保存为模板")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="分类:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        cat_var = tk.StringVar(value="自定义")
        ttk.Combobox(dialog, textvariable=cat_var,
                     values=list(self.tmpl_mgr.get_user().keys()) + ["自定义"]).pack(fill=tk.X, padx=10)

        ttk.Label(dialog, text="模板名称:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        name_var = tk.StringVar(value="我的模板")
        ttk.Entry(dialog, textvariable=name_var).pack(fill=tk.X, padx=10)

        ttk.Label(dialog, text="描述:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        desc_var = tk.StringVar(value="")
        ttk.Entry(dialog, textvariable=desc_var).pack(fill=tk.X, padx=10)

        def do_save():
            cat = cat_var.get().strip()
            name = name_var.get().strip()
            desc = desc_var.get().strip() or "用户自定义模板"
            if not cat or not name:
                messagebox.showwarning("提示", "分类和名称不能为空")
                return
            self.tmpl_mgr.add_user_template(cat, name, desc, code)
            self._refresh_template_tree()
            self.status.config(text=f"模板已保存: {cat} / {name}")
            dialog.destroy()

        ttk.Button(dialog, text="保存", command=do_save).pack(pady=15)

    def _delete_template(self):
        sel = self.tmpl_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个模板")
            return
        item = sel[0]
        vals = self.tmpl_tree.item(item, "values")
        if not vals or len(vals) < 3:
            messagebox.showwarning("提示", "请选择具体的模板项")
            return
        source, category, name = vals[0], vals[1], vals[2]
        if source != "user":
            messagebox.showwarning("提示", "只能删除用户自定义模板")
            return
        if messagebox.askyesno("确认删除", f"确定要删除模板「{name}」吗？"):
            if self.tmpl_mgr.delete_user_template(category, name):
                self._refresh_template_tree()
                self.status.config(text=f"已删除模板: {name}")

    def _export_templates(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON 文件", "*.json")])
        if path:
            self.tmpl_mgr.export_to_file(path)
            self.status.config(text=f"模板库已导出: {path}")

    def _import_templates(self):
        path = filedialog.askopenfilename(filetypes=[("JSON 文件", "*.json")])
        if path:
            try:
                self.tmpl_mgr.import_from_file(path)
                self._refresh_template_tree()
                self.status.config(text=f"模板库已导入: {path}")
            except Exception as e:
                messagebox.showerror("导入失败", str(e))

    def _load_default_template(self):
        code = self.tmpl_mgr.get_template_code("builtin", "基础图表", "正弦+余弦波")
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", code)
        self.status.config(text="已加载默认示例 | Ctrl+R 运行")
        self.run_code()

    # ────────────────── 核心逻辑 ──────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-r>", lambda e: self.run_code())
        self.root.bind("<Control-R>", lambda e: self.run_code())
        self.root.bind("<Control-s>", lambda e: self.save_script())
        self.root.bind("<Control-S>", lambda e: self.save_script())

    def run_code(self, event=None, silent=False):
        # 单图模式下运行代码 = 先返回总览
        if self.view_mode == "single":
            self._show_overview()

        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            if not silent:
                self.status.config(text="错误: 代码为空")
            return

        if not silent:
            self.status.config(text="正在运行...")
            self.root.update_idletasks()

        try:
            dpi = int(self.dpi_var.get())
        except ValueError:
            dpi = 100

        try:
            w = float(self.fig_w_var.get())
            h = float(self.fig_h_var.get())
            self.fig.set_size_inches(w, h)
        except ValueError:
            pass

        self.fig.clear()
        self.fig.set_dpi(dpi)

        try:
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            Axes3D = None
        try:
            from scipy import stats
        except ImportError:
            stats = None

        exec_globals = {
            "np": np, "fig": self.fig, "ax": None,
            "plt": plt, "Axes3D": Axes3D, "stats": stats,
        }

        try:
            exec(code, exec_globals)
            self.canvas.draw()

            # 更新子图导航栏
            self._update_subplot_nav()

            n_axes = len(self.fig.axes)
            size_info = f"{self.fig.get_size_inches()[0]:.1f}×{self.fig.get_size_inches()[1]:.1f}英寸"
            if n_axes > 1:
                msg = f"运行成功 | {n_axes} 个子图 | DPI={dpi} | {size_info}"
            else:
                msg = f"运行成功 | DPI={dpi} | {size_info}"
            if not silent:
                self.status.config(text=msg)
        except Exception as e:
            err = traceback.format_exc()
            short_err = str(e)[:80]
            if silent:
                self.status.config(text=f"⚡实时: {short_err}")
            else:
                self.status.config(text=f"错误: {short_err}")
                self._show_error(err)

    def _show_error(self, err_text):
        win = tk.Toplevel(self.root)
        win.title("运行错误")
        win.geometry("700x400")
        txt = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10), bg="#fff0f0", fg="#cc0000")
        txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        txt.insert("1.0", err_text)
        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=4)

    def clear_figure(self):
        self.fig.clear()
        self.canvas.draw()
        self._update_subplot_nav()
        self.status.config(text="图表已清除")

    def save_figure(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("PDF 文档", "*.pdf"),
                       ("SVG 矢量图", "*.svg"), ("所有文件", "*.*")]
        )
        if path:
            try:
                dpi = int(self.dpi_var.get())
            except ValueError:
                dpi = 100
            self.fig.savefig(path, dpi=dpi, bbox_inches="tight")
            self.status.config(text=f"图片已保存: {path}")

    def save_script(self, event=None):
        if self.script_path:
            path = self.script_path
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python 脚本", "*.py"), ("所有文件", "*.*")]
            )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.code_text.get("1.0", tk.END))
            self.script_path = path
            self.status.config(text=f"脚本已保存: {os.path.basename(path)}")

    def load_script(self):
        path = filedialog.askopenfilename(
            filetypes=[("Python 脚本", "*.py"), ("所有文件", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", content)
            self.script_path = path
            self.status.config(text=f"已加载: {os.path.basename(path)}")
            self.run_code()


# ════════════════════════════════════════
# 入口
# ════════════════════════════════════════

def main():
    root = tk.Tk()
    app = CodePlotAppV4(root)
    root.mainloop()


if __name__ == "__main__":
    main()
