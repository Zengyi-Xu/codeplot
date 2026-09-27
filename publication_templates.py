"""Publication-quality plot templates for CodePlot.

Design goals (fixing the three most common layout problems):
- Fonts too small  -> fixed physical figure size (3.5 in = journal single
  column) combined with explicit font sizes, so text-to-plot proportions
  are deterministic no matter where the figure is embedded.
- Overlapping parts -> constrained layout, inward ticks, legends without
  frames, and y-limits that leave headroom for annotations.
- Missing fonts    -> svg.fonttype='path' stores text as vector outlines
  (SVG never depends on installed fonts), pdf.fonttype=42 embeds TrueType;
  the font list falls back from Arial to common CJK fonts.

Every template is self-contained: the style preamble is repeated in each
code string so a template can run standalone in the CodePlot editor.
"""

_STYLE = """# -- Journal style (fixed size + explicit fonts: no shrink/overlap/missing fonts)
plt.rcParams.update({
    'font.family': 'sans-serif',
    # matplotlib uses the FIRST available font only (no per-glyph fallback):
    # for Chinese labels, move 'Microsoft YaHei' to the front of this list.
    'font.sans-serif': ['Arial', 'Helvetica', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'font.size': 10, 'axes.titlesize': 11, 'axes.labelsize': 10.5,
    'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5, 'legend.fontsize': 9,
    'axes.linewidth': 0.9, 'lines.linewidth': 1.6, 'lines.markersize': 5.5,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'xtick.top': True, 'ytick.right': True,
    'xtick.major.size': 3.5, 'ytick.major.size': 3.5,
    'xtick.minor.size': 2.0, 'ytick.minor.size': 2.0,
    'legend.frameon': False,
    'axes.unicode_minus': False,
    'svg.fonttype': 'path',   # SVG: text saved as outlines -> fonts never missing
    'pdf.fonttype': 42,       # PDF: embed TrueType fonts
})
C = ['#0072B2', '#D55E00', '#009E73', '#E69F00', '#CC79A7', '#56B4E9']  # Okabe-Ito palette

"""

