import os
import sys

# Make the repo root importable (data_layer, mock_llm, nebius_client, tools/...).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
