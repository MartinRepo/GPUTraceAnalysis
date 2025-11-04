TIME_BUCKET = "15min"
GPU_TOKENS_PER_UNIT = 1_000_000
TOTAL_GPU_OVERRIDE = None
DEFAULT_TIMEZONE = "UTC"
REGION = "region1"
DEFAULT_INPUT_CSV = f"datasets/{REGION}.csv"
DEFAULT_OUTPUT_CSV = f"results/gpu_usage_over_{TIME_BUCKET}_{REGION}.csv"
DISABLE_PLOT = False
DEFAULT_OUTPUT_PNG = f"results/gpu_usage_over_{TIME_BUCKET}_{REGION}.png"

import math
import pandas as pd
import numpy as np
from pathlib import Path


def normalize_total_gpu_override(val: str):
    if val is None:
        return None
    txt = str(val).strip()
    if txt.lower() == "none" or txt == "":
        return None
    try:
        n = int(txt)
        if n < 0:
            raise ValueError("total_gpu must be non-negative")
        return n
    except Exception as e:
        raise ValueError(f"Invalid --total_gpu value: {val}. Use integer or 'None'.") from e


def load_and_prepare(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    # Check for required columns
    required = {"TIMESTAMP", "ContextTokens", "GeneratedTokens"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["TIMESTAMP"] = df["TIMESTAMP"].astype(str).str.strip()
    df = df[df["TIMESTAMP"].notna() & (df["TIMESTAMP"] != "")]

    df["TIMESTAMP"] = pd.to_datetime(
        df["TIMESTAMP"], errors="coerce", utc=True
    )

    # Drop rows that still failed to parse
    bad_rows = df["TIMESTAMP"].isna().sum()
    if bad_rows > 0:
        print(f"[warn] Dropping {bad_rows} unparsable TIMESTAMP rows.")
        df = df.dropna(subset=["TIMESTAMP"])

    for col in ["ContextTokens", "GeneratedTokens"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Compute total tokens per request
    df["total_tokens"] = df["ContextTokens"] + df["GeneratedTokens"]

    # Sort by time
    df = df.sort_values("TIMESTAMP").reset_index(drop=True)
    return df



def aggregate_by_bucket(df: pd.DataFrame, bucket: str) -> pd.DataFrame:
    agg = (
        df.set_index("TIMESTAMP")
          .resample(bucket)
          .sum(numeric_only=True)
          .rename(columns={"total_tokens": "total_tokens_sum"})
    )
    if "total_tokens_sum" not in agg.columns:
        # just in case, recompute
        agg["total_tokens_sum"] = agg.get("ContextTokens", 0.0) + agg.get("GeneratedTokens", 0.0)
    return agg[["total_tokens_sum"]]


def compute_gpu_metrics(agg: pd.DataFrame, gpu_tokens_per_unit: float, total_gpu_override: int | None) -> pd.DataFrame:
    out = agg.copy()
    out["gpu_required"] = np.ceil(out["total_tokens_sum"] / float(gpu_tokens_per_unit))

    if total_gpu_override is None:
        # capacity policy: provision to peak (ceil of max requirement)
        peak = out["gpu_required"].max()
        total_gpu = int(math.ceil(peak))
    else:
        total_gpu = int(total_gpu_override)

    out["total_gpu"] = total_gpu
    out["free_gpu"] = out["total_gpu"] - out["gpu_required"]

    # For readability, add a column with the bucket start time as a regular column
    out = out.reset_index().rename(columns={"TIMESTAMP": "time_window_start"})
    return out


def save_results(df: pd.DataFrame, out_csv: Path):
    df.to_csv(out_csv, index=False)


def try_plot(df: pd.DataFrame, out_png: Path, disabled: bool):
    if disabled:
        return
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(12, 5))
    ax = plt.gca()
    ax.plot(df["time_window_start"], df["gpu_required"], label="GPU Required")
    ax.plot(df["time_window_start"], df["total_gpu"], label="Total GPU (Capacity)")
    ax.plot(df["time_window_start"], df["free_gpu"], label="Free GPU")

    ax.set_title("GPU Requirement and Free GPU Over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("GPUs")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main():
    bucket = TIME_BUCKET
    gpu_tokens_per_unit = GPU_TOKENS_PER_UNIT
    total_gpu_override = normalize_total_gpu_override(TOTAL_GPU_OVERRIDE)

    df = load_and_prepare(DEFAULT_INPUT_CSV)
    agg = aggregate_by_bucket(df, bucket=bucket)
    result = compute_gpu_metrics(agg, gpu_tokens_per_unit=gpu_tokens_per_unit, total_gpu_override=total_gpu_override)

    save_results(result, DEFAULT_OUTPUT_CSV)
    try_plot(result, DEFAULT_OUTPUT_PNG, disabled=DISABLE_PLOT)
    print(f"[Done] Results Wrote: {DEFAULT_OUTPUT_CSV}")
    if not DISABLE_PLOT:
        print(f"[Plot] Plot Wrote: {DEFAULT_OUTPUT_PNG}")

if __name__ == "__main__":
    main()
