#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(dirname "$0")/ncit-semantic-mapper/src
streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0