#!/usr/bin/env python3
"""
Quick test script to verify PDF enhancements.
Tests TOC with reading time and code blocks with line numbers.
"""

from pathlib import Path
from doc_generator.infrastructure.generators.pdf.generator import PDFGenerator

# Create test markdown content
test_markdown = """# Test Document

## Introduction

This is a test document to verify the PDF enhancements.

## Code Example

Here's some Python code:

```python
def hello_world():
    print("Hello, World!")
    return 42

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the functions
result = hello_world()
print(f"Result: {result}")
```

## Another Section

This section has more content to test the reading time calculation.

### Subsection 1

Some content here.

### Subsection 2

More content to make the document longer and test the TOC depth filtering.

## Conclusion

This concludes our test document.
"""

# Create metadata
metadata = {
    "title": "PDF Enhancement Test",
    "subtitle": "Testing TOC and Code Block Features",
    "author": "Test Author",
    "keywords": ["test", "pdf", "enhancements"],
    "generated_date": "2026-01-13"
}

# Create content dict
content = {
    "markdown": test_markdown,
    "section_images": {}
}

# Generate PDF
output_dir = Path("src/output/test")
output_dir.mkdir(parents=True, exist_ok=True)

generator = PDFGenerator()
try:
    pdf_path = generator.generate(content, metadata, output_dir)
    print(f"✅ PDF generated successfully: {pdf_path}")
    print(f"📄 File size: {pdf_path.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
