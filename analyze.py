#!/usr/bin/env python3
import os
import re
import sys
from collections import defaultdict

def analyze_includes(root_dir):
    """Analyze all source files for potentially incorrect local header includes"""
    # Common kernel system include patterns (won't fix these)
    SYSTEM_INCLUDES = [
        r'^linux/', r'^asm/', r'^uapi/', r'^media/', 
        r'^sound/', r'^drm/', r'^net/', r'^scsi/'
    ]
    
    # Track potential fixes
    fixes = defaultdict(list)
    total_files = 0
    analyzed_files = 0
    
    print(f"Scanning {root_dir} for include issues...")
    
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
                
                # Skip absolute paths and system includes
                if header.startswith('/') or any(re.match(pattern, header) for pattern in SYSTEM_INCLUDES):
                    continue
                    
                # Check if header exists locally
                local_path = os.path.normpath(os.path.join(dirpath, header))
                if os.path.exists(local_path):
                    # Verify it's not a system header (double-check)
                    if not is_system_header(header, root_dir):
                        fixes[filepath].append((lineno, line.strip(), header))
    
    print(f"Analyzed {analyzed_files} source files out of {total_files} total files")
    return fixes

def is_system_header(header, kernel_root):
    """Check if header exists in kernel's standard include paths"""
    system_paths = [
        os.path.join(kernel_root, 'include'),
        os.path.join(kernel_root, 'arch', os.path.basename(kernel_root), 'include'),
        os.path.join(kernel_root, 'arch', os.path.basename(kernel_root), 'include', 'generated')
    ]
    
    for path in system_paths:
        if os.path.exists(os.path.join(path, header)):
            return True
    return False

def print_dry_run(fixes):
    """Print analysis results and get user confirmation"""
    if not fixes:
        print("\n✅ No issues found! All local includes appear correct.")
        return False
    
    print(f"\n⚠️ Found {sum(len(v) for v in fixes.values())} potential issues across {len(fixes)} files")
    
    # Show examples
    print("\nExamples of issues found:")
    for i, (filepath, issues) in enumerate(list(fixes.items())[:3]):
        rel_path = os.path.relpath(filepath)
        print(f"\n  {rel_path}:")
        for lineno, line, header in issues[:2]:
            print(f"    Line {lineno+1}: {line}")
            print(f"      → Should use: #include \"{header}\"")
        if len(issues) > 2:
            print(f"    ... and {len(issues)-2} more issues in this file")
    
    if len(fixes) > 3:
        print(f"\n  ... and {len(fixes)-3} more files with issues")
    
    # Show summary
    print(f"\nTotal: {len(fixes)} files need fixing")
    
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
    print("\nApplying fixes...")
    files_fixed = 0
    
    for filepath, issues in fixes.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Process in reverse order to avoid line number shifts
            for lineno, old_line, header in sorted(issues, key=lambda x: x[0], reverse=True):
                new_line = old_line.replace(f'<{header}>', f'"{header}"', 1)
                lines[lineno] = lines[lineno].replace(old_line, new_line, 1)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            files_fixed += 1
            if files_fixed % 10 == 0:
                print(f"  Fixed {files_fixed} files...", end='\r')
                
        except Exception as e:
            print(f"\n❌ Error fixing {filepath}: {str(e)}")
    
    print(f"\n✅ Successfully fixed {files_fixed} files")

def main():
    kernel_root = os.path.abspath(os.getcwd())
    
    # Verify we're in a kernel tree
    if not os.path.exists(os.path.join(kernel_root, 'Makefile')) or \
       not os.path.exists(os.path.join(kernel_root, 'include', 'linux')):
        print("Error: Not in a Linux kernel source directory")
        print("Please run this script from the root of your kernel source tree")
        sys.exit(1)
    
    fixes = analyze_includes(kernel_root)
    
    if not fixes:
        sys.exit(0)
    
    if print_dry_run(fixes):
        apply_fixes(fixes)
        print("\n💡 Tip: Consider adding this to your build process:")
        print("    find . -name '*.[ch]' | xargs sed -i 's|#include <\\(mtk-[^>]\\+\\)>|#include \"\\1\"|g'")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
