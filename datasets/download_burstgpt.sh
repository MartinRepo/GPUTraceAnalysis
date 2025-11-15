#!/bin/bash

# Create directory
mkdir -p datasets/burstgpt_data
cd datasets/burstgpt_data

# Base URL of the release
BASE_URL="https://github.com/HPMLL/BurstGPT/releases/download/v1.1"

# File list
FILES=(
  "BurstGPT_1.csv"
  "BurstGPT_without_fails_1.csv"
  "BurstGPT_2.csv"
  "BurstGPT_without_fails_2.csv"
)

echo "Downloading BurstGPT CSV files..."

for f in "${FILES[@]}"; do
    echo "Downloading $f ..."
    wget -q --show-progress "${BASE_URL}/${f}"
done

echo "Download complete. Files saved in ./burstgpt_data/"
