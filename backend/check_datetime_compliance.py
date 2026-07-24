#!/usr/bin/env python3
"""
UTC DateTime Compliance Checker
Validates that all date/time operations in DreamAssist follow UTC standards
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Tuple


class DateTimeChecker:
    """Check codebase for UTC datetime compliance"""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.issues = []
        self.warnings = []
        self.compliant_files = []
    
    def check_file(self, filepath: Path) -> None:
        """Check a single Python file for datetime issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            file_issues = []
            
            # Check 1: date.today() - should be datetime.utcnow().date()
            for i, line in enumerate(lines, 1):
                if 'date.today()' in line and not line.strip().startswith('#'):
                    file_issues.append(
                        f"Line {i}: Found date.today() - use datetime.utcnow().date() instead\n  {line.strip()}"
                    )
            
            # Check 2: datetime.now() - should be datetime.utcnow()
            for i, line in enumerate(lines, 1):
                if 'datetime.now()' in line and not 'utcnow' in line and not line.strip().startswith('#'):
                    file_issues.append(
                        f"Line {i}: Found datetime.now() - use datetime.utcnow() instead\n  {line.strip()}"
                    )
            
            # Check 3: time object storage - should be converted to string
            for i, line in enumerate(lines, 1):
                # Look for patterns like: "start_time": time(...) without conversion
                if re.search(r'["\'](?:start_time|end_time|scheduled_time)["\'].*time\(\d+', line) and 'isoformat' not in line:
                    if 'TimeBlock' not in line and 'StudySession' not in line:  # Schema definitions are OK
                        self.warnings.append(
                            f"{filepath}:{i}: Possible raw time object storage\n  {line.strip()}"
                        )
            
            # Check 4: Direct date storage in MongoDB - should use datetime.combine
            for i, line in enumerate(lines, 1):
                if re.search(r'datetime\.combine\(.*time\.min\)', line):
                    # This is correct pattern
                    pass
                elif re.search(r'insert.*=.*date|update.*date', line) and 'datetime.combine' not in line:
                    if 'scheduled_date' in line or 'start_date' in line:
                        if '": {' not in line:  # Skip query filters
                            self.warnings.append(
                                f"{filepath}:{i}: Possible date storage without datetime conversion\n  {line.strip()}"
                            )
            
            if file_issues:
                self.issues.extend([f"{filepath}: {issue}" for issue in file_issues])
            elif self.should_check_file(filepath):
                self.compliant_files.append(str(filepath))
        
        except Exception as e:
            self.warnings.append(f"Error checking {filepath}: {e}")
    
    def should_check_file(self, filepath: Path) -> bool:
        """Determine if file should be checked"""
        return (
            filepath.suffix == '.py' and
            not filepath.name.startswith('test_') and
            'migrations' not in str(filepath) and
            '__pycache__' not in str(filepath)
        )
    
    def check_all(self) -> None:
        """Check all Python files in backend"""
        python_files = list(self.backend_path.rglob('*.py'))
        
        for filepath in python_files:
            if self.should_check_file(filepath):
                self.check_file(filepath)
    
    def print_report(self) -> int:
        """Print compliance report and return exit code"""
        print("=" * 70)
        print("UTC DATETIME COMPLIANCE CHECK")
        print("=" * 70)
        
        if self.issues:
            print(f"\n❌ ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  • {issue}")
        else:
            print("\n✅ No critical datetime issues found!")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        
        print(f"\n✅ Compliant files checked: {len(self.compliant_files)}")
        
        print("\n" + "=" * 70)
        print("STANDARDS APPLIED:")
        print("=" * 70)
        print("""
✓ All date comparisons use: datetime.utcnow().date()
✓ Date to datetime conversion: datetime.combine(date, time.min)
✓ Date range queries: time.min for start, time.max for end
✓ Time objects stored as: ISO format strings via .isoformat()
✓ No raw datetime.time objects stored directly in MongoDB
✓ Pydantic models handle string↔time conversion automatically
        """)
        
        return 1 if self.issues else 0


def main():
    """Main entry point"""
    backend_path = Path(__file__).parent
    
    checker = DateTimeChecker(str(backend_path))
    checker.check_all()
    
    exit_code = checker.print_report()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
