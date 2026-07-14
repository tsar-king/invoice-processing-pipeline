# src/excel_exporter.py - FIXED VERSION
import pandas as pd
from pathlib import Path
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment
from src.logger import logger

class ExcelExporter:
    """Export invoice data to formatted Excel"""
    
    def __init__(self, output_folder: str = "output_data"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True, parents=True)
        logger.info(f"ExcelExporter initialized")
    
    def export(self, df: pd.DataFrame, filename: str = None) -> Path:
        if df.empty:
            logger.warning("No data to export")
            return None
        
        if filename is None:
            filename = f"invoices_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        file_path = self.output_folder / filename
        logger.info(f"Exporting {len(df)} invoices to {file_path}")
        
        # Clean data
        df = df.copy()
        for col in ['total_amount', 'tax_amount', 'subtotal']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Sheet 1: All Invoices
            self._write_invoices_sheet(df, writer)
            
            # Sheet 2: Vendor Summary
            self._write_vendor_summary(df, writer)
            
            # Sheet 3: Monthly Summary
            self._write_monthly_summary(df, writer)
            
            # Sheet 4: Top Invoices
            self._write_top_invoices(df, writer)
            
            # Sheet 5: Validation Summary (if column exists)
            if 'validation_score' in df.columns:
                self._write_validation_summary(df, writer)
        
        logger.success(f"Excel report saved to {file_path}")
        return file_path
    
    def _write_invoices_sheet(self, df, writer):
        df.to_excel(writer, sheet_name='All Invoices', index=False)
        self._auto_adjust_width(writer.sheets['All Invoices'])
        self._style_header(writer.sheets['All Invoices'])
    
    def _write_vendor_summary(self, df, writer):
        if 'total_amount' in df.columns and 'vendor_name' in df.columns:
            vendor_summary = df.groupby('vendor_name')['total_amount'].agg(['sum', 'mean', 'count']).round(2)
            vendor_summary.columns = ['Total Value', 'Average Value', 'Invoice Count']
            vendor_summary = vendor_summary.sort_values('Total Value', ascending=False)
            vendor_summary.to_excel(writer, sheet_name='Vendor Summary')
            self._auto_adjust_width(writer.sheets['Vendor Summary'])
            self._style_header(writer.sheets['Vendor Summary'])
    
    def _write_monthly_summary(self, df, writer):
        if 'invoice_date' in df.columns and 'total_amount' in df.columns:
            df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
            df['month'] = df['invoice_date'].dt.to_period('M')
            monthly = df.groupby('month')['total_amount'].agg(['sum', 'count']).round(2)
            monthly.columns = ['Total Value', 'Invoice Count']
            monthly.to_excel(writer, sheet_name='Monthly Summary')
            self._auto_adjust_width(writer.sheets['Monthly Summary'])
            self._style_header(writer.sheets['Monthly Summary'])
    
    def _write_top_invoices(self, df, writer):
        if 'total_amount' in df.columns:
            cols = ['invoice_number', 'vendor_name', 'total_amount', 'invoice_date', 'currency']
            existing_cols = [c for c in cols if c in df.columns]
            if existing_cols:
                top_invoices = df.nlargest(10, 'total_amount')[existing_cols]
                top_invoices.to_excel(writer, sheet_name='Top 10 Invoices', index=False)
                self._auto_adjust_width(writer.sheets['Top 10 Invoices'])
                self._style_header(writer.sheets['Top 10 Invoices'])
    
    def _write_validation_summary(self, df, writer):
        if 'validation_score' in df.columns:
            validation_summary = pd.DataFrame({
                'Metric': ['Average Score', 'High (≥70%)', 'Medium (40-69%)', 'Low (<40%)'],
                'Value': [
                    f"{df['validation_score'].mean():.1%}" if df['validation_score'].notna().sum() > 0 else "N/A",
                    f"{(df['validation_score'] >= 0.7).sum()} invoices",
                    f"{(df['validation_score'].between(0.4, 0.7)).sum()} invoices",
                    f"{(df['validation_score'] < 0.4).sum()} invoices"
                ]
            })
            validation_summary.to_excel(writer, sheet_name='Validation Summary', index=False)
            self._style_header(writer.sheets['Validation Summary'])
    
    def _auto_adjust_width(self, worksheet):
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _style_header(self, worksheet):
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')


def export_to_excel():
    """Main entry point for Excel export"""
    csv_path = Path("output_data/all_invoices.csv")
    if not csv_path.exists():
        logger.error("No data found. Run the pipeline first!")
        return None
    
    df = pd.read_csv(csv_path)
    exporter = ExcelExporter()
    file_path = exporter.export(df)
    
    if file_path:
        print(f"\n✅ Excel report: {file_path}")
    return file_path

if __name__ == "__main__":
    export_to_excel()