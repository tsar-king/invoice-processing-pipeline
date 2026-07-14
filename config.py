# config.py - GRANITE 3.2 VISION 2B (STABLE)
import os

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434"

# Model - Granite 3.2 Vision 2B (Working well on your system)
MODEL_NAME = "granite3.2-vision:2b"

# Pipeline settings
INPUT_FOLDER = "input_invoices"
OUTPUT_FOLDER = "output_data"
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.pdf']

# Processing settings
MAX_TOKENS = 256
TEMPERATURE = 0.0
TIMEOUT = 300