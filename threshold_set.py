import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.signal import find_peaks
import glob, csv

# --- Load all profiles ---
files = sorted(glob.glob("/Users/msbl/Desktop/Hayden/kymograph_output/*.txt"))
results = {}

idx = 0

def load_profile(path):
    data = np.loadtxt(path, skiprows=1)
    return data[:, 0], data[:, 1]

# --- Set up figure ---
fig, ax = plt.subplots(figsize=(12, 5))
plt.subplots_adjust(bottom=0.4)

x, y = load_profile(files[idx])
line, = ax.plot(x, y, lw=1.5)
peak_scatter = ax.scatter([], [], color="red", zorder=5, marker="x", s=80)
thresh_line = ax.axhline(y.mean(), color="gray", linestyle="--")
title = ax.set_title("")
count_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=11)

# --- Widgets ---
ax_slider   = plt.axes([0.15, 0.20, 0.55, 0.03])
ax_slider_d = plt.axes([0.15, 0.13, 0.55, 0.03])
ax_prev     = plt.axes([0.15, 0.05, 0.12, 0.05])
ax_confirm  = plt.axes([0.44, 0.05, 0.12, 0.05])
ax_next     = plt.axes([0.60, 0.05, 0.12, 0.05])

slider   = Slider(ax_slider,   "Threshold",    y.min(), y.max(), valinit=y.mean())
slider_d = Slider(ax_slider_d, "Min distance", 1, 100,           valinit=10, valstep=1)
btn_prev    = Button(ax_prev,    "← Prev")
btn_confirm = Button(ax_confirm, "Confirm ✓")
btn_next    = Button(ax_next,    "Next →")

def update_plot(x, y, threshold, min_dist):
    peaks, _ = find_peaks(y, height=threshold, distance=int(min_dist))
    peak_scatter.set_offsets(np.c_[x[peaks], y[peaks]])
    thresh_line.set_ydata([threshold, threshold])
    count_text.set_text(f"Peaks: {len(peaks)}")
    title.set_text(f"[{idx+1}/{len(files)}]  {files[idx]}")
    fig.canvas.draw_idle()
    return len(peaks)

def load_and_refresh(new_idx):
    global idx, x, y
    idx = new_idx
    x, y = load_profile(files[idx])
    line.set_xdata(x)
    line.set_ydata(y)

    # Set y limits based on signal range with a small padding
    padding = (y.max() - y.min()) * 0.1
    ax.set_ylim(y.min() - padding, y.max() + padding)
    ax.set_xlim(x.min(), x.max())

    # Reset threshold slider range to this profile
    slider.valmin = y.min()
    slider.valmax = y.max()
    slider.set_val(y.mean())
    ax_slider.set_xlim(y.min(), y.max())

    update_plot(x, y, y.mean(), slider_d.val)

slider.on_changed(lambda val: update_plot(x, y, val, slider_d.val))
slider_d.on_changed(lambda val: update_plot(x, y, slider.val, val))

def on_confirm(event):
    results[files[idx]] = update_plot(x, y, slider.val, slider_d.val)
    print(f"Saved: {files[idx]}  →  {results[files[idx]]} peaks")

def on_next(event):
    if idx + 1 < len(files):
        load_and_refresh(idx + 1)

def on_prev(event):
    if idx - 1 >= 0:
        load_and_refresh(idx - 1)

btn_confirm.on_clicked(on_confirm)
btn_next.on_clicked(on_next)
btn_prev.on_clicked(on_prev)

load_and_refresh(0)
plt.show()

# --- Save results after closing window ---
with open("peak_counts.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["file", "peak_count"])
    for fname, count in results.items():
        writer.writerow([fname, count])

print("Results saved to peak_counts.csv")
