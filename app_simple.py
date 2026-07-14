# app_simple.py - UPDATED: appends uploads to master CSV
import os
import json
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
Path("uploads").mkdir(exist_ok=True)
Path("output_data").mkdir(exist_ok=True)

# ============================================================
# SIMPLE HTML TEMPLATE (unchanged)
# ============================================================
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Invoice Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 28px; font-weight: bold; color: #667eea; }
        .stat-label { color: #888; }
        table { width: 100%; background: white; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #667eea; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #eee; }
        .badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; display: inline-block; }
        .badge-high { background: #4CAF50; color: white; }
        .badge-medium { background: #FF9800; color: white; }
        .badge-low { background: #f44336; color: white; }
        .upload-section { background: white; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .upload-section input, .upload-section button { padding: 10px; margin: 5px; }
        .upload-section button { background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .upload-section button:hover { background: #5a6fd6; }
        .footer { text-align: center; color: #888; margin-top: 20px; }
        .loading { text-align: center; padding: 40px; color: #888; }
        .error { color: #f44336; padding: 20px; text-align: center; }
        .success { color: #4CAF50; padding: 10px; background: #d4edda; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Invoice Processing Dashboard</h1>
            <p>AI-powered invoice extraction with Granite 3.2 Vision</p>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card"><div class="stat-value" id="totalCount">-</div><div class="stat-label">Total Invoices</div></div>
            <div class="stat-card"><div class="stat-value" id="totalValue">-</div><div class="stat-label">Total Value ($)</div></div>
            <div class="stat-card"><div class="stat-value" id="avgValue">-</div><div class="stat-label">Average Value ($)</div></div>
            <div class="stat-card"><div class="stat-value" id="vendorCount">-</div><div class="stat-label">Unique Vendors</div></div>
        </div>
        
        <div style="background:white;padding:20px;border-radius:10px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
            <h3>📋 Invoices</h3>
            <div id="tableContainer"><div class="loading">Loading invoices...</div></div>
        </div>
        
        <div class="upload-section">
            <h3>📤 Upload Invoice</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" accept=".jpg,.jpeg,.png,.pdf" required>
                <button type="submit">📤 Upload & Process</button>
                <div id="uploadStatus"></div>
            </form>
        </div>
        
        <div class="footer">
            <p>Powered by Granite 3.2 Vision 2B | Local AI Processing</p>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                const res = await fetch('/api/invoices');
                const data = await res.json();
                
                if (data.invoices && data.invoices.length > 0) {
                    const invoices = data.invoices;
                    document.getElementById('totalCount').textContent = invoices.length;
                    
                    let total = 0;
                    let validCount = 0;
                    for (const inv of invoices) {
                        const amount = parseFloat(inv.total_amount);
                        if (!isNaN(amount) && amount > 0) {
                            total += amount;
                            validCount++;
                        }
                    }
                    
                    document.getElementById('totalValue').textContent = '$' + total.toFixed(2);
                    const avg = validCount > 0 ? total / validCount : 0;
                    document.getElementById('avgValue').textContent = '$' + avg.toFixed(2);
                    
                    const vendors = new Set();
                    for (const inv of invoices) if (inv.vendor_name) vendors.add(inv.vendor_name);
                    document.getElementById('vendorCount').textContent = vendors.size;
                    
                    let html = '<table><thead><tr><th>Invoice #</th><th>Date</th><th>Vendor</th><th>Total</th><th>Validation</th></tr></thead><tbody>';
                    for (const inv of invoices) {
                        const score = inv.validation_score || 0;
                        let badge = '<span class="badge badge-low">❌ Low</span>';
                        if (score >= 0.7) badge = '<span class="badge badge-high">✅ High</span>';
                        else if (score >= 0.4) badge = '<span class="badge badge-medium">⚠️ Medium</span>';
                        
                        const amount = parseFloat(inv.total_amount) || 0;
                        html += `<tr>
                            <td>${inv.invoice_number || 'N/A'}</td>
                            <td>${inv.invoice_date || 'N/A'}</td>
                            <td>${inv.vendor_name || 'N/A'}</td>
                            <td>${inv.currency || '$'}${amount.toFixed(2)}</td>
                            <td>${badge}</td>
                        </tr>`;
                    }
                    html += '</tbody></table>';
                    document.getElementById('tableContainer').innerHTML = html;
                } else {
                    document.getElementById('tableContainer').innerHTML = '<div class="loading">No invoices processed yet. Upload one above!</div>';
                    document.getElementById('totalCount').textContent = '0';
                    document.getElementById('totalValue').textContent = '$0.00';
                    document.getElementById('avgValue').textContent = '$0.00';
                    document.getElementById('vendorCount').textContent = '0';
                }
            } catch (e) {
                document.getElementById('tableContainer').innerHTML = `<div class="error">Error: ${e.message}</div>`;
            }
        }
        
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const status = document.getElementById('uploadStatus');
            
            if (!fileInput.files || fileInput.files.length === 0) {
                status.innerHTML = '<span style="color:red;">Please select a file</span>';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            status.innerHTML = '⏳ Uploading and processing...';
            status.className = '';
            
            try {
                const res = await fetch('/api/upload', { method: 'POST', body: formData });
                const result = await res.json();
                
                if (result.success) {
                    const inv = result.result || {};
                    const score = inv._validation_score || 0;
                    let badge = '❌ Low';
                    if (score >= 0.7) badge = '✅ High';
                    else if (score >= 0.4) badge = '⚠️ Medium';
                    
                    status.innerHTML = `
                        <div class="success">
                            <strong>✅ Processed: ${result.filename}</strong><br>
                            📄 Invoice Number: ${inv.invoice_number || 'N/A'}<br>
                            🏢 Vendor: ${inv.vendor_name || 'N/A'}<br>
                            💰 Total: ${inv.currency || '$'}${parseFloat(inv.total_amount || 0).toFixed(2)}<br>
                            📊 Validation: ${badge}
                        </div>
                    `;
                    fileInput.value = '';
                    loadData();  // Refresh the table and stats
                } else {
                    status.innerHTML = `<span style="color:red;">❌ ${result.error}</span>`;
                }
            } catch (e) {
                status.innerHTML = `<span style="color:red;">❌ ${e.message}</span>`;
            }
        });
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', loadData);
        
        // Refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

# ============================================================
# API ENDPOINTS (UPDATED)
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=SIMPLE_HTML)

@app.get("/api/invoices")
async def get_invoices():
    try:
        csv_path = Path("output_data/all_invoices.csv")
        if not csv_path.exists():
            return {"invoices": [], "count": 0}
        
        df = pd.read_csv(csv_path)
        # Ensure numeric columns are float
        for col in ['total_amount', 'subtotal', 'tax_amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.fillna("")
        return {"invoices": df.to_dict('records'), "count": len(df)}
    except Exception as e:
        print(f"Error in /api/invoices: {e}")
        return {"invoices": [], "count": 0, "error": str(e)}

@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        from src.pipeline import InvoicePipeline
        from src.validator import InvoiceValidator
        
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process invoice
        pipeline = InvoicePipeline()
        result = pipeline.processor.process_invoice(str(file_path))
        
        # Validate
        validation = InvoiceValidator.validate(result)
        result['_validation_score'] = validation["score"]
        result['_is_valid'] = validation["is_valid"]
        result['_filename'] = file.filename
        
        # Save individual JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"output_data/uploaded_{timestamp}.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        # --- NEW: Append to master CSV ---
        csv_path = Path("output_data/all_invoices.csv")
        # Build a row with the fields we want in CSV
        row = {
            'filename': file.filename,
            'invoice_number': result.get('invoice_number', ''),
            'invoice_date': result.get('invoice_date', ''),
            'due_date': result.get('due_date', ''),
            'vendor_name': result.get('vendor_name', ''),
            'vendor_address': result.get('vendor_address', ''),
            'customer_name': result.get('customer_name', ''),
            'customer_address': result.get('customer_address', ''),
            'total_amount': result.get('total_amount', ''),
            'tax_amount': result.get('tax_amount', ''),
            'subtotal': result.get('subtotal', ''),
            'currency': result.get('currency', ''),
            'payment_terms': result.get('payment_terms', ''),
            'validation_score': result.get('_validation_score', ''),
            'is_valid': result.get('_is_valid', ''),
            'processed_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])
        df.to_csv(csv_path, index=False)
        
        return {
            "success": True,
            "filename": file.filename,
            "result": result
        }
    except Exception as e:
        print(f"Error in /api/upload: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 INVOICE DASHBOARD (SIMPLE VERSION)")
    print("="*60)
    print("🌐 URL: http://localhost:8000")
    print("📡 API Docs: http://localhost:8000/docs")
    print("="*60)
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(
        "app_simple:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )