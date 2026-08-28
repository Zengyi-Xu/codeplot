"""
CodePlot v2 — 代码驱动的实时画图工具（模板增强版）
用法: python codeplot_v2.py

功能:
  - 左侧代码编辑器, 编写 matplotlib 代码
  - 右侧实时渲染图表
  - 丰富的内置模板库（20+ 种图表类型）
  - 支持自定义模板: 保存 / 编辑 / 删除 / 导入导出
  - 支持 Ctrl+R 运行, Ctrl+S 保存脚本

模板数据存储:
  程序首次运行时会生成 templates.json 文件,
  内置模板会自动写入, 用户模板保存在其中。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import traceback
import os
import json


# ════════════════════════════════════════
# 内置模板定义（首次运行时自动写入模板库）
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
""",
            "imports": {"plt": "matplotlib.pyplot"}
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
""",
            "imports": {"plt": "matplotlib.pyplot"}
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
from matplotlib.patches import Polygon

np.random.seed(42)
data = [np.random.normal(0, std, 100) for std in range(1, 5)]

ax = fig.add_subplot(111)
ax.clear()
positions = [1, 2, 3, 4]
for i, (d, pos) in enumerate(zip(data, positions)):
    # 计算KDE
    from scipy import stats
    kde = stats.gaussian_kde(d)
    x_range = np.linspace(d.min(), d.max(), 100)
    kde_vals = kde(x_range)
    kde_vals = kde_vals / kde_vals.max() * 0.4
    # 绘制小提琴
    ax.fill_betweenx(x_range, pos - kde_vals, pos + kde_vals, alpha=0.6, color=plt.cm.Set2(i))
    # 箱线图元素
    q1, median, q3 = np.percentile(d, [25, 50, 75])
    ax.plot([pos - 0.05, pos + 0.05], [median, median], 'k-', linewidth=2)
    ax.plot(pos, median, 'wo', markersize=5)

ax.set_xticks(positions)
ax.set_xticklabels(['A', 'B', 'C', 'D'])
ax.set_title('小提琴图', fontsize=14)
ax.set_ylabel('数值')
fig.tight_layout()
""",
            "imports": {"plt": "matplotlib.pyplot"}
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
""",
            "imports": {}
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
# 在每个单元格标注数值
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
import matplotlib.pyplot as plt
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
""",
            "imports": {"plt": "matplotlib.pyplot"}
        },
    },
}


# ════════════════════════════════════════
# 模板管理器
# ════════════════════════════════════════

class TemplateManager:
    """模板管理器：负责加载、保存和管理内置/用户模板"""

    def __init__(self, filepath=None):
        if filepath is None:
            # 存储在程序所在目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.filepath = os.path.join(base_dir, "templates.json")
        else:
            self.filepath = filepath
        self.templates = self._load_or_init()

    def _load_or_init(self):
        """加载模板文件，不存在则创建"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 确保内置模板是最新的（合并新模板）
                data["builtin"] = self._merge_builtin(data.get("builtin", {}))
                return data
            except Exception:
                pass
        # 首次运行或文件损坏：写入内置模板
        data = {"builtin": dict(BUILTIN_TEMPLATES), "user": {}}
        self._save(data)
        return data

    def _merge_builtin(self, existing):
        """合并内置模板：保留用户没有改动的，更新新增的"""
        merged = {}
        for category, items in BUILTIN_TEMPLATES.items():
            merged[category] = {}
            for name, tmpl in items.items():
                # 如果现有模板存在且code一致，保留；否则用新的
                if category in existing and name in existing[category]:
                    existing_code = existing[category][name].get("code", "")
                    if existing_code == tmpl["code"]:
                        merged[category][name] = existing[category][name]
                    else:
                        # 用户修改过，保留用户版本但标记
                        merged[category][name] = existing[category][name]
                else:
                    merged[category][name] = dict(tmpl)
        return merged

    def _save(self, data=None):
        if data is None:
            data = self.templates
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all(self):
        return self.templates

    def get_builtin(self):
        return self.templates.get("builtin", {})

    def get_user(self):
        return self.templates.get("user", {})

    def add_user_template(self, category, name, desc, code):
        """添加用户自定义模板"""
        if category not in self.templates["user"]:
            self.templates["user"][category] = {}
        self.templates["user"][category][name] = {"desc": desc, "code": code}
        self._save()

    def delete_user_template(self, category, name):
        """删除用户模板（内置模板不可删除）"""
        user = self.templates.get("user", {})
        if category in user and name in user[category]:
            del user[category][name]
            if not user[category]:
                del user[category]
            self._save()
            return True
        return False

    def rename_user_template(self, old_cat, old_name, new_cat, new_name):
        """重命名用户模板"""
        user = self.templates.get("user", {})
        if old_cat in user and old_name in user[old_cat]:
            tmpl = user[old_cat].pop(old_name)
            if not user[old_cat]:
                del user[old_cat]
            if new_cat not in user:
                user[new_cat] = {}
            user[new_cat][new_name] = tmpl
            self._save()
            return True
        return False

    def get_template_code(self, source, category, name):
        """获取模板代码"""
        section = self.templates.get(source, {})
        cat = section.get(category, {})
        tmpl = cat.get(name, {})
        return tmpl.get("code", "")

    def get_template_info(self, source, category, name):
        """获取模板完整信息"""
        section = self.templates.get(source, {})
        cat = section.get(category, {})
        return cat.get(name, {})

    def export_to_file(self, path):
        """导出模板库到文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    def import_from_file(self, path):
        """从文件导入模板（合并到用户模板）"""
        with open(path, "r", encoding="utf-8") as f:
            imported = json.load(f)
        # 只合并用户模板
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
    """代码编辑器行号画布"""
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
# 主应用
# ════════════════════════════════════════