PUBLICATION_TEMPLATES = {
    "Publication": {
        "Line Plot (Journal)": {
            "desc": "Single-column line plot with inward ticks, minor ticks and clean legend.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

np.random.seed(7)
x = np.linspace(0, 10, 300)
y1 = np.exp(-x / 3.0) + 0.012 * np.random.randn(x.size)
y2 = 0.8 * np.exp(-x / 5.0) + 0.012 * np.random.randn(x.size)

ax.plot(x, y1, color=C[0], label='Channel A')
ax.plot(x, y2, color=C[1], ls='--', label='Channel B')
ax.set_xlabel('Time (ns)')
ax.set_ylabel('Amplitude (a.u.)')
ax.set_xlim(0, 10)
ax.set_ylim(-0.08, 1.12)
ax.minorticks_on()
ax.legend(loc='upper right', handlelength=1.8)
""",
        },
        "BER Curve (semilog)": {
            "desc": "BER vs OSNR on log scale with FEC threshold line — classic optical-comm figure.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

osnr = np.arange(10, 22, 1.5)
ber_btb = 0.4 * np.exp(-(osnr - 10) / 1.9)
ber_80km = 0.4 * np.exp(-(osnr - 10) / 3.1) + 4e-5

ax.semilogy(osnr, ber_btb, '-o', color=C[0], mfc='white', mew=1.3,
            label='Back-to-back')
ax.semilogy(osnr, ber_80km, '-s', color=C[1], mfc='white', mew=1.3,
            label='After 80 km SSMF')
ax.axhline(3.8e-3, color='0.35', ls=':', lw=1.2)
ax.text(10.3, 6e-3, 'HD-FEC limit 3.8$\\\\times$10$^{-3}$',
        fontsize=8.5, color='0.3')
ax.set_xlabel('OSNR (dB)')
ax.set_ylabel('BER')
ax.set_xlim(10, 21)
ax.set_ylim(1e-5, 1.5)
ax.grid(True, which='major', ls=':', lw=0.5, alpha=0.6)
ax.legend(loc='lower left')
""",
        },
        "Spectrum / Frequency Response": {
            "desc": "Power spectrum with -3 dB bandwidth annotation and shaded roll-off region.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

f = np.linspace(0, 40, 2000)  # GHz
resp = np.exp(-((f - 12) / 9.0) ** 4)          # super-Gaussian passband
noise = 10 ** (-38 / 10) * (1 + 0.15 * np.random.default_rng(3).standard_normal(f.size))
p_dbm = 10 * np.log10(resp ** 2 * 1e-3 + np.abs(noise) * 1e-3) + 30

ax.plot(f, p_dbm, color=C[0], lw=1.4)
ax.axhline(-3, color='0.35', ls=':', lw=1.1)
ax.axvspan(24, 40, color=C[3], alpha=0.12, lw=0)
ax.text(31.5, -9, 'roll-off', ha='center', fontsize=8.5, color='0.35')
ax.annotate('-3 dB', xy=(6.2, -3), xytext=(3.0, -10),
            fontsize=8.5, color='0.25',
            arrowprops=dict(arrowstyle='->', color='0.25', lw=0.8))
ax.set_xlabel('Frequency (GHz)')
ax.set_ylabel('Power (dBm)')
ax.set_xlim(0, 40)
ax.set_ylim(-40, 8)
""",
        },
        "Zoom Inset": {
            "desc": "Main curve with a magnified inset linked by zoom indicator lines.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

x = np.linspace(0, 100, 2000)
rng = np.random.default_rng(5)
y = np.sinc((x - 72) / 8.0) + 0.03 * np.sin(x * 2.1) * np.exp(-((x - 72) / 30) ** 2)
y = y + 0.008 * rng.standard_normal(x.size)

ax.plot(x, y, color=C[0], lw=1.2)
ax.set_xlabel('Wavelength detuning (pm)')
ax.set_ylabel('Transmission (a.u.)')
ax.set_xlim(0, 100)
ax.minorticks_on()

# inset on the left, away from the peak, so its tick labels hit empty space
axins = ax.inset_axes([0.13, 0.50, 0.40, 0.42])
axins.plot(x, y, color=C[0], lw=1.0)
axins.set_xlim(68, 76)
axins.set_ylim(0.88, 1.04)
axins.tick_params(labelsize=8)
axins.minorticks_on()
ax.indicate_inset_zoom(axins, edgecolor='0.35', lw=0.9)
""",
        },
        "Dual Y-Axis": {
            "desc": "Transmission + phase vs wavelength with color-matched left/right axes.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

wl = np.linspace(1530, 1560, 400)
notch = 12 / (1 + ((wl - 1545.0) / 0.6) ** 2)
trans = -1.5 - notch
phase = 2.2 * np.arctan((wl - 1545.0) / 0.6)

ax.plot(wl, trans, color=C[0], label='Transmission')
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('Transmission (dB)', color=C[0])
ax.tick_params(axis='y', colors=C[0], right=False)
ax.set_xlim(1530, 1560)
ax.set_ylim(-15, 0)

ax2 = ax.twinx()
ax2.plot(wl, phase, color=C[1], ls='--', label='Phase')
ax2.set_ylabel('Phase (rad)', color=C[1])
ax2.tick_params(axis='y', colors=C[1], direction='in')
ax2.set_ylim(-4, 4)
ax2.spines['right'].set_color(C[1])
ax.spines['left'].set_color(C[0])

lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [l.get_label() for l in lines], loc='center right')
""",
        },
        "Heatmap + Colorbar": {
            "desc": "2-D map (e.g. BER/SNR surface) with right-sized colorbar, no squeezing.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.8)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

xx = np.linspace(-3, 3, 160)
yy = np.linspace(-3, 3, 120)
X, Y = np.meshgrid(xx, yy)
Z = np.exp(-(X ** 2 + Y ** 2)) + 0.6 * np.exp(-((X - 1.2) ** 2 + (Y + 1) ** 2))

im = ax.imshow(Z, extent=[-3, 3, -3, 3], origin='lower',
               cmap='viridis', aspect='auto')
ax.set_xlabel('Frequency offset (GHz)')
ax.set_ylabel('Launch power (dBm)')
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('Normalized intensity')
cbar.ax.tick_params(labelsize=9)
""",
        },
        "Bar + Error Bars": {
            "desc": "Bar chart with error bars and value labels that never clip at the top.",
            "code": _STYLE + """fig.set_size_inches(3.5, 2.6)
fig.set_constrained_layout(True)
ax = fig.add_subplot(111)

labels = ['16-QAM', '32-QAM', '64-QAM', '128-QAM']
means = [12.4, 15.1, 18.6, 21.3]
errs = [0.4, 0.6, 0.8, 1.1]

bars = ax.bar(labels, means, yerr=errs, capsize=3.5, width=0.58,
              color=[C[0], C[2], C[3], C[1]],
              edgecolor='black', linewidth=0.8,
              error_kw=dict(lw=1.1, capthick=1.1))
ax.bar_label(bars, fmt='%.1f', padding=2.5, fontsize=9)
ax.set_ylabel('Required OSNR (dB)')
ax.set_ylim(0, max(np.array(means) + np.array(errs)) * 1.22)
ax.tick_params(axis='x', length=0)
ax.grid(True, axis='y', ls=':', lw=0.5, alpha=0.6)
ax.set_axisbelow(True)
""",
        },
    },
}
