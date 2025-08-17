#!/usr/bin/env python3
import os
import re
import sys
from collections import defaultdict

def analyze_includes(root_dir):
    """Analyze all source files for incorrectly included same-directory headers"""
    fixes = defaultdict(list)
    total_files = 0
    analyzed_files = 0
    
    print(f"Scanning {root_dir} for same-directory include issues...")
    
    for dirpath, _, filenames in os.walk(root_dir):
        total_files += len(filenames)
        for filename in filenames:
            if not filename.endswith(('.c', '.h', '.S')):
                continue
                
            analyzed_files += 1
            filepath = os.path.join(dirpath, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue
                
            for lineno, line in enumerate(lines):
                # Match #include <header> patterns
                match = re.search(r'#include\s*<([^>]+)>', line)
                if not match:
                    continue
                    
                header = match.group(1).strip()
                
                # CRITICAL: Only consider headers WITHOUT directory separators
                if '/' in header or '\\' in header:
                    continue  # Skip subdirectory headers like "cluster/masklog.h"
                
                # Skip absolute paths
                if header.startswith('/'):
                    continue
                    
                # Check if header exists in SAME directory
                local_path = os.path.join(dirpath, header)
                if os.path.exists(local_path):
                    fixes[filepath].append((lineno, line.strip(), header))
    
    print(f"Analyzed {analyzed_files} source files out of {total_files} total files")
    return fixes

def print_dry_run(fixes):
    """Print analysis results and get user confirmation"""
    if not fixes:
        print("\n✅ No same-directory include issues found!")
        return False
    
    print(f"\n⚠️ Found {sum(len(v) for v in fixes.values())} potential same-directory issues across {len(fixes)} files")
    
    # Show examples
    print("\nExamples of issues found (ONLY same-directory headers):")
    examples_shown = 0
    for filepath, issues in list(fixes.items())[:5]:
        rel_path = os.path.relpath(filepath)
        for lineno, line, header in issues:
            # Verify it's truly same-directory
            if '/' not in header and '\\' not in header:
                print(f"\n  {rel_path}:")
                print(f"    Line {lineno+1}: {line}")
                print(f"      → Should use: #include \"{header}\"")
                examples_shown += 1
                if examples_shown >= 3:
                    break
        if examples_shown >= 3:
            break
    
    if len(fixes) > 5:
        print(f"\n  ... and {len(fixes)-5} more files with issues")
    
    print(f"\nTotal same-directory issues: {sum(len(v) for v in fixes.values())}")
    print("Note: Subdirectory headers (e.g., <cluster/file.h>) are intentionally NOT fixed")
    
    while True:
        response = input("\nApply fixes? (y/n) [n]: ").strip().lower()
        if response in ('', 'n'):
            print("Aborted. No changes made.")
            return False
        if response == 'y':
            return True
        print("Please enter 'y' or 'n'")

def apply_fixes(fixes):
    """Apply the include fixes to source files"""
    print("\nApplying fixes to same-directory headers...")
    files_fixed = 0
    issues_fixed = 0
    
    for filepath, issues in fixes.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Process in reverse order to avoid line number shifts
            for lineno, old_line, header in sorted(issues, key=lambda x: x[0], reverse=True):
                new_line = old_line.replace(f'<{header}>', f'"{header}"', 1)
                lines[lineno] = lines[lineno].replace(old_line, new_line, 1)
                issues_fixed += 1
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            files_fixed += 1
            
        except Exception as e:
            print(f"\n❌ Error fixing {filepath}: {str(e)}")
    
    print(f"\n✅ Successfully fixed {issues_fixed} same-directory includes across {files_fixed} files")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print("Usage: fix-same-dir-includes.py [kernel_root]")
        print("Analyzes and fixes ONLY same-directory header includes (e.g., <file.h> → \"file.h\")")
        print("Subdirectory headers (e.g., <sub/file.h>) are intentionally NOT modified")
        sys.exit(0)
    
    kernel_root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    
    # Verify we're in a kernel tree
    if not os.path.exists(os.path.join(kernel_root, 'Makefile')) or \
       not os.path.exists(os.path.join(kernel_root, 'include', 'linux')):
        print("Error: Not in a Linux kernel source directory")
        print("Please run this script from the root of your kernel source tree")
        sys.exit(1)
    
    fixes = analyze_includes(kernel_root)
    
    if not fixes:
        print("\nNo same-directory include issues found. Nothing to fix.")
        sys.exit(0)
    
    if print_dry_run(fixes):
        apply_fixes(fixes)
        print("\n💡 Tip: This only fixes same-directory headers. Subdirectory headers are correct as-is.")
        print("    Example of what WAS fixed: #include <mtk-hcp.h> → #include \"mtk-hcp.h\"")
        print("    Example of what WAS NOT fixed: #include <cluster/masklog.h> (correct as-is)")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
