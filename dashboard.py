# dashboard.py - FIXED VERSION
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def create_dashboard():
    """Generate a professional visual dashboard from invoice data"""
    
    print("\n" + "="*60)
    print("📊 GENERATING INVOICE DASHBOARD")
    print("="*60)
    
    # Check if data exists
    csv_path = Path("output_data/all_invoices.csv")
    if not csv_path.exists():
        print("❌ No invoice data found. Run the pipeline first!")
        return
    
    # Load data
    df = pd.read_csv(csv_path)
    
    # Clean numeric columns
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
    df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce')
    df['validation_score'] = pd.to_numeric(df['validation_score'], errors='coerce')
    
    # Create output directory for dashboard
    dashboard_dir = Path("output_data/dashboard")
    dashboard_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"📊 Creating dashboard in: {dashboard_dir}")
    
    # ============================================================
    # 1. PRINT STATISTICS
    # ============================================================
    
    print("\n" + "="*60)
    print("📊 INVOICE DASHBOARD")
    print("="*60)
    
    print(f"\n📈 Total Invoices: {len(df)}")
    
    # Calculate totals
    total_value = df['total_amount'].sum()
    print(f"💰 Total Value: ${total_value:,.2f}")
    print(f"📊 Average Value: ${df['total_amount'].mean():,.2f}")
    print(f"🔝 Max Value: ${df['total_amount'].max():,.2f}")
    print(f"📉 Min Value: ${df['total_amount'].min():,.2f}")
    
    # Validation stats
    if 'validation_score' in df.columns:
        valid_count = df['validation_score'].notna().sum()
        if valid_count > 0:
            avg_score = df['validation_score'].mean()
            print(f"\n🎯 Average Validation Score: {avg_score:.0%}")
    
    # Top vendors
    print("\n🏢 Top 5 Vendors by Total Value:")
    top_vendors = df.groupby('vendor_name')['total_amount'].sum().sort_values(ascending=False).head(5)
    for vendor, amount in top_vendors.items():
        if vendor and vendor != 'nan':
            print(f"   {vendor[:30]}: ${amount:,.2f}")
    
    # Currency distribution
    print("\n💱 Currency Distribution:")
    for currency, count in df['currency'].value_counts().items():
        if currency and currency != 'nan':
            print(f"   {currency}: {count} invoices ({count/len(df)*100:.0f}%)")
    
    # ============================================================
    # 2. CREATE CHARTS
    # ============================================================
    
    # Only create charts if we have enough data
    if len(df) > 1:
        print("\n📈 Generating charts...")
        
        # Create a figure with multiple subplots
        fig = plt.figure(figsize=(14, 10))
        
        # Chart 1: Invoice Amounts Bar Chart
        ax1 = plt.subplot(2, 2, 1)
        valid_amounts = df['total_amount'].notna()
        if valid_amounts.sum() > 0:
            # Create bar chart
            bars = ax1.bar(range(len(df[valid_amounts])), 
                          df.loc[valid_amounts, 'total_amount'].values, 
                          color='steelblue', alpha=0.7)
            ax1.set_title('Invoice Amounts', fontsize=12)
            ax1.set_xlabel('Invoice Index', fontsize=10)
            ax1.set_ylabel('Amount ($)', fontsize=10)
            
            # Add value labels on bars
            for bar, amount in zip(bars, df.loc[valid_amounts, 'total_amount'].values):
                if amount > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            f'${amount:.0f}', ha='center', va='bottom', fontsize=8)
        else:
            ax1.text(0.5, 0.5, 'No valid amount data', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Invoice Amounts', fontsize=12)
        
        # Chart 2: Top Vendors Horizontal Bar Chart
        ax2 = plt.subplot(2, 2, 2)
        vendor_data = df.groupby('vendor_name')['total_amount'].sum().sort_values(ascending=False).head(10)
        if len(vendor_data) > 0 and vendor_data.sum() > 0:
            vendor_data = vendor_data[vendor_data > 0]
            # Create bars
            bars = ax2.barh(vendor_data.index, vendor_data.values, color='forestgreen', alpha=0.7)
            ax2.set_title('Top 10 Vendors by Total Value', fontsize=12)
            ax2.set_xlabel('Total Amount ($)', fontsize=10)
            # Set y-ticks with truncated labels
            labels = [name[:25] + '...' if len(str(name)) > 25 else name for name in vendor_data.index]
            ax2.set_yticks(range(len(labels)))
            ax2.set_yticklabels(labels)
        else:
            ax2.text(0.5, 0.5, 'No vendor data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Top Vendors', fontsize=12)
        
        # Chart 3: Validation Scores Distribution
        ax3 = plt.subplot(2, 2, 3)
        if 'validation_score' in df.columns and df['validation_score'].notna().sum() > 0:
            scores = df['validation_score'].dropna()
            ax3.hist(scores, bins=10, color='cornflowerblue', edgecolor='black', alpha=0.7)
            ax3.set_title('Validation Score Distribution', fontsize=12)
            ax3.set_xlabel('Confidence Score', fontsize=10)
            ax3.set_ylabel('Number of Invoices', fontsize=10)
            ax3.axvline(scores.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {scores.mean():.0%}')
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, 'No validation data available', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Validation Scores', fontsize=12)
        
        # Chart 4: Currency Distribution Pie Chart
        ax4 = plt.subplot(2, 2, 4)
        currency_counts = df['currency'].value_counts()
        currency_counts = currency_counts[currency_counts.index.notna()]
        if len(currency_counts) > 0:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            ax4.pie(currency_counts.values, labels=currency_counts.index, 
                   autopct='%1.0f%%', colors=colors[:len(currency_counts)],
                   shadow=True, startangle=90)
            ax4.set_title('Currency Distribution', fontsize=12)
        else:
            ax4.text(0.5, 0.5, 'No currency data', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Currency Distribution', fontsize=12)
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save dashboard
        dashboard_path = dashboard_dir / "dashboard.png"
        plt.savefig(dashboard_path, dpi=150, bbox_inches='tight')
        print(f"   ✅ Dashboard saved: {dashboard_path}")
        
        # Also save a high-res version
        plt.savefig(dashboard_dir / "dashboard_hires.png", dpi=300, bbox_inches='tight')
        print(f"   ✅ High-res dashboard saved: {dashboard_dir / 'dashboard_hires.png'}")
        
        # Try to display the plot (if running in GUI environment)
        try:
            plt.show()
        except:
            pass
        plt.close()
    
    # ============================================================
    # 3. GENERATE HTML DASHBOARD
    # ============================================================
    
    print("\n📄 Generating HTML dashboard...")
    
    # Get model name
    model_name = getattr(config, 'MODEL_NAME', 'Granite 3.2 Vision 2B')
    
    # Clean data for HTML
    total_value_clean = float(total_value) if not pd.isna(total_value) else 0
    avg_value_clean = float(df['total_amount'].mean()) if not pd.isna(df['total_amount'].mean()) else 0
    unique_vendors = len(df['vendor_name'].unique())
    
    # Create HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice Processing Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 5px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f0f0f0; }}
        .badge-success {{ background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .badge-warning {{ background: #FF9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .badge-danger {{ background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Invoice Processing Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Model: {model_name}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(df)}</div>
                <div class="stat-label">Total Invoices</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${total_value_clean:,.2f}</div>
                <div class="stat-label">Total Value</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${avg_value_clean:,.2f}</div>
                <div class="stat-label">Average Value</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{unique_vendors}</div>
                <div class="stat-label">Unique Vendors</div>
            </div>
        </div>
        
        <div class="chart-container">
            <img src="dashboard.png" alt="Dashboard Charts">
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3>📋 Invoice Details</h3>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Invoice #</th>
                            <th>Date</th>
                            <th>Vendor</th>
                            <th>Total</th>
                            <th>Currency</th>
                            <th>Validation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add table rows (limit to 20 for performance)
    for _, row in df.head(20).iterrows():
        inv_num = row.get('invoice_number', 'N/A')
        inv_date = row.get('invoice_date', 'N/A')
        vendor = str(row.get('vendor_name', 'N/A'))[:30]
        total = f"${row.get('total_amount', 0):.2f}" if pd.notna(row.get('total_amount')) else 'N/A'
        currency = row.get('currency', '')
        
        score = row.get('validation_score', 0)
        if pd.notna(score) and score >= 0.7:
            badge = '<span class="badge-success">✅ High</span>'
        elif pd.notna(score) and score >= 0.4:
            badge = '<span class="badge-warning">⚠️ Medium</span>'
        else:
            badge = '<span class="badge-danger">❌ Low</span>'
        
        html_content += f"""
                        <tr>
                            <td>{inv_num}</td>
                            <td>{inv_date}</td>
                            <td>{vendor}</td>
                            <td>{total}</td>
                            <td>{currency}</td>
                            <td>{badge}</td>
                        </tr>
"""
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by AI Invoice Processing Pipeline</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML dashboard
    html_path = dashboard_dir / "dashboard.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✅ HTML dashboard saved: {html_path}")
    
    # ============================================================
    # 4. SAVE SUMMARY JSON
    # ============================================================
    
    print("\n📊 Saving summary data...")
    
    # Clean top vendors for JSON
    top_vendors_dict = df.groupby('vendor_name')['total_amount'].sum().sort_values(ascending=False).head(10).to_dict()
    top_vendors_dict = {k: float(v) for k, v in top_vendors_dict.items() if pd.notna(k) and k != 'nan'}
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_invoices": int(len(df)),
        "total_value": float(total_value_clean),
        "average_value": float(avg_value_clean),
        "unique_vendors": int(unique_vendors),
        "currency_distribution": {str(k): int(v) for k, v in df['currency'].value_counts().to_dict().items() if pd.notna(k)},
        "top_vendors": top_vendors_dict,
        "validation_avg_score": float(df['validation_score'].mean()) if 'validation_score' in df and df['validation_score'].notna().sum() > 0 else 0,
        "model": model_name
    }
    
    summary_path = dashboard_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✅ Summary data saved: {summary_path}")
    
    print("\n" + "="*60)
    print("✅ Dashboard generation complete!")
    print(f"📁 Dashboard files in: {dashboard_dir}")
    print("\n📄 To view the HTML dashboard, open:")
    print(f"   {dashboard_dir / 'dashboard.html'}")
    print("="*60)

if __name__ == "__main__":
    create_dashboard()