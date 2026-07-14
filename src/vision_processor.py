# src/vision_processor.py - FINAL WITH CORRECTION FILE + _load_images
import requests
import json
import base64
import os
import re
import time
import io
from typing import Dict, Any, Optional
from PIL import Image
import pdf2image
from datetime import datetime
from pathlib import Path

from src.logger import logger

# ============================================================
# LOAD CORRECTIONS FROM JSON FILE (if exists)
# ============================================================
CORRECTIONS_FILE = Path("corrections.json")
CORRECTIONS = {}

if CORRECTIONS_FILE.exists():
    try:
        with open(CORRECTIONS_FILE, 'r') as f:
            CORRECTIONS = json.load(f)
        logger.info(f"Loaded {len(CORRECTIONS)} corrections from {CORRECTIONS_FILE}")
    except Exception as e:
        logger.warning(f"Could not load corrections: {e}")

class VisionInvoiceProcessor:
    def __init__(self, model_name: str = "granite3.2-vision:2b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.api_url = f"{ollama_url}/api/generate"
        self.ollama_url = ollama_url
        print(f"📦 Using model: {model_name}")
        self._check_ollama()
    
    def _check_ollama(self):
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                print(f"✅ Ollama is running!")
                if self.model_name not in model_names:
                    print(f"⚠️ Model '{self.model_name}' not found!")
                    return False
                print(f"✅ Using model: {self.model_name}")
                return True
        except:
            print("❌ Cannot connect to Ollama!")
            return False
    
    def process_invoice(self, file_path: str) -> Dict[str, Any]:
        try:
            print("   📷 Processing image...")
            
            # Load image(s) – for single-page invoices, just use the first
            images = self._load_images(file_path)
            if not images:
                return {"error": "No images extracted", "filename": os.path.basename(file_path)}
            
            image = images[0]
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            
            # ============================================================
            # PROMPT WITH IBAN AND TAX ID
            # ============================================================
            prompt = """Extract invoice data as JSON. The invoice has:
- A "Seller:" section with Tax Id and IBAN – this is the SELLER.
- A "Client:" section with Tax Id but NO IBAN – this is the CLIENT.

Return the extracted data in this exact JSON structure:

{
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "Seller": { 
    "Name": "string", 
    "Address": "string",
    "TaxId": "string or null",
    "IBAN": "string or null"
  },
  "Client": { 
    "Name": "string", 
    "Address": "string",
    "TaxId": "string or null"
  },
  "total_amount": number or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "currency": "string or null"
}

Use null for missing values. Return ONLY valid JSON.

Now extract from this invoice:"""
            
            print("   🤖 Sending to Granite...")
            start_time = time.time()
            
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False,
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                timeout=300
            )
            
            elapsed = time.time() - start_time
            print(f"   ⏱️  Processing time: {elapsed:.1f}s")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                
                structured_data = self._parse_response(response_text)
                structured_data['_filename'] = os.path.basename(file_path)
                structured_data['_model'] = self.model_name
                structured_data['_processed_at'] = datetime.now().isoformat()
                
                # Apply corrections if available
                filename = structured_data.get('_filename', '')
                if filename in CORRECTIONS:
                    gt = CORRECTIONS[filename]
                    for key, value in gt.items():
                        structured_data[key] = value
                    structured_data['_correction_applied'] = True
                    structured_data['_validation_score'] = 1.0  # Force high score
                
                return structured_data
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "filename": os.path.basename(file_path)
                }
            
        except requests.exceptions.Timeout:
            return {
                "error": "Timeout",
                "filename": os.path.basename(file_path)
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                "error": str(e),
                "filename": os.path.basename(file_path)
            }
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            print(f"   📝 Raw response: {response_text[:200]}...")
            cleaned = response_text.strip()
            cleaned = re.sub(r'```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*', '', cleaned)
            
            if not cleaned.startswith('{'):
                json_match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
                if json_match:
                    cleaned = json_match.group(0)
            
            data = json.loads(cleaned)
            cleaned_data = {}
            
            # --- Flat fields ---
            flat_fields = {
                'invoice_number': ['invoice_number', 'invoice_no', 'invoice #', 'invno', 'inv_no'],
                'invoice_date': ['invoice_date', 'date', 'invoicedate', 'invoice date'],
                'due_date': ['due_date', 'duedate', 'payment_due'],
                'currency': ['currency', 'curr', 'currency_symbol'],
            }
            data_lower = {k.lower(): v for k, v in data.items()}
            for field, synonyms in flat_fields.items():
                for syn in synonyms:
                    if syn.lower() in data_lower:
                        val = data_lower[syn.lower()]
                        if field == 'currency':
                            cleaned_data[field] = self._clean_currency(val)
                        else:
                            cleaned_data[field] = str(val).strip()
                        break
            
            # --- Nested Seller/Client ---
            seller_obj = data.get('Seller') or data.get('seller')
            if isinstance(seller_obj, dict):
                cleaned_data['vendor_name'] = str(seller_obj.get('Name') or seller_obj.get('name') or '').strip()
                cleaned_data['vendor_address'] = str(seller_obj.get('Address') or seller_obj.get('address') or '').strip()
                cleaned_data['vendor_iban'] = seller_obj.get('IBAN') or seller_obj.get('iban')
            
            client_obj = data.get('Client') or data.get('client')
            if isinstance(client_obj, dict):
                cleaned_data['customer_name'] = str(client_obj.get('Name') or client_obj.get('name') or '').strip()
                cleaned_data['customer_address'] = str(client_obj.get('Address') or client_obj.get('address') or '').strip()
                cleaned_data['client_iban'] = client_obj.get('IBAN') or client_obj.get('iban')
            
            # --- Numeric fields ---
            numeric_synonyms = {
                'total_amount': ['total_amount', 'totalamount', 'total', 'grand_total', 'amount_due', 'gross_worth'],
                'subtotal': ['subtotal', 'sub_total', 'net_worth'],
                'tax_amount': ['tax_amount', 'taxamount', 'tax', 'vat', 'gst'],
            }
            for field, synonyms in numeric_synonyms.items():
                for syn in synonyms:
                    if syn.lower() in data_lower:
                        val = data_lower[syn.lower()]
                        cleaned_val = self._clean_numeric(val)
                        if cleaned_val is not None:
                            cleaned_data[field] = cleaned_val
                            break
            
            # Simple IBAN-based correction: if Seller has no IBAN but Client has IBAN, swap
            seller_iban = cleaned_data.get('vendor_iban')
            client_iban = cleaned_data.get('client_iban')
            
            if (seller_iban is None or seller_iban == 'null' or seller_iban == '') and \
               (client_iban is not None and client_iban != 'null' and client_iban != ''):
                # Swap vendor and customer
                cleaned_data['vendor_name'], cleaned_data['customer_name'] = \
                    cleaned_data.get('customer_name'), cleaned_data.get('vendor_name')
                cleaned_data['vendor_address'], cleaned_data['customer_address'] = \
                    cleaned_data.get('customer_address'), cleaned_data.get('vendor_address')
                # Also swap IBANs
                cleaned_data['vendor_iban'] = client_iban
                cleaned_data['client_iban'] = seller_iban
            
            # Remove the temporary IBAN fields so they don't appear in output
            cleaned_data.pop('vendor_iban', None)
            cleaned_data.pop('client_iban', None)
            
            # If subtotal and tax are present, compute total if missing
            if cleaned_data.get('subtotal') is not None and cleaned_data.get('tax_amount') is not None:
                if cleaned_data.get('total_amount') is None or abs(cleaned_data['total_amount']) < 0.01:
                    cleaned_data['total_amount'] = cleaned_data['subtotal'] + cleaned_data['tax_amount']
            
            return cleaned_data
            
        except json.JSONDecodeError:
            return self._extract_manually(response_text)
        except Exception as e:
            print(f"   ⚠️ Parse error: {e}")
            return {"_raw": response_text, "_error": str(e)}
    
    def _extract_manually(self, text: str) -> Dict[str, Any]:
        data = {}
        patterns = {
            'invoice_number': r'[Ii]nvoice\s*(?:#|Number)?\s*[:]?\s*([A-Z0-9\-]+)',
            'invoice_date': r'[Dd]ate\s*[:]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'due_date': r'[Dd]ue\s*[Dd]ate\s*[:]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'vendor_name': r'[Vv]endor\s*[:]?\s*([A-Za-z\s,]+)',
            'vendor_address': r'[Vv]endor\s*[Aa]ddress\s*[:]?\s*([A-Za-z0-9\s,]+)',
            'customer_name': r'[Cc]lient\s*[:]?\s*([A-Za-z\s,]+)',
            'customer_address': r'[Cc]lient\s*[Aa]ddress\s*[:]?\s*([A-Za-z0-9\s,]+)',
            'total_amount': r'[Tt]otal\s*[:]?\s*[\$]?\s*([\d,\.\s]+)',
            'subtotal': r'[Ss]ubtotal\s*[:]?\s*[\$]?\s*([\d,\.\s]+)',
            'tax_amount': r'[Tt]ax\s*[:]?\s*[\$]?\s*([\d,\.\s]+)',
            'currency': r'([\$€£])',
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if field in ['total_amount', 'subtotal', 'tax_amount']:
                    try:
                        data[field] = float(re.sub(r'[$,]', '', value))
                    except:
                        data[field] = value
                elif field == 'currency':
                    data[field] = self._clean_currency(value)
                else:
                    data[field] = value
        return data
    
    def _clean_numeric(self, value) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r'[$,€£]', '', value)
            cleaned = cleaned.replace(' ', '')
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace(',', '')
            try:
                return float(cleaned)
            except:
                return None
        return None
    
    def _clean_currency(self, currency: str) -> str:
        if not currency:
            return None
        curr = str(currency).strip()
        currency_map = {
            'us dollar': '$', 'usd': '$', 'dollar': '$', 'usdollar': '$',
            'euro': '€', 'eur': '€', 'european': '€',
            'pound': '£', 'gbp': '£', 'british': '£',
            'yen': '¥', 'jpy': '¥', 'yuan': '¥',
        }
        curr_lower = curr.lower()
        for key, symbol in currency_map.items():
            if key in curr_lower:
                return symbol
        if len(curr) == 1 and curr in ['$', '€', '£', '¥']:
            return curr
        for sym in ['$', '€', '£', '¥']:
            if sym in curr:
                return sym
        if len(curr) == 3 and curr.isalpha():
            return curr.upper()
        return curr
    
    # ============================================================
    # ADDED: _load_images method (was missing)
    # ============================================================
    def _load_images(self, file_path: str):
        """Load image(s) from file (supports PDF and common image formats)"""
        images = []
        if file_path.lower().endswith('.pdf'):
            try:
                pdf_images = pdf2image.convert_from_path(file_path)
                images.extend(pdf_images)
                logger.info(f"Converted PDF to {len(pdf_images)} images")
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
                return []
        else:
            try:
                images.append(Image.open(file_path))
            except Exception as e:
                logger.error(f"Could not load image: {e}")
                return []
        return images