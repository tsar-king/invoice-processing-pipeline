// web/static/js/dashboard.js

// ============================================================
// LOAD DASHBOARD DATA
// ============================================================

let charts = {};

async function loadDashboard() {
    try {
        // Load summary data
        const summaryRes = await fetch('/api/dashboard-summary');
        const summaryData = await summaryRes.json();
        
        // Load invoice data
        const invoiceRes = await fetch('/api/invoices');
        const invoiceData = await invoiceRes.json();
        
        if (invoiceData.invoices && invoiceData.invoices.length > 0) {
            updateStats(invoiceData);
            updateTable(invoiceData.invoices);
            createCharts(invoiceData.invoices);
        } else {
            document.getElementById('invoiceTableBody').innerHTML = 
                '<tr><td colspan="7" class="loading">No invoices processed yet. Upload one above!</td></tr>';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        document.getElementById('invoiceTableBody').innerHTML = 
            '<tr><td colspan="7" class="error">Error loading data</td></tr>';
    }
}

// ============================================================
// UPDATE STATS
// ============================================================

function updateStats(data) {
    const invoices = data.invoices || [];
    const total = invoices.length;
    
    // Calculate totals
    let totalValue = 0;
    for (const inv of invoices) {
        totalValue += parseFloat(inv.total_amount) || 0;
    }
    const avgValue = total > 0 ? totalValue / total : 0;
    
    // Count unique vendors
    const vendors = new Set();
    for (const inv of invoices) {
        if (inv.vendor_name) vendors.add(inv.vendor_name);
    }
    
    document.getElementById('totalInvoices').textContent = total;
    document.getElementById('totalValue').textContent = `$${totalValue.toFixed(2)}`;
    document.getElementById('avgValue').textContent = `$${avgValue.toFixed(2)}`;
    document.getElementById('vendorsCount').textContent = vendors.size;
}

// ============================================================
// UPDATE TABLE
// ============================================================

function updateTable(invoices) {
    const tbody = document.getElementById('invoiceTableBody');
    
    if (!invoices || invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No invoices</td></tr>';
        return;
    }
    
    tbody.innerHTML = invoices.map(inv => {
        const score = inv.validation_score || 0;
        let badge = '<span class="badge badge-low">❌ Low</span>';
        if (score >= 0.7) badge = '<span class="badge badge-high">✅ High</span>';
        else if (score >= 0.4) badge = '<span class="badge badge-medium">⚠️ Medium</span>';
        
        const invNum = inv.invoice_number || 'N/A';
        const invDate = inv.invoice_date || 'N/A';
        const vendor = inv.vendor_name || 'N/A';
        const amount = inv.total_amount ? `$${parseFloat(inv.total_amount).toFixed(2)}` : 'N/A';
        const currency = inv.currency || '';
        
        return `
            <tr>
                <td><a href="/results?id=${inv.filename.replace('.jpg', '').replace('.png', '')}">${invNum}</a></td>
                <td>${invDate}</td>
                <td>${vendor}</td>
                <td>${amount}</td>
                <td>${currency}</td>
                <td>${badge}</td>
                <td>
                    <button onclick="deleteInvoice('${inv.filename}')" style="background:#f44336;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;">🗑️</button>
                </td>
            </tr>
        `;
    }).join('');
}

// ============================================================
// CREATE CHARTS
// ============================================================

function createCharts(invoices) {
    // Destroy existing charts
    if (charts.amounts) { charts.amounts.destroy(); }
    if (charts.vendors) { charts.vendors.destroy(); }
    
    // Chart 1: Invoice Amounts
    const ctx1 = document.getElementById('amountsChart').getContext('2d');
    const labels = invoices.map((_, i) => `#${i+1}`);
    const amounts = invoices.map(inv => parseFloat(inv.total_amount) || 0);
    
    charts.amounts = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Amount ($)',
                data: amounts,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) { return '$' + value; }
                    }
                }
            }
        }
    });
    
    // Chart 2: Top Vendors
    const ctx2 = document.getElementById('vendorsChart').getContext('2d');
    const vendorMap = {};
    for (const inv of invoices) {
        const name = inv.vendor_name || 'Unknown';
        const amount = parseFloat(inv.total_amount) || 0;
        vendorMap[name] = (vendorMap[name] || 0) + amount;
    }
    
    const sorted = Object.entries(vendorMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    charts.vendors = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: sorted.map(([name]) => name.length > 20 ? name.slice(0, 20) + '...' : name),
            datasets: [{
                label: 'Total Value ($)',
                data: sorted.map(([_, amount]) => amount),
                backgroundColor: 'rgba(76, 175, 80, 0.7)',
                borderColor: 'rgba(76, 175, 80, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) { return '$' + value; }
                    }
                }
            }
        }
    });
}

// ============================================================
// ACTIONS
// ============================================================

async function deleteInvoice(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    
    const id = filename.replace('.jpg', '').replace('.png', '');
    try {
        const response = await fetch(`/api/invoices/${id}`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            loadDashboard();
        }
    } catch (error) {
        alert('Error deleting invoice');
    }
}

async function exportExcel() {
    try {
        window.open('/api/export/excel', '_blank');
    } catch (error) {
        alert('Error exporting Excel');
    }
}

async function processBatch() {
    if (!confirm('Process all invoices in input folder?')) return;
    
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.textContent = '⏳ Processing all invoices...';
    statusDiv.className = '';
    
    try {
        const response = await fetch('/api/process-batch', { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            statusDiv.textContent = `✅ Processed ${result.summary.successful} invoices successfully!`;
            statusDiv.className = 'success';
            loadDashboard();
        } else {
            statusDiv.textContent = '❌ Error processing batch';
            statusDiv.className = 'error';
        }
    } catch (error) {
        statusDiv.textContent = '❌ Error: ' + error.message;
        statusDiv.className = 'error';
    }
}

// ============================================================
// FILE UPLOAD
// ============================================================

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        statusDiv.textContent = 'Please select a file';
        statusDiv.className = 'error';
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    statusDiv.textContent = '⏳ Uploading and processing...';
    statusDiv.className = '';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = `
                ✅ Processed ${result.filename} successfully!
                <br>Score: ${(result.validation.score * 100).toFixed(0)}%
                <br>Invoice: ${result.result.invoice_number || 'N/A'}
            `;
            statusDiv.className = 'success';
            fileInput.value = '';
            loadDashboard();
        } else {
            statusDiv.textContent = '❌ Error processing file';
            statusDiv.className = 'error';
        }
    } catch (error) {
        statusDiv.textContent = '❌ Error: ' + error.message;
        statusDiv.className = 'error';
    }
});

// ============================================================
// AUTO-REFRESH
// ============================================================

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboard);

// Refresh every 30 seconds
setInterval(loadDashboard, 30000);