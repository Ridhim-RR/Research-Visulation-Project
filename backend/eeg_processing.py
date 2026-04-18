from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from scipy.io import loadmat

matplotlib.use("Agg")


@dataclass
class ProcessingSettings:
    fs: int = 512
    twndw: float = 1.0
    frame_index: int = 1
    nj: int = 8
    freq_max_hz: float = 64.0
    img_n: int = 900

    def validate(self) -> None:
        if self.fs <= 0:
            raise ValueError("Fs must be greater than 0.")
        if self.twndw <= 0:
            raise ValueError("Twndw must be greater than 0.")
        if self.frame_index <= 0:
            raise ValueError("frameIndex must be at least 1.")
        if self.nj <= 0:
            raise ValueError("Nj must be greater than 0.")
        if self.freq_max_hz <= 0:
            raise ValueError("freqMaxHz must be greater than 0.")
        if self.img_n < 64 or self.img_n > 1500:
            raise ValueError("imgN must be between 64 and 1500.")


def _first_valid_matrix_variable(mat_dict: dict[str, Any]) -> tuple[str, np.ndarray]:
    for key, value in mat_dict.items():
        if key.startswith("__"):
            continue
        arr = np.asarray(value)
        if arr.ndim == 2 and arr.size > 0 and np.issubdtype(arr.dtype, np.number):
            return key, arr.astype(np.float64)
    raise ValueError("No valid 2D numeric data variable was found in the MAT file.")


def load_mat_matrix(file_bytes: bytes) -> tuple[str, np.ndarray]:
    try:
        mat_dict = loadmat(BytesIO(file_bytes), squeeze_me=False, struct_as_record=False)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to parse MAT file: {exc}") from exc

    return _first_valid_matrix_variable(mat_dict)


def mnproduce3_general(aa: np.ndarray, ni: int, nj: int) -> np.ndarray:
    a2 = aa / nj

    x = np.zeros((2, nj), dtype=np.float64)
    for i in range(1, nj + 1):
        x[0, i - 1] = nj - i + 1
        x[1, i - 1] = i - 1

    out_segments: list[np.ndarray] = []

    for i in range(ni):
        if i < ni - 1:
            z = np.column_stack((a2[:, i], a2[:, i + 1])) @ x
        else:
            z = np.column_stack((a2[:, i], a2[:, 0])) @ x
        out_segments.append(z)

    return np.concatenate(out_segments, axis=1)


def semani_polar_cell_raster(m: np.ndarray, img_n: int) -> tuple[np.ndarray, np.ndarray]:
    nr, ntheta = m.shape

    xv = np.linspace(-1, 1, img_n)
    yv = np.linspace(-1, 1, img_n)

    xq, yq = np.meshgrid(xv, yv)
    th = np.arctan2(yq, xq)
    r = np.sqrt(xq**2 + yq**2)

    th = np.where(th < 0, th + 2 * np.pi, th)

    inside = r <= 1

    layer_idx = np.floor(r * nr).astype(int)
    layer_idx = np.clip(layer_idx, 0, nr - 1)

    seg_idx = np.floor((th / (2 * np.pi)) * ntheta).astype(int)
    seg_idx = np.clip(seg_idx, 0, ntheta - 1)

    img = np.full_like(r, np.nan, dtype=np.float64)
    alpha = np.zeros_like(r, dtype=np.float64)

    img[inside] = m[layer_idx[inside], seg_idx[inside]]
    alpha[inside] = 1.0

    return img, alpha


def colorzmnpalet() -> ListedColormap:
    nseg = 250
    coolfrac = 0.95 / 2
    autumnfrac = 0.95 / 2
    zerofrac = 0.1 / 2

    ncoolrange = int(np.floor(nseg * coolfrac))
    nautumnrange = int(np.floor(nseg * autumnfrac))
    nzerorange = int(np.floor(nseg * zerofrac))

    coolcolors = plt.get_cmap("cool")(np.linspace(0, 1, max(ncoolrange, 1)))[:, :3]
    autumncolors = plt.get_cmap("autumn")(np.linspace(0, 1, max(nautumnrange, 1)))[:, :3]
    zerocolors = np.ones((max(nzerorange, 1), 3))

    grirnk = np.vstack([autumncolors, zerocolors, coolcolors])
    return ListedColormap(grirnk)


