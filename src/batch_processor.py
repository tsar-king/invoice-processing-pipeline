# src/batch_processor.py - Batch Processing with Progress Bar
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from src.logger import logger
from src.pipeline import InvoicePipeline
import config

class BatchProcessor:
    """
    Process invoices in batches with progress tracking
    Handles retries, logging, and batch management
    """
    
    def __init__(self, batch_size: int = 5, max_retries: int = 3):
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.pipeline = InvoicePipeline()
        self.results = []
        self.failed = []
        self.processed_count = 0
        
        logger.info(f"BatchProcessor initialized with batch_size={batch_size}, max_retries={max_retries}")
    
    def process_invoice_with_retry(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single invoice with retry logic
        
        Args:
            file_path: Path to invoice file
            
        Returns:
            Dictionary with extracted data, or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Processing {file_path.name} (attempt {attempt}/{self.max_retries})")
                
                result = self.pipeline.processor.process_invoice(str(file_path))
                
                # Check if we got data
                has_data = any([
                    result.get('invoice_number'),
                    result.get('total_amount'),
                    result.get('vendor_name')
                ])
                
                if has_data:
                    logger.success(f"Successfully processed {file_path.name}")
                    return result
                else:
                    logger.warning(f"No data extracted from {file_path.name} (attempt {attempt})")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {str(e)}")
                
                if attempt < self.max_retries:
                    wait_time = attempt * 2  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to process {file_path.name} after {self.max_retries} attempts")
        
        return None
    
    def process_all(self) -> Dict[str, Any]:
        """
        Process all invoices in batches
        
        Returns:
            Dictionary with processing summary
        """
        # Get all invoice files
        invoice_files = self.pipeline._get_invoice_files()
        
        if not invoice_files:
            logger.warning("No invoice files found")
            return {"error": "No invoices found"}
        
        total = len(invoice_files)
        logger.info(f"Found {total} invoice(s) to process")
        
        # Create batches
        batches = [invoice_files[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        logger.info(f"Created {len(batches)} batch(es)")
        
        # Process each batch
        for batch_idx, batch in enumerate(batches, 1):
            logger.info(f"\n📦 Processing Batch {batch_idx}/{len(batches)} ({len(batch)} invoices)")
            print(f"\n{'='*60}")
            print(f"📦 BATCH {batch_idx}/{len(batches)}")
            print(f"{'='*60}")
            
            # Use tqdm for progress bar
            for file_path in tqdm(batch, desc=f"Batch {batch_idx}", unit="invoice"):
                self.processed_count += 1
                
                result = self.process_invoice_with_retry(file_path)
                
                if result:
                    # Add metadata
                    result['_filename'] = file_path.name
                    self.results.append(result)
                else:
                    self.failed.append(file_path.name)
                
                # Save progress after each invoice
                if self.processed_count % 5 == 0:
                    self._save_progress()
                    
        # Save results to CSV
        if self.results:
            import pandas as pd
            df = pd.DataFrame(self.results)
            csv_path = Path("output_data/all_invoices.csv")
            csv_path.parent.mkdir(exist_ok=True)
            df.to_csv(csv_path, index=False)
            logger.success(f"Saved {len(self.results)} invoices to {csv_path}")

        # Final save
        self._save_progress()
        
        return self._get_summary()
    
    def _save_progress(self):
        """Save progress to disk"""
        import json
        from datetime import datetime
        
        try:
            progress_file = Path("output_data/progress.json")
            progress_file.parent.mkdir(exist_ok=True)
            
            progress_data = {
                "processed": self.processed_count,
                "successful": len(self.results),
                "failed": len(self.failed),
                "last_updated": datetime.now().isoformat()
            }
            
            # Write to temp file first, then rename (avoids permission issues)
            temp_file = progress_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
            
            # Rename temp to actual (atomic operation)
            temp_file.replace(progress_file)
            
        except Exception as e:
            # Don't crash if progress can't be saved
            print(f"⚠️ Could not save progress: {e}")
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        total = self.processed_count
        
        summary = {
            "total_processed": total,
            "successful": len(self.results),
            "failed": len(self.failed),
            "success_rate": (len(self.results) / total * 100) if total > 0 else 0,
            "failed_files": self.failed,
            "results": self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print processing summary"""
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"📁 Total Invoices: {summary['total_processed']}")
        print(f"✅ Successful: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failed_files']:
            print("\n⚠️ Failed Files:")
            for file in summary['failed_files']:
                print(f"   - {file}")
        print("="*60)


def run_batch_processing():
    """Main entry point for batch processing"""
    # Create batch processor with settings from config
    batch_size = getattr(config, 'BATCH_SIZE', 5)
    max_retries = getattr(config, 'MAX_RETRIES', 3)
    
    processor = BatchProcessor(batch_size=batch_size, max_retries=max_retries)
    summary = processor.process_all()
    processor.print_summary(summary)
    
    return summary

if __name__ == "__main__":
    run_batch_processing()