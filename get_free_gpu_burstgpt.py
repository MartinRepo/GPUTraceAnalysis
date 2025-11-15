import math
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


CSV_FILES: List[str] = [
    "datasets/burstgpt_data/BurstGPT_without_fails_1.csv",  # Region A
    "datasets/burstgpt_data/BurstGPT_without_fails_2.csv",  # Region B
]
REGION_NAMES: Dict[str, str] = {
    "datasets/burstgpt_data/BurstGPT_without_fails_1.csv": "Region-A",
    "datasets/burstgpt_data/BurstGPT_without_fails_2.csv": "Region-B",
}
TIME_UNIT_SECONDS: int = 3600
TOKENS_PER_GPU_PER_HOUR: float = 4_000_00
USE_TOTAL_TOKENS: bool = False
OUTPUT_DIR: str = "results/burstgpt"
PLOT_FORMAT: str = "png"

START_DATE = "2024-10-01 00:00:00"
ANALYSIS_START_TIME: str | None = "2024-10-21 00:00:00"
ANALYSIS_END_TIME: str | None = "2024-10-25 23:00:00"


def compute_gpu_usage_for_region(
    csv_path: Path,
    tokens_per_gpu_per_time_unit: float,
    time_unit_seconds: int = TIME_UNIT_SECONDS,
    region_name: str | None = None,
) -> pd.DataFrame:
    if region_name is None:
        region_name = csv_path.stem

    print(f"\n=== Processing region: {region_name} ({csv_path}) ===")
    df = pd.read_csv(csv_path)

    df["Timestamp"] = pd.to_numeric(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])

    if USE_TOTAL_TOKENS:
        df["io_tokens"] = df["Total tokens"]
    else:
        df["io_tokens"] = df["Request tokens"] + df["Response tokens"]

    df["time_unit_index"] = (df["Timestamp"] // time_unit_seconds).astype(int)

    grouped = df.groupby("time_unit_index")["io_tokens"].sum()

    full_index = range(int(grouped.index.min()), int(grouped.index.max()) + 1)
    grouped = grouped.reindex(full_index, fill_value=0).sort_index()

    gpu_required = np.ceil(grouped / tokens_per_gpu_per_time_unit)

    peak_gpu_required = gpu_required.max()
    total_gpus = math.ceil(peak_gpu_required)

    print(f"Peak GPU required (float) for {region_name}: {peak_gpu_required:.3f}")
    print(f"Total GPUs allocated for {region_name}: {total_gpus}")

    free_gpus = total_gpus - gpu_required

    real_seconds = [i * time_unit_seconds for i in grouped.index]
    timestamps = pd.to_datetime(
        real_seconds,
        unit="s",
        origin=pd.Timestamp(START_DATE),
    )

    result = pd.DataFrame(
        {
            "timestamp": timestamps,
            "total_tokens_sum": grouped.values,
            "gpu_required": gpu_required.values,
            "total_gpus": total_gpus,
            "free_gpus": free_gpus.values,
        }
    )

    return result


def plot_region(df: pd.DataFrame, region_name: str, out_dir: Path) -> None:
    if df.empty:
        print(f"[WARN] No data in analysis window for {region_name}, skip plotting.")
        return

    fig = plt.figure(figsize=(14, 6))

    plt.plot(
        df["timestamp"],
        df["gpu_required"],
        label="Required GPUs",
        color="blue",
    )

    total_gpus = df["total_gpus"].iloc[0]
    plt.plot(
        df["timestamp"],
        [total_gpus] * len(df),
        label="Total GPUs",
        color="orange",
    )

    plt.plot(
        df["timestamp"],
        df["free_gpus"],
        label="Free GPUs",
        color="green",
    )

    plt.xlabel("Time")
    plt.ylabel("GPUs")
    plt.title(f"GPU usage - {region_name}")
    plt.legend()
    fig.autofmt_xdate()
    plt.tight_layout()

    out_path = out_dir / f"{region_name}_gpu_daily.{PLOT_FORMAT}"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved plot for {region_name}: {out_path}")


def main() -> None:
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(exist_ok=True, parents=True)

    tokens_per_gpu_per_time_unit = TOKENS_PER_GPU_PER_HOUR * (
        TIME_UNIT_SECONDS / 3600.0
    )

    print("===================================================")
    print(f"TIME_UNIT_SECONDS = {TIME_UNIT_SECONDS}")
    print(f"TOKENS_PER_GPU_PER_HOUR = {TOKENS_PER_GPU_PER_HOUR}")
    print("Tokens per GPU per time unit:", tokens_per_gpu_per_time_unit)
    print("CSV files:", CSV_FILES)
    print(f"START_DATE = {START_DATE}")
    print(f"ANALYSIS_START_TIME = {ANALYSIS_START_TIME}")
    print(f"ANALYSIS_END_TIME   = {ANALYSIS_END_TIME}")
    print("===================================================")

    analysis_start_ts = pd.Timestamp(ANALYSIS_START_TIME) if ANALYSIS_START_TIME else None
    analysis_end_ts = pd.Timestamp(ANALYSIS_END_TIME) if ANALYSIS_END_TIME else None

    for csv_file in CSV_FILES:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"[WARN] Not found: {csv_file}")
            continue

        region_name = REGION_NAMES.get(csv_file, csv_path.stem)

        df = compute_gpu_usage_for_region(
            csv_path,
            tokens_per_gpu_per_time_unit,
            TIME_UNIT_SECONDS,
            region_name,
        )

        df_window = df.copy()
        if analysis_start_ts is not None:
            df_window = df_window[df_window["timestamp"] >= analysis_start_ts]
        if analysis_end_ts is not None:
            df_window = df_window[df_window["timestamp"] < analysis_end_ts]

        if df_window.empty:
            print(f"[WARN] No data in analysis window for {region_name}, skip saving and plotting.")
            continue
        region_csv_window = out_dir / f"gpu_usage_over_{TIME_UNIT_SECONDS}_{region_name}.csv"
        df_window.to_csv(region_csv_window, index=False)
        print(f"Saved WINDOW CSV for {region_name}: {region_csv_window}")

        plot_region(df_window, region_name, out_dir)


if __name__ == "__main__":
    main()
