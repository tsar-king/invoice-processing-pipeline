# src/pipeline.py - ENHANCED WITH VALIDATION & METRICS
from pathlib import Path
import pandas as pd
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Any
from src.vision_processor import VisionInvoiceProcessor
from src.validator import InvoiceValidator
from src.metrics import PipelineMetrics
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
        self.metrics = PipelineMetrics()
    
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
        
        self.metrics.start()
        
        print(f"\n📁 Found {len(invoice_files)} invoice(s)")
        print(f"🧠 Using: {config.MODEL_NAME} via Ollama")
        print("="*60)
        
        for idx, file_path in enumerate(invoice_files, 1):
            print(f"\n🔄 [{idx}/{len(invoice_files)}] {file_path.name}")
            print("-" * 40)
            
            start_time = time.time()
            result = self.processor.process_invoice(str(file_path))
            elapsed = time.time() - start_time
            
            # Validate result
            validation = InvoiceValidator.validate(result)
            
            # Determine success
            has_data = any([
                result.get('invoice_number'),
                result.get('total_amount'),
                result.get('vendor_name')
            ])
            
            if has_data:
                print("   ✅ Extraction successful!")
            else:
                print(f"   ❌ Extraction failed: {result.get('error', 'No data')}")
            
            # Show validation score
            if validation["score"] > 0:
                print(f"   📊 Confidence Score: {validation['score']:.0%}")
                if validation["warnings"]:
                    for warning in validation["warnings"][:2]:
                        print(f"   ⚠️ {warning}")
            
            # Record metrics
            self.metrics.record(
                success=has_data,
                time_taken=elapsed,
                fields=result,
                error=result.get('error')
            )
            
            # Add validation to result
            result['_validation_score'] = validation["score"]
            result['_is_valid'] = validation["is_valid"]
            
            self._save_individual_result(result, file_path.stem)
            self.results.append(result)
            self._print_result_summary(result, validation)
        
        self.metrics.stop()
        self._save_master_csv()
        self.metrics.save()
        self.metrics.print_summary()
    
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
                'validation_score': r.get('_validation_score', 0),
                'is_valid': r.get('_is_valid', False),
                'has_error': 'error' in r
            })
        pd.DataFrame(rows).to_csv(self.output_folder / "all_invoices.csv", index=False)
        print(f"\n📊 Master CSV saved")
    
    def _print_result_summary(self, result, validation):
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