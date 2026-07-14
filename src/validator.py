# src/validator.py
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple

class InvoiceValidator:
    """Validate and score extracted invoice data"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all validations and return results"""
        results = {
            "is_valid": True,
            "score": 0.0,
            "warnings": [],
            "errors": [],
            "fields": {}
        }
        
        # Validate each field
        results["fields"]["invoice_number"] = InvoiceValidator._validate_invoice_number(data.get("invoice_number"))
        results["fields"]["invoice_date"] = InvoiceValidator._validate_date(data.get("invoice_date"))
        results["fields"]["total_amount"] = InvoiceValidator._validate_amount(data.get("total_amount"))
        results["fields"]["vendor_name"] = InvoiceValidator._validate_name(data.get("vendor_name"), "vendor")
        results["fields"]["customer_name"] = InvoiceValidator._validate_name(data.get("customer_name"), "customer")
        results["fields"]["currency"] = InvoiceValidator._validate_currency(data.get("currency"))
        
        # Collect warnings and errors
        for field, result in results["fields"].items():
            if result.get("warning"):
                results["warnings"].append(f"{field}: {result['warning']}")
            if result.get("error"):
                results["errors"].append(f"{field}: {result['error']}")
        
        # Calculate confidence score
        field_scores = []
        for field, result in results["fields"].items():
            if result.get("score") is not None:
                field_scores.append(result["score"])
        
        if field_scores:
            results["score"] = sum(field_scores) / len(field_scores)
        else:
            results["score"] = 0.0
        
        # Mark invalid if errors exist
        if results["errors"]:
            results["is_valid"] = False
        
        return results
    
    @staticmethod
    def _validate_invoice_number(value) -> Dict[str, Any]:
        result = {"value": value, "score": 1.0}
        if not value:
            result["error"] = "Missing invoice number"
            result["score"] = 0.0
        elif len(str(value)) < 3:
            result["warning"] = "Invoice number seems too short"
            result["score"] = 0.5
        return result
    
    @staticmethod
    def _validate_date(value) -> Dict[str, Any]:
        result = {"value": value, "score": 1.0}
        if not value:
            result["error"] = "Missing date"
            result["score"] = 0.0
            return result
        
        date_str = str(value)
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%b %d, %Y']:
            try:
                datetime.strptime(date_str, fmt)
                return result
            except:
                continue
        
        result["warning"] = f"Unusual date format: {date_str}"
        result["score"] = 0.5
        return result
    
    @staticmethod
    def _validate_amount(value) -> Dict[str, Any]:
        result = {"value": value, "score": 1.0}
        if value is None:
            result["error"] = "Missing amount"
            result["score"] = 0.0
            return result
        
        try:
            amount = float(value)
            if amount <= 0:
                result["error"] = "Amount must be positive"
                result["score"] = 0.0
            elif amount > 1000000:
                result["warning"] = "Amount seems unusually high"
                result["score"] = 0.5
        except:
            result["error"] = "Invalid amount format"
            result["score"] = 0.0
        
        return result
    
    @staticmethod
    def _validate_name(value: str, field: str) -> Dict[str, Any]:
        result = {"value": value, "score": 1.0}
        if not value:
            result["error"] = f"Missing {field} name"
            result["score"] = 0.0
        elif len(str(value)) < 2:
            result["warning"] = f"{field} name seems too short"
            result["score"] = 0.5
        return result
    
    @staticmethod
    def _validate_currency(value: str) -> Dict[str, Any]:
        result = {"value": value, "score": 1.0}
        if not value:
            result["warning"] = "Missing currency"
            result["score"] = 0.5
        elif value not in ['$', '€', '£', '¥'] and len(value) > 3:
            result["warning"] = f"Unusual currency: {value}"
            result["score"] = 0.5
        return result