def plot_cartesian_grid(ax: plt.Axes, radial_axis: np.ndarray, n_ch: int) -> None:
    main_angles = np.linspace(0, 360, n_ch + 1)
    for ang in main_angles:
        ax.axvline(ang, linestyle=":", color=(0.35, 0.35, 0.35), linewidth=0.9)

    n_r = 6
    r_vals = np.linspace(float(np.min(radial_axis)), float(np.max(radial_axis)), n_r)
    for rv in r_vals:
        ax.axhline(rv, linestyle=":", color=(0.55, 0.55, 0.55), linewidth=0.6)


def plot_polar_guides(ax: plt.Axes, r_max: float, sf: int, n_circles: int, n_ch: int) -> None:
    th = np.linspace(0, 2 * np.pi, 500)

    for k in range(1, n_circles + 1):
        rr = r_max * k / n_circles
        ax.plot(rr * np.cos(th), rr * np.sin(th), ":", color=(0.45, 0.45, 0.45), linewidth=0.7)

    angs_all = np.linspace(0, 2 * np.pi, sf + 1)
    for ang in angs_all:
        ax.plot([0, r_max * np.cos(ang)], [0, r_max * np.sin(ang)], "-", color=(0.10, 0.10, 0.10), linewidth=0.15)

    angs_main = np.linspace(0, 2 * np.pi, n_ch + 1)
    for ang in angs_main:
        ax.plot([0, r_max * np.cos(ang)], [0, r_max * np.sin(ang)], ":", color=(0.20, 0.20, 0.20), linewidth=1.0)

    label_angles_deg = np.arange(0, 360, 30)
    r_text = 1.05 * r_max

    for ang_deg in label_angles_deg:
        ang_rad = np.deg2rad(ang_deg)
        xt = r_text * np.cos(ang_rad)
        yt = r_text * np.sin(ang_rad)
        ax.text(
            xt,
            yt,
            f"{ang_deg}°",
            ha="center",
            va="center",
            fontsize=8,
            color=(0, 0, 0.8),
            fontweight="bold",
        )


def _to_base64_png(fig: plt.Figure) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    png_bytes = buf.read()
    buf.close()
    return base64.b64encode(png_bytes).decode("ascii")


