# GPU Capacity Collector

This tool analyzes **Azure LLM Inference Trace** datasets to estimate GPU utilization and capacity requirements over time.
It aggregates token-level data into time buckets, computes GPU demand, and visualizes total vs. free GPU capacity.

---

## Overview

* **Input:** Azure LLM Inference Trace CSV files (`TIMESTAMP, ContextTokens, GeneratedTokens`)
* **Output:**

  * Aggregated CSV showing GPU usage and free capacity
  * Line chart of GPU demand vs. total capacity over time

---

## Environment Setup

1. **Install dependencies**

   ```bash
   pip install pandas numpy matplotlib
   ```

2. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

---

## Download Datasets

Use the helper script to download the official Azure public datasets:

```bash
bash download_datasets.sh
```

This will create the following directory structure:

```
datasets/
 ├─ region1.csv   # Code dataset
 └─ region2.csv   # Conversation dataset
```

---

## Configuration

Edit the top of the Python script to customize runtime parameters:

| Variable              | Default                                               | Description                                                                   |
| --------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| `TIME_BUCKET`         | `"15min"`                                             | Time aggregation window (`"15min"`, `"30min"`, `"1H"`, etc.)                  |
| `GPU_TOKENS_PER_UNIT` | `1_000_000`                                           | Tokens a single GPU can process per time bucket                               |
| `TOTAL_GPU_OVERRIDE`  | `None`                                                | If set, fixes total GPU capacity; if `None`, auto-calculated from peak demand |
| `DEFAULT_TIMEZONE`    | `"UTC"`                                               | Dataset timezone                                                              |
| `REGION`              | `"region1"`                                           | Region name used for input/output naming                                      |
| `DEFAULT_INPUT_CSV`   | `"datasets/{REGION}.csv"`                             | Input dataset path                                                            |
| `DEFAULT_OUTPUT_CSV`  | `"results/gpu_usage_over_{TIME_BUCKET}_{REGION}.csv"` | Output CSV path                                                               |
| `DISABLE_PLOT`        | `False`                                               | Disable plot generation if `True`                                             |
| `DEFAULT_OUTPUT_PNG`  | `"results/gpu_usage_over_{TIME_BUCKET}_{REGION}.png"` | Output plot path                                                              |

---

## Run the Analysis

Run the main analysis script:

```bash
python analysis.py
```

This will:

1. Load and clean the input dataset
2. Aggregate total tokens per time window
3. Compute GPU requirements (`ceil` mode, integer GPUs)
4. Determine total GPU and free GPU
5. Save the results and plot

Example output:

```
[Done] Results Wrote: results/gpu_usage_over_15min_region1.csv
[Plot] Plot Wrote: results/gpu_usage_over_15min_region1.png
```

---

## Output Description

| Column              | Description                                  |
| ------------------- | -------------------------------------------- |
| `time_window_start` | Start timestamp of each time bucket          |
| `total_tokens_sum`  | Total input + generated tokens in the bucket |
| `gpu_required`      | GPUs required (rounded up)                   |
| `total_gpu`         | Total GPU capacity                           |
| `free_gpu`          | Available (idle) GPUs in that time window    |

The plot visualizes:

* **Blue:** GPU required
* **Orange:** Total GPU capacity
* **Green:** Free GPUs over time

---

## Tips

* A warning like `[warn] Dropping X unparsable TIMESTAMP rows.` means malformed timestamps were safely skipped.
* Adjust `GPU_TOKENS_PER_UNIT` to simulate different GPU hardware capacities.
* Compare `region1` vs. `region2` to evaluate cross-region load balancing.

---

## Example Commands

```bash
# Run analysis for region1 (default)
python analysis.py

# Run analysis for region2
REGION="region2" python analysis.py
```