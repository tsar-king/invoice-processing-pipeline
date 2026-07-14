\# 📋 Invoice Processing Pipeline – Project Summary



\## Project Overview

Built an AI-powered invoice processing system that extracts structured data from invoice images with 100% success rate using IBM Granite 3.2 Vision 2B.



\## Key Results

\- \*\*Success Rate\*\*: 100% (10/10 invoices)

\- \*\*Processing Time\*\*: \~20 seconds per invoice

\- \*\*Fields Extracted\*\*: 9 fields (invoice number, date, vendor, customer, amounts, currency)

\- \*\*Model\*\*: IBM Granite 3.2 Vision 2B (2.4 GB)

\- \*\*Platform\*\*: RTX 2050 4GB, 16GB RAM



\## Technologies Used

\- \*\*AI Model\*\*: IBM Granite 3.2 Vision 2B via Ollama

\- \*\*Language\*\*: Python 3.10+

\- \*\*Key Libraries\*\*: requests, Pillow, pandas, matplotlib

\- \*\*Output\*\*: JSON + CSV + Metrics Dashboard



\## Challenges Overcome

1\. \*\*Model Selection\*\*: Tested 5+ VLMs (LLaVA, BakLLaVA, Moondream, Phi, Granite)

2\. \*\*Hallucination\*\*: Granite proved most reliable, others hallucinated

3\. \*\*Performance\*\*: Optimized prompt and parsing for 100% success rate

4\. \*\*Data Quality\*\*: Added validation layer with confidence scoring



\## Future Enhancements

\- \[ ] Web dashboard with FastAPI

\- \[ ] Database integration (PostgreSQL)

\- \[ ] Email notifications

\- \[ ] Batch processing with progress bar

