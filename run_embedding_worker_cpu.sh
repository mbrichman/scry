#!/bin/bash
# Force PyTorch to use CPU instead of MPS to avoid tensor bugs

export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Alternatively, force CPU device
export CUDA_VISIBLE_DEVICES=""

source venv/bin/activate
python db/workers/embedding_worker.py --workers 4 --batch-size 20 --verbose