def process_eeg_matrix(x_raw: np.ndarray, settings: ProcessingSettings, source_name: str) -> dict[str, Any]:
    settings.validate()

    if x_raw.ndim != 2:
        raise ValueError("Input EEG matrix must be 2D with shape [nSamples, nChannels].")

    n_samples, n_ch = x_raw.shape
    if n_samples < 2 or n_ch < 1:
        raise ValueError("Input EEG matrix must have at least 2 samples and 1 channel.")

    valx = x_raw.astype(np.float64)

    mx_all = np.max(np.abs(valx))
    if mx_all < np.finfo(float).eps:
        mx_all = 1.0
    valx = valx / mx_all

    mu_all = np.mean(valx)
    sd_all = np.std(valx)
    if sd_all < np.finfo(float).eps:
        sd_all = 1.0
    valxx = (valx - mu_all) / sd_all

    vmin = float(np.min(valxx))
    vmax = float(np.max(valxx))
    if abs(vmax - vmin) < np.finfo(float).eps:
        valxx = np.zeros_like(valxx)
    else:
        valxx = (valxx - vmin) / (vmax - vmin)

    valxx = valxx - np.mean(valxx)
    x = valxx.copy()

    for k in range(n_ch):
        mxk = np.max(np.abs(x[:, k]))
        if mxk < np.finfo(float).eps:
            mxk = 1.0
        x[:, k] = x[:, k] / mxk

    kf = int(round(settings.twndw * settings.fs))
    if kf < 2:
        raise ValueError("Window size is too small. Increase Twndw or Fs.")

    n_frames = n_samples // kf
    if n_frames < 1:
        raise ValueError("The selected analysis window is longer than the signal.")

    frame_index = max(1, min(settings.frame_index, n_frames))
    idx1 = (frame_index - 1) * kf
    idx2 = frame_index * kf

    xw = x[idx1:idx2, :]
    t_local = np.arange(kf, dtype=np.float64) / settings.fs + (frame_index - 1) * settings.twndw

    sf = n_ch * settings.nj
    btime = mnproduce3_general(xw, n_ch, settings.nj)

    theta_centers_deg = np.linspace(0, 360, sf + 1, dtype=np.float64)[:-1]

    nf = sf
    epsilon = 1e-10

    half_bins = int(np.ceil(kf / 2) + 1)
    ppenclog = np.zeros((half_bins, nf), dtype=np.float64)

    for nn in range(nf):
        pencere = btime[:, nn].reshape(-1)
        pencerex_fft = np.fft.fft(pencere, kf).reshape(-1)
        pencere_fft = np.abs(pencerex_fft)

        tmp2x = pencere_fft[:half_bins] ** 2
        if tmp2x.size > 2:
            tmp2x[1:-1] = 2 * tmp2x[1:-1]

        tmp2x = tmp2x / (kf * settings.fs)
        tmpdb = 10 * np.log10(tmp2x + np.finfo(float).eps)
        ppenclog[:, nn] = tmpdb

    ppenclog = ppenclog - np.max(ppenclog)

    f_axis = (settings.fs / kf) * np.arange(half_bins, dtype=np.float64)
    freq_mask = f_axis <= settings.freq_max_hz

    f_plot = f_axis[freq_mask]
    freq_data = ppenclog[freq_mask, :]

    time_polar_img, time_alpha = semani_polar_cell_raster(btime, settings.img_n)
    freq_polar_img, freq_alpha = semani_polar_cell_raster(freq_data, settings.img_n)

    semani_img_b64, channels_img_b64 = _build_figures(
        frame_index=frame_index,
        twndw=settings.twndw,
        theta_centers_deg=theta_centers_deg,
        t_local=t_local,
        btime=btime,
        f_plot=f_plot,
        freq_data=freq_data,
        time_polar_img=time_polar_img,
        time_alpha=time_alpha,
        freq_polar_img=freq_polar_img,
        freq_alpha=freq_alpha,
        xw=xw,
        n_ch=n_ch,
        sf=sf,
    )

    return {
        "metadata": {
            "sourceVariable": source_name,
            "nSamples": int(n_samples),
            "nChannels": int(n_ch),
            "frameIndexUsed": int(frame_index),
            "nFrames": int(n_frames),
            "Kf": int(kf),
            "Sf": int(sf),
            "frequencyBins": int(f_plot.size),
        },
        "settings": {
            "Fs": int(settings.fs),
            "Twndw": float(settings.twndw),
            "frameIndex": int(frame_index),
            "Nj": int(settings.nj),
            "freqMaxHz": float(settings.freq_max_hz),
            "imgN": int(settings.img_n),
        },
        "numeric": {
            "thetaCentersDeg": theta_centers_deg.tolist(),
            "tLocal": t_local.tolist(),
            "fPlot": f_plot.tolist(),
            "Btime": btime.tolist(),
            "freqData": freq_data.tolist(),
            "timePolarImg": time_polar_img.tolist(),
            "timeAlpha": time_alpha.tolist(),
            "freqPolarImg": freq_polar_img.tolist(),
            "freqAlpha": freq_alpha.tolist(),
            "Xw": xw.tolist(),
        },
        "images": {
            "semaniFigurePngBase64": semani_img_b64,
            "channelsFigurePngBase64": channels_img_b64,
        },
    }


