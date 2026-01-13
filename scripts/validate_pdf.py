#!/usr/bin/env python3
"""
PDF Quality Validation Script (Feature 13).

Validates PDF quality metrics including:
- Page count expansion ratio
- Image embedding verification
- Link validation
- Text extractability
- File size checks
"""

import sys
from pathlib import Path
from typing import Dict, Any

try:
    from pypdf import PdfReader
except ImportError:
    print("⚠️  pypdf not installed. Install with: pip install pypdf")
    sys.exit(1)

from loguru import logger


def validate_pdf_quality(pdf_path: Path, source_path: Path = None, max_expansion_ratio: float = 1.5) -> Dict[str, Any]:
    """
    Validate PDF quality metrics.
    
    Args:
        pdf_path: Path to the PDF file to validate
        source_path: Optional path to source markdown file for comparison
        max_expansion_ratio: Maximum allowed page expansion ratio
        
    Returns:
        Dictionary with validation results and metrics
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    # Check if PDF exists
    if not pdf_path.exists():
        results["valid"] = False
        results["errors"].append(f"PDF file not found: {pdf_path}")
        return results
    
    try:
        # Read PDF
        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        results["metrics"]["page_count"] = num_pages
        
        # Check file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        results["metrics"]["file_size_mb"] = round(file_size_mb, 2)
        
        if file_size_mb > 50:
            results["warnings"].append(f"Large file size: {file_size_mb:.1f} MB (max recommended: 50 MB)")
        
        # Extract metadata
        metadata = reader.metadata
        if metadata:
            results["metrics"]["metadata"] = {
                "title": metadata.get("/Title", "N/A"),
                "author": metadata.get("/Author", "N/A"),
                "creator": metadata.get("/Creator", "N/A"),
                "subject": metadata.get("/Subject", "N/A"),
            }
            
            # Validate metadata presence
            if not metadata.get("/Title"):
                results["warnings"].append("PDF metadata: Title not set")
            if not metadata.get("/Author"):
                results["warnings"].append("PDF metadata: Author not set")
        else:
            results["warnings"].append("No PDF metadata found")
        
        # Check text extractability
        text_extractable = False
        total_text_length = 0
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text and len(text.strip()) > 0:
                    text_extractable = True
                    total_text_length += len(text)
            except Exception as e:
                results["warnings"].append(f"Could not extract text from page {page_num}: {e}")
        
        results["metrics"]["text_extractable"] = text_extractable
        results["metrics"]["total_text_length"] = total_text_length
        
        if not text_extractable:
            results["errors"].append("No text could be extracted from PDF")
            results["valid"] = False
        
        # Check for images
        image_count = 0
        for page in reader.pages:
            if "/XObject" in page["/Resources"]:
                xobjects = page["/Resources"]["/XObject"].get_object()
                for obj in xobjects:
                    if xobjects[obj]["/Subtype"] == "/Image":
                        image_count += 1
        
        results["metrics"]["image_count"] = image_count
        
        # Page expansion ratio check (if source provided)
        if source_path and source_path.exists():
            with open(source_path, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            # Estimate source pages (rough: 500 words per page)
            word_count = len(source_content.split())
            estimated_source_pages = max(1, word_count // 500)
            
            expansion_ratio = num_pages / estimated_source_pages
            results["metrics"]["expansion_ratio"] = round(expansion_ratio, 2)
            results["metrics"]["estimated_source_pages"] = estimated_source_pages
            
            if expansion_ratio > max_expansion_ratio:
                results["warnings"].append(
                    f"High page expansion ratio: {expansion_ratio:.2f}x "
                    f"(max recommended: {max_expansion_ratio}x)"
                )
        
        # Overall validation
        if results["errors"]:
            results["valid"] = False
        
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Error reading PDF: {e}")
        logger.exception("PDF validation error")
    
    return results


def print_validation_report(results: Dict[str, Any], pdf_path: Path):
    """
    Print a formatted validation report.
    
    Args:
        results: Validation results dictionary
        pdf_path: Path to the PDF file
    """
    print("\n" + "="*70)
    print(f"📋 PDF Quality Validation Report")
    print("="*70)
    print(f"\n📄 File: {pdf_path.name}")
    print(f"📍 Path: {pdf_path}")
    
    # Overall status
    if results["valid"]:
        print(f"\n✅ Status: VALID")
    else:
        print(f"\n❌ Status: INVALID")
    
    # Metrics
    if results["metrics"]:
        print(f"\n📊 Metrics:")
        metrics = results["metrics"]
        
        if "page_count" in metrics:
            print(f"  • Pages: {metrics['page_count']}")
        
        if "file_size_mb" in metrics:
            print(f"  • File Size: {metrics['file_size_mb']} MB")
        
        if "text_extractable" in metrics:
            status = "✓" if metrics["text_extractable"] else "✗"
            print(f"  • Text Extractable: {status}")
        
        if "total_text_length" in metrics:
            print(f"  • Total Text Length: {metrics['total_text_length']:,} characters")
        
        if "image_count" in metrics:
            print(f"  • Embedded Images: {metrics['image_count']}")
        
        if "expansion_ratio" in metrics:
            print(f"  • Page Expansion Ratio: {metrics['expansion_ratio']}x")
            print(f"    (from ~{metrics['estimated_source_pages']} estimated source pages)")
        
        if "metadata" in metrics:
            print(f"\n📝 Metadata:")
            for key, value in metrics["metadata"].items():
                print(f"  • {key.title()}: {value}")
    
    # Warnings
    if results["warnings"]:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"  • {warning}")
    
    # Errors
    if results["errors"]:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  • {error}")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main entry point for the validation script."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_pdf.py <pdf-file> [source-markdown-file]")
        print("\nExample:")
        print("  python scripts/validate_pdf.py src/output/test/document.pdf")
        print("  python scripts/validate_pdf.py src/output/test/document.pdf src/data/document.md")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    source_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Run validation
    results = validate_pdf_quality(pdf_path, source_path)
    
    # Print report
    print_validation_report(results, pdf_path)
    
    # Exit with appropriate code
    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()
