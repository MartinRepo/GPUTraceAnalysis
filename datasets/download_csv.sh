#!/bin/bash
set -e  

DATA_DIR="datasets"

mkdir -p "$DATA_DIR"

URL_REGION1="https://azurepublicdatasettraces.blob.core.windows.net/azurellminfererencetrace/AzureLLMInferenceTrace_code_1week.csv"
URL_REGION2="https://azurepublicdatasettraces.blob.core.windows.net/azurellminfererencetrace/AzureLLMInferenceTrace_conv_1week.csv"

FILE_REGION1="$DATA_DIR/region1.csv"
FILE_REGION2="$DATA_DIR/region2.csv"

echo "Start downloading Azure LLM Inference Trace datasets..."
echo

# Download region1
echo "Downloading region1 ..."
curl -L -o "$FILE_REGION1" "$URL_REGION1"

# Download region2
echo "Downloading region2 ..."
curl -L -o "$FILE_REGION2" "$URL_REGION2"

echo
echo "Download completed! File locations are as follows:"
echo " - $FILE_REGION1"
echo " - $FILE_REGION2"
echo
echo "You can now use these files as input to run gpu_capacity_planner.py"