def _build_figures(
    *,
    frame_index: int,
    twndw: float,
    theta_centers_deg: np.ndarray,
    t_local: np.ndarray,
    btime: np.ndarray,
    f_plot: np.ndarray,
    freq_data: np.ndarray,
    time_polar_img: np.ndarray,
    time_alpha: np.ndarray,
    freq_polar_img: np.ndarray,
    freq_alpha: np.ndarray,
    xw: np.ndarray,
    n_ch: int,
    sf: int,
) -> tuple[str, str]:
    grirnk = colorzmnpalet()

    fig1 = plt.figure(figsize=(16, 10), facecolor="white")

    ax1 = fig1.add_subplot(2, 2, 1)
    im1 = ax1.imshow(
        btime,
        aspect="auto",
        origin="lower",
        extent=[theta_centers_deg[0], theta_centers_deg[-1], t_local[0], t_local[-1]],
        cmap=grirnk,
        vmin=-1,
        vmax=1,
    )
    ax1.set_xlabel("Segment angle (deg)")
    ax1.set_ylabel("Time (s)")
    ax1.set_title(f"EEG Semani - Time Cartesian | Frame {frame_index}")
    plot_cartesian_grid(ax1, t_local, n_ch)
    cbar1 = fig1.colorbar(im1, ax=ax1)
    cbar1.set_label("Amplitude")

    ax2 = fig1.add_subplot(2, 2, 2)
    r_max_time = twndw
    im2 = ax2.imshow(
        time_polar_img,
        extent=[-r_max_time, r_max_time, -r_max_time, r_max_time],
        origin="lower",
        cmap=grirnk,
        vmin=-1,
        vmax=1,
    )
    im2.set_alpha(time_alpha)
    ax2.set_aspect("equal", adjustable="box")
    ax2.set_xlim(-1.15 * r_max_time, 1.15 * r_max_time)
    ax2.set_ylim(-1.15 * r_max_time, 1.15 * r_max_time)
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_title(f"EEG Semani - Time Polar 2D | Frame {frame_index}")
    plot_polar_guides(ax2, r_max_time, sf, 6, n_ch)
    cbar2 = fig1.colorbar(im2, ax=ax2)
    cbar2.set_label("Amplitude")

    ax3 = fig1.add_subplot(2, 2, 3)
    fmax = float(max(np.max(f_plot), np.finfo(float).eps))
    im3 = ax3.imshow(
        freq_data,
        aspect="auto",
        origin="lower",
        extent=[theta_centers_deg[0], theta_centers_deg[-1], f_plot[0], f_plot[-1] if f_plot.size > 0 else 0],
        cmap="viridis",
        vmin=-50,
        vmax=0,
    )
    ax3.set_xlabel("Segment angle (deg)")
    ax3.set_ylabel("Frequency (Hz)")
    ax3.set_title(f"EEG Semani - Frequency Cartesian | Frame {frame_index}")
    plot_cartesian_grid(ax3, f_plot if f_plot.size > 0 else np.array([0, fmax]), n_ch)
    cbar3 = fig1.colorbar(im3, ax=ax3)
    cbar3.set_label("Log power")

    ax4 = fig1.add_subplot(2, 2, 4)
    r_max_freq = float(np.max(f_plot)) if f_plot.size > 0 else 1.0
    im4 = ax4.imshow(
        freq_polar_img,
        extent=[-r_max_freq, r_max_freq, -r_max_freq, r_max_freq],
        origin="lower",
        cmap="viridis",
        vmin=-50,
        vmax=0,
    )
    im4.set_alpha(freq_alpha)
    ax4.set_aspect("equal", adjustable="box")
    ax4.set_xlim(-1.15 * r_max_freq, 1.15 * r_max_freq)
    ax4.set_ylim(-1.15 * r_max_freq, 1.15 * r_max_freq)
    ax4.set_xlabel("X")
    ax4.set_ylabel("Y")
    ax4.set_title(f"EEG Semani - Frequency Polar 2D | Frame {frame_index}")
    plot_polar_guides(ax4, r_max_freq, sf, 6, n_ch)
    cbar4 = fig1.colorbar(im4, ax=ax4)
    cbar4.set_label("Relative dB")

    fig1.tight_layout()
    semani_img_b64 = _to_base64_png(fig1)
    plt.close(fig1)

    fig2_height = min(24, max(6, n_ch * 1.2))
    fig2, axes = plt.subplots(n_ch, 1, figsize=(12, fig2_height), facecolor="white", squeeze=False)

    for idx in range(n_ch):
        ax = axes[idx, 0]
        ax.plot(t_local, xw[:, idx], "k", linewidth=0.8)
        ax.set_ylim([-1.1, 1.1])
        ax.grid(True)
        ax.set_title(f"Channel {idx + 1} - CH{idx + 1}")
        if idx == n_ch - 1:
            ax.set_xlabel("Time (s)")

    fig2.tight_layout()
    channels_img_b64 = _to_base64_png(fig2)
    plt.close(fig2)

    return semani_img_b64, channels_img_b64


def process_eeg_mat_bytes(file_bytes: bytes, settings: ProcessingSettings) -> dict[str, Any]:
    source_name, x_raw = load_mat_matrix(file_bytes)
    return process_eeg_matrix(x_raw=x_raw, settings=settings, source_name=source_name)
