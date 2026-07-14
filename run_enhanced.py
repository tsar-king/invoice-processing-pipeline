#!/usr/bin/env python3
"""
Enhanced Invoice Processing Pipeline Runner
Supports batch processing, retries, progress tracking, and Excel export
"""

import sys
import argparse
from pathlib import Path
from src.logger import logger
from src.batch_processor import run_batch_processing
from src.excel_exporter import export_to_excel
from src.pipeline import InvoicePipeline
import config

def main():
    """Main entry point with command line arguments"""
    
    parser = argparse.ArgumentParser(
        description="AI Invoice Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enhanced.py                  # Process all invoices with batch processing
  python run_enhanced.py --batch-size 10  # Process with batch size 10
  python run_enhanced.py --excel-only     # Only export Excel from existing data
  python run_enhanced.py --single invoice_0.jpg  # Process single invoice
        """
    )
    
    parser.add_argument(
        '--batch-size', type=int, default=5,
        help='Number of invoices per batch (default: 5)'
    )
    parser.add_argument(
        '--max-retries', type=int, default=3,
        help='Maximum retries per invoice (default: 3)'
    )
    parser.add_argument(
        '--excel-only', action='store_true',
        help='Only export Excel from existing data, skip processing'
    )
    parser.add_argument(
        '--single', type=str,
        help='Process a single invoice file'
    )
    parser.add_argument(
        '--dashboard', action='store_true',
        help='Generate dashboard after processing'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 ENHANCED INVOICE PROCESSING PIPELINE")
    print("="*60)
    print(f"📌 Model: {config.MODEL_NAME}")
    print(f"📁 Input: {config.INPUT_FOLDER}")
    print(f"📁 Output: {config.OUTPUT_FOLDER}")
    print("="*60)
    
    # Excel-only mode
    if args.excel_only:
        logger.info("Excel-only mode: exporting from existing data")
        file_path = export_to_excel()
        if file_path:
            print(f"\n✅ Excel report saved: {file_path}")
        return
    
    # Single invoice mode
    if args.single:
        logger.info(f"Single invoice mode: processing {args.single}")
        pipeline = InvoicePipeline()
        result = pipeline.processor.process_invoice(args.single)
        
        # Validate
        from src.validator import InvoiceValidator
        validation = InvoiceValidator.validate(result)
        
        print("\n📊 Result:")
        for key, value in result.items():
            if not key.startswith('_'):
                print(f"   {key}: {value}")
        
        print(f"\n📊 Validation Score: {validation['score']:.0%}")
        return
    
    # Batch processing mode
    logger.info("Starting batch processing...")
    
    # Update config with command line args
    config.BATCH_SIZE = args.batch_size
    config.MAX_RETRIES = args.max_retries
    
    # Run batch processing
    from src.batch_processor import BatchProcessor
    processor = BatchProcessor(batch_size=args.batch_size, max_retries=args.max_retries)
    summary = processor.process_all()
    processor.print_summary(summary)
    
    # Export to Excel
    if summary.get('successful', 0) > 0:
        logger.info("Exporting results to Excel...")
        excel_path = export_to_excel()
        if excel_path:
            print(f"\n📊 Excel report: {excel_path}")
    
    # Generate dashboard if requested
    if args.dashboard:
        logger.info("Generating dashboard...")
        try:
            import dashboard
            dashboard.create_dashboard()
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Processing complete!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)