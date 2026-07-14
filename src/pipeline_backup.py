# src/pipeline.py - CLEAN VERSION
from pathlib import Path
import pandas as pd
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from src.vision_processor import VisionInvoiceProcessor
import config

class InvoicePipeline:
    def __init__(self):
        self.processor = VisionInvoiceProcessor(
            model_name=config.MODEL_NAME,
            ollama_url=config.OLLAMA_URL
        )
        self.input_folder = Path(config.INPUT_FOLDER)
        self.output_folder = Path(config.OUTPUT_FOLDER)
        self.output_folder.mkdir(exist_ok=True, parents=True)
        self.results = []
        self.success_count = 0
        self.error_count = 0
        self.field_stats = {}
    
    def _clean_amount(self, value):
        if value is None or value == '' or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r'[$,€£\s]', '', value)
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            try:
                return float(cleaned)
            except:
                return None
        return None
    
    def run(self):
        invoice_files = self._get_invoice_files()
        if not invoice_files:
            print("❌ No invoice files found")
            return
        
        print(f"\n📁 Found {len(invoice_files)} invoice(s)")
        print(f"🧠 Using: {config.MODEL_NAME} via Ollama")
        print("="*60)
        
        for idx, file_path in enumerate(invoice_files, 1):
            print(f"\n🔄 [{idx}/{len(invoice_files)}] {file_path.name}")
            print("-" * 40)
            
            result = self.processor.process_invoice(str(file_path))
            
            has_data = any([
                result.get('invoice_number'),
                result.get('total_amount'),
                result.get('vendor_name')
            ])
            
            if has_data:
                self.success_count += 1
                print("   ✅ Extraction successful!")
            else:
                self.error_count += 1
                print(f"   ❌ Extraction failed: {result.get('error', 'No data')}")
            
            for field in ['invoice_number', 'invoice_date', 'vendor_name', 'customer_name', 'total_amount', 'tax_amount', 'currency']:
                if result.get(field):
                    self.field_stats[field] = self.field_stats.get(field, 0) + 1
            
            self._save_individual_result(result, file_path.stem)
            self.results.append(result)
            self._print_result_summary(result)
        
        self._save_master_csv()
        self._print_final_summary(len(invoice_files))
    
    def _get_invoice_files(self):
        files = []
        for ext in ['.jpg', '.jpeg', '.png', '.pdf']:
            files.extend(self.input_folder.glob(f"*{ext}"))
            files.extend(self.input_folder.glob(f"*{ext.upper()}"))
        seen = set()
        unique = []
        for f in sorted(files):
            if f.name.lower() not in seen:
                seen.add(f.name.lower())
                unique.append(f)
        return unique
    
    def _save_individual_result(self, result, filename):
        with open(self.output_folder / f"{filename}.json", 'w') as f:
            json.dump(result, f, indent=2)
    
    def _save_master_csv(self):
        if not self.results:
            return
        rows = []
        for r in self.results:
            rows.append({
                'filename': r.get('_filename', ''),
                'invoice_number': r.get('invoice_number', ''),
                'invoice_date': r.get('invoice_date', ''),
                'vendor_name': r.get('vendor_name', ''),
                'vendor_address': r.get('vendor_address', ''),
                'customer_name': r.get('customer_name', ''),
                'customer_address': r.get('customer_address', ''),
                'total_amount': self._clean_amount(r.get('total_amount', '')),
                'tax_amount': self._clean_amount(r.get('tax_amount', '')),
                'subtotal': self._clean_amount(r.get('subtotal', '')),
                'currency': r.get('currency', ''),
                'payment_terms': r.get('payment_terms', ''),
                'model_used': r.get('_model', ''),
                'processed_at': r.get('_processed_at', ''),
                'partial_data': r.get('_partial', False),
                'has_error': 'error' in r
            })
        pd.DataFrame(rows).to_csv(self.output_folder / "all_invoices.csv", index=False)
        print(f"\n📊 Master CSV saved")
    
    def _print_result_summary(self, result):
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            return
        
        fields = [
            ('📄 Invoice #', 'invoice_number'),
            ('📅 Date', 'invoice_date'),
            ('🏢 Vendor', 'vendor_name'),
            ('👤 Customer', 'customer_name'),
            ('💰 Total', 'total_amount'),
            ('💱 Currency', 'currency'),
        ]
        
        printed = False
        for label, key in fields:
            value = result.get(key)
            if value:
                print(f"   {label}: {value}")
                printed = True
        
        if not printed:
            print("   ⚠️ No data extracted")
        
        if result.get('_partial'):
            print("   ⚠️ Partial extraction")
    
    def _print_final_summary(self, total):
        print("\n" + "="*60)
        print("📊 PROCESSING SUMMARY")
        print("="*60)
        print(f"✅ Successfully processed: {self.success_count}/{total}")
        print(f"❌ Failed: {self.error_count}/{total}")
        print(f"\n🧠 Model: {config.MODEL_NAME}")
        
        if self.field_stats:
            print("\n📋 Field Extraction Stats:")
            for field, count in sorted(self.field_stats.items(), key=lambda x: -x[1]):
                pct = (count/total)*100
                bar = "█" * int(pct/10) + "░" * (10 - int(pct/10))
                print(f"   {field:<20} {bar} {count}/{total} ({pct:.0f}%)")
        
        print(f"\n📁 Results in: {self.output_folder.absolute()}")
        print("="*60)