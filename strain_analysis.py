import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from scipy.ndimage import gaussian_filter

# =============================================================
# CONFIG
# =============================================================
STACK_PATH   = "/Users/msbl/Desktop/strain_test/awesome_heart_pumping1.tif"
OUTPUT_DIR   = "/Users/msbl/Desktop/strain_test/test5_heart_big_win/"
SMOOTH_SIGMA = 2      # gaussian smoothing on flow before computing strain
QUIVER_STEP  = 15     # plot every Nth vector in quiver plot
FARNEBACK = dict(     # optical flow parameters
    pyr_scale  = 0.5,
    levels     = 3,
    winsize    = 31,  # larger = smoother, less spatial detail
    iterations = 3,
    poly_n     = 5,
    poly_sigma = 1.2,
    flags      = 0
)

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================
# LOAD STACK
# =============================================================
stack = io.imread(STACK_PATH).astype(np.float32)
print(f"Loaded stack: {stack.shape}")  # expected (frames, height, width)
n_frames, height, width = stack.shape

def norm255(img):
    mn, mx = img.min(), img.max()
    if mx == mn:
        return np.zeros_like(img, dtype=np.uint8)
    return ((img - mn) / (mx - mn) * 255).astype(np.uint8)

# =============================================================
# COMPUTE OPTICAL FLOW FOR EVERY CONSECUTIVE FRAME PAIR
# =============================================================
u_stack = np.zeros((n_frames - 1, height, width), dtype=np.float32)
v_stack = np.zeros((n_frames - 1, height, width), dtype=np.float32)

for i in range(n_frames - 1):
    f1 = norm255(stack[i])
    f2 = norm255(stack[i + 1])
    flow = cv2.calcOpticalFlowFarneback(f1, f2, None, **FARNEBACK)
    u_stack[i] = flow[..., 0]   # x displacement
    v_stack[i] = flow[..., 1]   # y displacement
    print(f"  Frame {i+1}/{n_frames-1}", end="\r")

print("\nFlow computation done.")

# =============================================================
# SPATIAL SUMMARY MAPS
# =============================================================
# Displacement magnitude per frame, then average
magnitude    = np.sqrt(u_stack**2 + v_stack**2)
mean_mag     = magnitude.mean(axis=0)
max_mag      = magnitude.max(axis=0)

# Mean flow field, smoothed before strain computation
u_mean = gaussian_filter(u_stack.mean(axis=0), sigma=SMOOTH_SIGMA)
v_mean = gaussian_filter(v_stack.mean(axis=0), sigma=SMOOTH_SIGMA)

# Strain tensor components from mean flow
exx = np.gradient(u_mean, axis=1)          # normal strain x (du/dx)
eyy = np.gradient(v_mean, axis=0)          # normal strain y (dv/dy)
exy = 0.5 * (np.gradient(u_mean, axis=0)   # shear strain
           + np.gradient(v_mean, axis=1))

# Max principal strain
principal = np.sqrt(((exx - eyy) / 2)**2 + exy**2)

# Dilation (area strain)
dilation = exx + eyy

# =============================================================
# TEMPORAL SUMMARY (per-frame average displacement)
# =============================================================
mean_mag_per_frame = magnitude.mean(axis=(1, 2))

# =============================================================
# PLOT 1: Spatial maps
# =============================================================
ref = norm255(stack[0])

# Quiver subsampling
y_q, x_q = np.mgrid[0:height:QUIVER_STEP, 0:width:QUIVER_STEP]
u_q = u_mean[::QUIVER_STEP, ::QUIVER_STEP]
v_q = v_mean[::QUIVER_STEP, ::QUIVER_STEP]

fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.suptitle("Spatial motion and strain maps", fontsize=14)

def symclim(arr, pct=99):
    lim = np.percentile(np.abs(arr), pct)
    return -lim, lim

# Mean displacement magnitude
im0 = axes[0, 0].imshow(mean_mag, cmap="hot")
axes[0, 0].set_title("Mean displacement magnitude (px/frame)")
plt.colorbar(im0, ax=axes[0, 0])

# Peak displacement magnitude
im1 = axes[0, 1].imshow(max_mag, cmap="hot")
axes[0, 1].set_title("Peak displacement magnitude (px/frame)")
plt.colorbar(im1, ax=axes[0, 1])

# Displacement vector field
axes[0, 2].imshow(ref, cmap="gray")
axes[0, 2].quiver(x_q, y_q, u_q, v_q,
                  color="red", scale=20, width=0.003, headwidth=3)
axes[0, 2].set_title("Mean displacement field")

# Normal strain x
vmin, vmax = symclim(exx)
im3 = axes[1, 0].imshow(exx, cmap="RdBu_r", vmin=vmin, vmax=vmax)
axes[1, 0].set_title("Normal strain exx (du/dx)")
plt.colorbar(im3, ax=axes[1, 0])

# Normal strain y
vmin, vmax = symclim(eyy)
im4 = axes[1, 1].imshow(eyy, cmap="RdBu_r", vmin=vmin, vmax=vmax)
axes[1, 1].set_title("Normal strain eyy (dv/dy)")
plt.colorbar(im4, ax=axes[1, 1])

# Max principal strain
im5 = axes[1, 2].imshow(principal, cmap="hot")
axes[1, 2].set_title("Max principal strain")
plt.colorbar(im5, ax=axes[1, 2])

for ax in axes.flat:
    ax.axis("off")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/spatial_maps.png", dpi=150, bbox_inches="tight")
plt.show()

# =============================================================
# PLOT 2: Dilation map (area strain)
# =============================================================
fig, ax = plt.subplots(figsize=(6, 5))
vmin, vmax = symclim(dilation)
im = ax.imshow(dilation, cmap="RdBu_r", vmin=vmin, vmax=vmax)
ax.set_title("Dilation (exx + eyy)\nred = expansion, blue = compression")
ax.axis("off")
plt.colorbar(im, ax=ax)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/dilation_map.png", dpi=150, bbox_inches="tight")
plt.show()

# =============================================================
# PLOT 3: Mean displacement over time
# =============================================================
fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(mean_mag_per_frame, lw=1.5)
ax.set_xlabel("Frame")
ax.set_ylabel("Mean displacement (px/frame)")
ax.set_title("Tissue motion over time")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/displacement_over_time.png", dpi=150, bbox_inches="tight")
plt.show()

# =============================================================
# SAVE RAW ARRAYS for further analysis
# =============================================================
np.save(f"{OUTPUT_DIR}/u_stack.npy", u_stack)
np.save(f"{OUTPUT_DIR}/v_stack.npy", v_stack)
np.save(f"{OUTPUT_DIR}/mean_mag.npy", mean_mag)
np.save(f"{OUTPUT_DIR}/principal_strain.npy", principal)
np.save(f"{OUTPUT_DIR}/dilation.npy", dilation)

print(f"All outputs saved to {OUTPUT_DIR}/")
