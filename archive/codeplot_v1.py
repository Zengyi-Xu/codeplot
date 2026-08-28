"""
CodePlot - 代码驱动的实时画图工具
用法: python codeplot.py

功能:
  - 左侧代码编辑器, 编写 matplotlib 代码
  - 右侧实时渲染图表
  - 预置示例数据, 开箱即用
  - 支持 Ctrl+R 运行, Ctrl+S 保存脚本
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import traceback
import os


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


class CodePlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CodePlot - 代码驱动实时画图")
        self.root.geometry("1400x900")
        self.root.minsize(900, 600)
        self.script_path = None

        self._build_ui()
        self._bind_shortcuts()
        self._insert_demo_code()

    # ────────────────── UI 构建 ──────────────────

    def _build_ui(self):
        # 主框架
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── 左侧面板: 代码编辑区
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # 工具栏
        tb = ttk.Frame(left_frame)
        tb.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(tb, text="▶ 运行", command=self.run_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="💾 保存", command=self.save_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="📂 加载", command=self.load_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="🔄 重置", command=self._insert_demo_code).pack(side=tk.LEFT, padx=2)
        ttk.Label(tb, text="预设:").pack(side=tk.LEFT, padx=(10, 0))
        self.data_var = tk.StringVar(value="请选择...")
        dc = ttk.Combobox(tb, textvariable=self.data_var, state="readonly",
                          values=["请选择...", "正弦波", "随机散点", "多组折线", "柱状图", "自定义"],
                          width=12)
        dc.pack(side=tk.LEFT, padx=2)
        dc.bind("<<ComboboxSelected>>", self._on_preset_data)

        # 代码编辑器
        editor_frame = ttk.Frame(left_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self.code_text = tk.Text(editor_frame, wrap=tk.NONE, undo=True,
                                  font=("Consolas", 11), padx=6, pady=4,
                                  bg="#fafafa", fg="#333333",
                                  insertbackground="#333333",
                                  selectbackground="#b4d7ff")
        self.code_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        line_canvas = LineNumberCanvas(editor_frame, self.code_text)
        line_canvas.pack(side=tk.LEFT, fill=tk.Y)

        vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.config(yscrollcommand=vsb.set)

        # ── 右侧面板: 图表渲染区
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # 图表工具栏
        ptb = ttk.Frame(right_frame)
        ptb.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(ptb, text="DPI:").pack(side=tk.LEFT, padx=4)
        self.dpi_var = tk.StringVar(value="100")
        dpi_c = ttk.Combobox(ptb, textvariable=self.dpi_var,
                             values=["80", "100", "120", "150"], width=6, state="readonly")
        dpi_c.pack(side=tk.LEFT)
        dpi_c.bind("<<ComboboxSelected>>", lambda e: self.run_code())
        ttk.Button(ptb, text="📥 保存图片", command=self.save_figure).pack(side=tk.RIGHT, padx=4)
        ttk.Button(ptb, text="🔧 清除", command=self.clear_figure).pack(side=tk.RIGHT, padx=2)

        # 图表画布
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Matplotlib 导航工具栏
        nav = NavigationToolbar2Tk(self.canvas, right_frame, pack_toolbar=False)
        nav.pack(fill=tk.X)

        # ── 状态栏
        self.status = ttk.Label(self.root, text="就绪 | 按 Ctrl+R 运行代码", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ────────────────── 核心逻辑 ──────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-r>", lambda e: self.run_code())
        self.root.bind("<Control-R>", lambda e: self.run_code())
        self.root.bind("<Control-s>", lambda e: self.save_script())
        self.root.bind("<Control-S>", lambda e: self.save_script())

    def _insert_demo_code(self):
        demo = '''# 示例: 正弦波 + 余弦波
import numpy as np

x = np.linspace(0, 4*np.pi, 500)
y1 = np.sin(x)
y2 = np.cos(x)

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y1, label='sin(x)', linewidth=2)
ax.plot(x, y2, label='cos(x)', linewidth=2, linestyle='--')
ax.set_title('正弦波与余弦波', fontsize=14)
ax.set_xlabel('x (rad)', fontsize=12)
ax.set_ylabel('y', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
'''
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", demo)
        self.status.config(text="已加载示例代码 | Ctrl+R 运行")

    def _on_preset_data(self, event=None):
        choice = self.data_var.get()
        snippets = {
            "正弦波": """# 正弦波数据
x = np.linspace(0, 4*np.pi, 500)
y = np.sin(x)

ax = fig.add_subplot(111)
ax.clear()
ax.plot(x, y, color='tab:blue', linewidth=2)
ax.set_title('正弦波', fontsize=14)
ax.set_xlabel('x')
ax.set_ylabel('sin(x)')
ax.grid(True, alpha=0.3)
fig.tight_layout()
""",
            "随机散点": """# 随机散点数据
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
""",
            "多组折线": """# 多组折线数据
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
""",
            "柱状图": """# 柱状图数据
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
""",
        }
        if choice in snippets:
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", snippets[choice])
            self.run_code()

    def run_code(self, event=None):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            self.status.config(text="错误: 代码为空")
            return

        self.status.config(text="正在运行...")
        self.root.update_idletasks()

        try:
            # 解析 DPI
            try:
                dpi = int(self.dpi_var.get())
            except ValueError:
                dpi = 100

            # 重建 Figure（应用 DPI）
            self.fig.clear()
            self.fig.set_dpi(dpi)

            # 执行用户代码，提供预定义变量
            exec_globals = {
                "np": np,
                "fig": self.fig,
                "ax": None,
            }
            exec(code, exec_globals)

            self.canvas.draw()
            self.status.config(text=f"运行成功 | DPI={dpi} | 按 Ctrl+R 重新运行")
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


# ────────────────── 入口 ──────────────────

def main():
    root = tk.Tk()
    app = CodePlotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
