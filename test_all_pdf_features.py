#!/usr/bin/env python3
"""
Comprehensive test script for PDF enhancements (Phases 2-4).
Tests all implemented features including headers, footers, clickable URLs, and enhanced tables.
"""

from pathlib import Path
from doc_generator.infrastructure.generators.pdf.generator import PDFGenerator

# Create test markdown content with all features
test_markdown = """# Advanced PDF Features Test

## Introduction

This document tests all the **enhanced PDF features** including:
- Table of Contents with reading time
- Code blocks with line numbers
- Headers and footers with page numbers
- Clickable URLs and links
- Enhanced table formatting

For more information, visit [Google](https://www.google.com) or check out [GitHub](https://github.com).

## Code Examples

Here's some Python code with line numbers:

```python
def calculate_fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    # Test the function
    for i in range(10):
        result = calculate_fibonacci(i)
        print(f"F({i}) = {result}")

if __name__ == "__main__":
    main()
```

### JavaScript Example

```javascript
function fetchData(url) {
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Data received:', data);
            return data;
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
```

## Performance Metrics

Here's a table with enhanced formatting:

| Feature | Status | Performance | Score |
|---------|--------|-------------|-------|
| TOC | Yes | Excellent | 95% |
| Code Blocks | Yes | High | 92% |
| Headers/Footers | Yes | Good | 88% |
| Clickable URLs | Yes | Excellent | 98% |
| Tables | Yes | High | 90% |
| Metadata | Yes | Good | 85% |

## Test Results

| Test Case | Result | Notes |
|-----------|--------|-------|
| Reading Time | Pass | Calculated correctly |
| Line Numbers | Pass | All lines numbered |
| Page Numbers | Pass | Appears on all pages |
| URL Links | Pass | All links clickable |
| Visual Indicators | Pass | ✓/✗ symbols work |

## Additional Content

This section adds more content to test pagination and ensure the headers/footers appear correctly across multiple pages.

### Subsection 1: Lorem Ipsum

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Subsection 2: More Content

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

### Subsection 3: Testing Pagination

This content ensures we have enough text to span multiple pages, which will help us verify that:
1. Headers appear on each page
2. Footers appear on each page
3. Page numbers increment correctly
4. Section titles update in headers

## Conclusion

This comprehensive test document validates all the PDF enhancements:
- ✅ Enhanced Table of Contents
- ✅ Code blocks with line numbers
- ✅ Document metadata
- ✅ Headers and footers
- ✅ Clickable URLs
- ✅ Enhanced table formatting

Visit [our documentation](https://example.com/docs) for more details.
"""

# Create metadata with all fields
metadata = {
    "title": "PDF Enhancements Test - Complete",
    "subtitle": "Testing All Features (Phases 2-4)",
    "author": "PDF Enhancement Team",
    "keywords": ["pdf", "enhancements", "testing", "headers", "footers", "urls"],
    "generated_date": "2026-01-13",
    "content_type": "technical_documentation"
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
    print("\n🎯 Features to verify:")
    print("  1. ✓ Table of Contents with reading time")
    print("  2. ✓ Code blocks with line numbers")
    print("  3. ✓ Headers on each page (except cover)")
    print("  4. ✓ Footers with date on each page")
    print("  5. ✓ Page numbers in headers")
    print("  6. ✓ Clickable URLs (blue and underlined)")
    print("  7. ✓ Enhanced tables with ✓/✗ indicators")
    print("  8. ✓ Color-coded performance metrics")
    print("  9. ✓ PDF metadata (check File → Properties)")
    print("\n📖 Open the PDF to verify all features!")
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