class CodePlotAppV2:
    def __init__(self, root):
        self.root = root
        self.root.title("CodePlot v2 — 代码驱动实时画图")
        self.root.geometry("1550x950")
        self.root.minsize(1000, 650)
        self.script_path = None

        # 模板管理器
        self.tmpl_mgr = TemplateManager()

        self._build_ui()
        self._bind_shortcuts()
        self._load_default_template()

    # ────────────────── UI 构建 ──────────────────

    def _build_ui(self):
        # 主分割窗口: 左(模板+代码) | 右(图表)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ══════ 左侧面板 ══════
        left_outer = ttk.Frame(main_paned)
        main_paned.add(left_outer, weight=1)

        # 左侧再用 PanedWindow 分割: 上(模板) | 下(代码)
        left_paned = ttk.PanedWindow(left_outer, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)

        # ── 模板面板 ──
        tmpl_frame = ttk.LabelFrame(left_paned, text="模板库", padding=4)
        left_paned.add(tmpl_frame, weight=1)

        # 模板工具栏
        tmpl_tb = ttk.Frame(tmpl_frame)
        tmpl_tb.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(tmpl_tb, text="➕ 保存为模板", command=self._save_as_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="🗑️ 删除", command=self._delete_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="📤 导出", command=self._export_templates).pack(side=tk.LEFT, padx=2)
        ttk.Button(tmpl_tb, text="📥 导入", command=self._import_templates).pack(side=tk.LEFT, padx=2)

        # 模板树
        self.tmpl_tree = ttk.Treeview(tmpl_frame, show="tree", selectmode="browse")
        self.tmpl_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tmpl_tree.bind("<<TreeviewSelect>>", self._on_tmpl_select)
        self.tmpl_tree.bind("<Double-1>", self._on_tmpl_double)

        tmpl_vsb = ttk.Scrollbar(tmpl_frame, orient=tk.VERTICAL, command=self.tmpl_tree.yview)
        tmpl_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tmpl_tree.config(yscrollcommand=tmpl_vsb.set)

        self._refresh_template_tree()

        # 模板描述标签
        self.tmpl_desc = ttk.Label(left_outer, text="提示: 单击查看描述, 双击加载模板代码",
                                    wraplength=300, foreground="#666666", font=("微软雅黑", 9))
        self.tmpl_desc.pack(fill=tk.X, padx=4, pady=2)

        # ── 代码编辑面板 ──
        code_frame = ttk.LabelFrame(left_paned, text="代码编辑器", padding=4)
        left_paned.add(code_frame, weight=2)

        # 代码工具栏
        code_tb = ttk.Frame(code_frame)
        code_tb.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(code_tb, text="▶ 运行", command=self.run_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="💾 保存脚本", command=self.save_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="📂 加载脚本", command=self.load_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(code_tb, text="🔄 重置示例", command=self._load_default_template).pack(side=tk.LEFT, padx=2)

        # 代码编辑器
        editor_frame = ttk.Frame(code_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self.code_text = tk.Text(editor_frame, wrap=tk.NONE, undo=True,
                                  font=("Consolas", 11), padx=6, pady=4,
                                  bg="#fafafa", fg="#333333",
                                  insertbackground="#333333",
                                  selectbackground="#b4d7ff")
        self.code_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

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
        ttk.Label(ptb, text="DPI:").pack(side=tk.LEFT, padx=4)
        self.dpi_var = tk.StringVar(value="100")
        dpi_c = ttk.Combobox(ptb, textvariable=self.dpi_var,
                             values=["80", "100", "120", "150", "200"], width=6, state="readonly")
        dpi_c.pack(side=tk.LEFT)
        dpi_c.bind("<<ComboboxSelected>>", lambda e: self.run_code())
        ttk.Button(ptb, text="📥 保存图片", command=self.save_figure).pack(side=tk.RIGHT, padx=4)
        ttk.Button(ptb, text="🔧 清除图表", command=self.clear_figure).pack(side=tk.RIGHT, padx=2)

        # 图表画布
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        nav = NavigationToolbar2Tk(self.canvas, right_frame, pack_toolbar=False)
        nav.pack(fill=tk.X)

        # 状态栏
        self.status = ttk.Label(self.root, text="就绪 | 按 Ctrl+R 运行 | 双击模板加载",
                                relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ────────────────── 模板相关 ──────────────────

    def _refresh_template_tree(self):
        """刷新模板树"""
        # 清空
        for item in self.tmpl_tree.get_children():
            self.tmpl_tree.delete(item)

        # 内置模板
        builtin_node = self.tmpl_tree.insert("", tk.END, text="📚 内置模板", open=True)
        for category, items in self.tmpl_mgr.get_builtin().items():
            cat_node = self.tmpl_tree.insert(builtin_node, tk.END, text=f"  {category}", open=False)
            for name in items:
                self.tmpl_tree.insert(cat_node, tk.END, text=f"    {name}",
                                      values=("builtin", category, name))

        # 用户模板
        user_node = self.tmpl_tree.insert("", tk.END, text="👤 我的模板", open=True)
        for category, items in self.tmpl_mgr.get_user().items():
            cat_node = self.tmpl_tree.insert(user_node, tk.END, text=f"  {category}", open=False)
            for name in items:
                self.tmpl_tree.insert(cat_node, tk.END, text=f"    {name}",
                                      values=("user", category, name))

        # 如果没有用户模板，显示提示
        if not self.tmpl_mgr.get_user():
            self.tmpl_tree.insert(user_node, tk.END, text="    (暂无自定义模板)")

    def _on_tmpl_select(self, event=None):
        """单击模板：显示描述"""
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
        """双击模板：加载代码"""
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
        """将当前代码保存为用户模板"""
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("提示", "代码为空，无法保存为模板")
            return

        # 询问分类和名称
        dialog = tk.Toplevel(self.root)
        dialog.title("保存为模板")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="分类:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        cat_var = tk.StringVar(value="自定义")
        cat_entry = ttk.Combobox(dialog, textvariable=cat_var,
                                  values=list(self.tmpl_mgr.get_user().keys()) + ["自定义"])
        cat_entry.pack(fill=tk.X, padx=10)

        ttk.Label(dialog, text="模板名称:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        name_var = tk.StringVar(value="我的模板")
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(fill=tk.X, padx=10)

        ttk.Label(dialog, text="描述:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        desc_var = tk.StringVar(value="")
        desc_entry = ttk.Entry(dialog, textvariable=desc_var)
        desc_entry.pack(fill=tk.X, padx=10)

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
        """删除选中的用户模板"""
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
        """导出模板库到文件"""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")]
        )
        if path:
            self.tmpl_mgr.export_to_file(path)
            self.status.config(text=f"模板库已导出: {path}")

    def _import_templates(self):
        """从文件导入模板"""
        path = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json")]
        )
        if path:
            try:
                self.tmpl_mgr.import_from_file(path)
                self._refresh_template_tree()
                self.status.config(text=f"模板库已导入: {path}")
            except Exception as e:
                messagebox.showerror("导入失败", str(e))

    def _load_default_template(self):
        """加载默认示例代码（正弦+余弦）"""
        code = self.tmpl_mgr.get_template_code("builtin", "基础图表", "正弦+余弦波")
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", code)
        self.status.config(text="已加载默认示例 | Ctrl+R 运行")
        self.run_code()

    # ────────────────── 核心逻辑（与 v1 相同）──────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-r>", lambda e: self.run_code())
        self.root.bind("<Control-R>", lambda e: self.run_code())
        self.root.bind("<Control-s>", lambda e: self.save_script())
        self.root.bind("<Control-S>", lambda e: self.save_script())

    def run_code(self, event=None):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            self.status.config(text="错误: 代码为空")
            return

        self.status.config(text="正在运行...")
        self.root.update_idletasks()

        try:
            dpi = int(self.dpi_var.get())
        except ValueError:
            dpi = 100

        self.fig.clear()
        self.fig.set_dpi(dpi)

        # 执行代码前确保需要的 import 可用
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            plt = None
        try:
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            Axes3D = None
        try:
            from scipy import stats
        except ImportError:
            stats = None

        exec_globals = {
            "np": np,
            "fig": self.fig,
            "ax": None,
            "plt": plt,
            "Axes3D": Axes3D,
            "stats": stats,
        }

        try:
            exec(code, exec_globals)
            self.canvas.draw()
            self.status.config(text=f"运行成功 | DPI={dpi} | Ctrl+R 重新运行")
        except Exception as e:
            err = traceback.format_exc()
            self.status.config(text=f"错误: {str(e)[:80]}")
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
        self.status.config(text="图表已清除")

    def save_figure(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("PDF 文档", "*.pdf"),
                       ("SVG 矢量图", "*.svg"), ("所有文件", "*.*")]
        )
        if path:
            self.fig.savefig(path, dpi=int(self.dpi_var.get()), bbox_inches="tight")
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
    app = CodePlotAppV2(root)
    root.mainloop()


if __name__ == "__main__":
    main()
