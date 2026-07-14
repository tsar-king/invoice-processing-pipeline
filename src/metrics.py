# src/metrics.py
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class PipelineMetrics:
    """Track and report pipeline performance"""
    
    def __init__(self):
        self._reset()
    
    def _reset(self):
        self.metrics = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "processing_times": [],
            "field_extraction": {},
            "start_time": None,
            "end_time": None,
            "errors": []
        }
    
    def start(self):
        self.metrics["start_time"] = datetime.now().isoformat()
    
    def stop(self):
        self.metrics["end_time"] = datetime.now().isoformat()
    
    def record(self, success: bool, time_taken: float, fields: Dict[str, Any], error: Optional[str] = None):
        """Record a single invoice processing result"""
        self.metrics["total"] += 1
        if success:
            self.metrics["successful"] += 1
        else:
            self.metrics["failed"] += 1
            if error:
                self.metrics["errors"].append(error)
        
        self.metrics["processing_times"].append(time_taken)
        
        # Track field extraction rates
        for field, value in fields.items():
            if field not in self.metrics["field_extraction"]:
                self.metrics["field_extraction"][field] = {"found": 0, "total": 0}
            self.metrics["field_extraction"][field]["total"] += 1
            if value and value != "N/A" and value != "null":
                self.metrics["field_extraction"][field]["found"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        total = self.metrics["total"]
        if total == 0:
            return {"error": "No invoices processed"}
        
        times = self.metrics["processing_times"]
        
        # Calculate field extraction rates
        field_rates = {}
        for field, data in self.metrics["field_extraction"].items():
            rate = (data["found"] / data["total"]) * 100 if data["total"] > 0 else 0
            field_rates[field] = round(rate, 2)
        
        summary = {
            "total_invoices": total,
            "successful": self.metrics["successful"],
            "failed": self.metrics["failed"],
            "success_rate": round((self.metrics["successful"] / total) * 100, 2),
            "avg_processing_time": round(sum(times) / len(times), 2) if times else 0,
            "min_processing_time": round(min(times), 2) if times else 0,
            "max_processing_time": round(max(times), 2) if times else 0,
            "field_extraction_rates": field_rates,
            "start_time": self.metrics["start_time"],
            "end_time": self.metrics["end_time"],
            "errors": self.metrics["errors"]
        }
        return summary
    
    def save(self, filepath: str = "output_data/metrics.json"):
        """Save metrics to JSON file"""
        Path(filepath).parent.mkdir(exist_ok=True)
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def print_summary(self):
        """Print a formatted summary to console"""
        summary = self.get_summary()
        if "error" in summary:
            print(f"❌ {summary['error']}")
            return
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE METRICS")
        print("="*60)
        print(f"📁 Total Invoices: {summary['total_invoices']}")
        print(f"✅ Successful: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']}%")
        print(f"\n⏱️  Average Time: {summary['avg_processing_time']}s")
        print(f"   Min Time: {summary['min_processing_time']}s")
        print(f"   Max Time: {summary['max_processing_time']}s")
        
        print("\n📋 Field Extraction Rates:")
        for field, rate in summary["field_extraction_rates"].items():
            bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
            print(f"   {field:<20} {bar} {rate:.1f}%")
        
        if summary["errors"]:
            print(f"\n⚠️ Errors: {len(summary['errors'])}")