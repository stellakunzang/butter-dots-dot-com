#!/usr/bin/env python3
"""
Command-line spell checker for Tibetan text files.
Supports: .txt, .rtf
Usage: python check_file.py <input_file>
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.spellcheck.engine import TibetanSpellChecker

try:
    from striprtf.striprtf import rtf_to_text
    RTF_SUPPORT = True
except ImportError:
    RTF_SUPPORT = False


def format_error(error, text):
    """Format an error with context for display."""
    position = error['position']
    word = error['word']
    error_type = error['error_type']
    severity = error['severity']
    
    # Get surrounding context (20 chars before and after)
    start = max(0, position - 20)
    end = min(len(text), position + len(word) + 20)
    context = text[start:end]
    
    # Highlight the error word
    word_start = position - start
    word_end = word_start + len(word)
    highlighted = (
        context[:word_start] + 
        f"[{context[word_start:word_end]}]" + 
        context[word_end:]
    )
    
    severity_emoji = {
        'critical': '🔴',
        'error': '🟡',
        'info': '🔵'
    }
    
    return (
        f"{severity_emoji.get(severity, '⚪')} {severity.upper()}: {error_type}\n"
        f"   Word: {word} (at position {position})\n"
        f"   Context: ...{highlighted}...\n"
    )


def read_file(file_path: Path) -> str:
    """Read text from file, supporting both .txt and .rtf formats."""
    suffix = file_path.suffix.lower()
    
    if suffix == '.rtf':
        if not RTF_SUPPORT:
            print("Error: RTF support not installed. Run: pip install striprtf")
            sys.exit(1)
        
        print(f"📖 Reading RTF file: {file_path}")
        rtf_content = file_path.read_text(encoding='utf-8')
        text = rtf_to_text(rtf_content)
        print(f"✅ RTF converted to plain text")
        return text
    
    elif suffix == '.txt' or suffix == '':
        print(f"📖 Reading text file: {file_path}")
        return file_path.read_text(encoding='utf-8')
    
    else:
        print(f"⚠️  Unknown file type '{suffix}', treating as plain text")
        return file_path.read_text(encoding='utf-8')


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_file.py <input_file>")
        print("Supported formats: .txt, .rtf")
        print("Example: python check_file.py test.txt")
        print("Example: python check_file.py document.rtf")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Read the file (handles both txt and rtf)
    text = read_file(input_file)
    
    if not text.strip():
        print("Error: File is empty or contains no text")
        sys.exit(1)
    
    print(f"📝 Text length: {len(text)} characters")
    print(f"🔍 Running spell checker...\n")
    
    # Run spell checker
    checker = TibetanSpellChecker()
    errors = checker.check_text(text)
    
    # Display results
    print("=" * 70)
    print(f"SPELL CHECK RESULTS")
    print("=" * 70)
    print(f"Total errors found: {len(errors)}\n")
    
    if not errors:
        print("✅ No errors found! The text looks good.")
    else:
        # Group by severity
        by_severity = {}
        for error in errors:
            severity = error.get('severity', 'unknown')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)
        
        # Display summary
        print("Summary by severity:")
        for severity in ['critical', 'error', 'info']:
            if severity in by_severity:
                print(f"  {severity.upper()}: {len(by_severity[severity])}")
        print()
        
        # Display each error
        print("Detailed errors:")
        print("-" * 70)
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. {format_error(error, text)}")
    
    print("=" * 70)
    print(f"✅ Spell check complete!")
    
    # Return exit code based on error count
    sys.exit(0 if len(errors) == 0 else 1)


if __name__ == "__main__":
    main()
