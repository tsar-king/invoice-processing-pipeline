# 🧾 AI Invoice Processing Pipeline

> **Automated invoice data extraction using IBM Granite 3.2 Vision 2B** – 100% local, no API costs, complete data privacy.

---

## 📌 Overview

This project is a production‑ready AI pipeline that extracts structured data from invoice images and PDFs using a vision‑language model. It processes invoices locally, outputs structured JSON, CSV, and Excel reports, and includes a **FastAPI web dashboard** for real‑time processing.

---

## ✨ Key Features

- 🔒 **100% Local** – No API calls, no cloud costs, complete data privacy.
- 🤖 **Vision AI** – Uses IBM Granite 3.2 Vision 2B for document understanding.
- 📄 **Multi‑format** – Supports JPG, JPEG, PNG, and PDF invoices.
- 📊 **Structured Output** – JSON, CSV, and Excel with multiple sheets.
- ⚡ **Fast Processing** – ~20 seconds per invoice on RTX 2050 4GB.
- 📈 **Web Dashboard** – FastAPI interface with file upload, live processing, and data visualization.
- 🛡️ **Validation Layer** – Confidence scoring and error detection.
- 📦 **Batch Processing** – Progress bars, automatic retries, and logging.

---

## 🧠 Models Tested

| Model | Status | Reason |
|-------|--------|--------|
| **Granite 3.2 Vision 2B** | ✅ **Selected** | Best balance of speed/accuracy |
| Moondream | ❌ Rejected | Poor accuracy, hallucination |
| LLaVA 7B | ❌ Failed | Hallucinated, not reading images |
| BakLLaVA 7B | ❌ Failed | Empty/incomplete responses |

---

## 🏗️ Architecture
┌─────────────────────┐
│ Input Invoices │ (JPG, PNG, PDF)
│ (input_invoices/) │
└──────────┬──────────┘
▼
┌─────────────────────┐
│ Granite 3.2 │ (Vision-Language Model via Ollama)
│ Vision 2B │
└──────────┬──────────┘
▼
┌─────────────────────┐
│ Text Extraction │ (JSON Parsing + Regex Fallback)
└──────────┬──────────┘
▼
┌─────────────────────┐
│ Validation │ (Confidence scoring, error detection)
└──────────┬──────────┘
▼
┌─────────────────────┐
│ Output │ (JSON + CSV + Excel + Dashboard)
│ (output_data/) │
└─────────────────────┘


1. **Input** → `input_invoices/` (JPG, PNG, PDF)
2. **AI Processing** → Granite 3.2 Vision 2B via Ollama
3. **Text Extraction** → JSON Parsing + Regex Fallback
4. **Validation** → Confidence scoring & error detection
5. **Output** → JSON, CSV, Excel, and Dashboard (`output_data/`)
---

## 📊 Fields Extracted

| Field | Example |
|-------|---------|
| Invoice Number | `40378170` |
| Invoice Date | `2012-10-15` |
| Vendor Name | `Patel, Thompson and Montgomery` |
| Vendor Address | `356 Kyle Vista, New James, MA` |
| Customer Name | `Jackson, Odonnell and Jackson` |
| Customer Address | `267 John Track Suite 841` |
| Total Amount | `8.25` |
| Subtotal | `7.50` |
| Tax Amount | `0.75` |
| Currency | `$` |

---

## 💻 Tech Stack

| Layer | Technology |
|-------|------------|
| **AI Model** | IBM Granite 3.2 Vision 2B (via Ollama) |
| **Language** | Python 3.10+ |
| **Web Framework** | FastAPI |
| **Data Analysis** | Pandas, Matplotlib |
| **Output** | JSON, CSV, Excel (openpyxl) |
| **Platform** | Local (RTX 2050 4GB + 16GB RAM) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Ollama installed
- 4GB+ GPU or 8GB+ RAM

### Installation

```bash
# 1. Clone or download this repository
git clone https://github.com/tsar-king/invoice-processing-pipeline.git
cd invoice-processing-pipeline

# 2. Create virtual environment
conda create -n invoice_pipeline python=3.10 -y
conda activate invoice_pipeline

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull the model
ollama pull granite3.2-vision:2b

# 5. Place your invoices in input_invoices/

# 6. Run the pipeline
python run_enhanced.py --batch-size 5

# 7. Start the web dashboard
python app_simple.py

Project Link: [https://github.com/tsar-king/invoice-processing-pipeline](https://github.com/tsar-king/invoice-processing-pipeline)