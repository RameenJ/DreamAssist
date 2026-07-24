#!/usr/bin/env python3
"""Fix indentation in progress_tracker.py - add 4 spaces to method bodies"""

with open('services/progress_tracker.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
in_method = False
method_indent_level = 0

for i, line in enumerate(lines):
    # Detect class method definitions (4 spaces + async/def)
    if (line.startswith('    async def ') or line.startswith('    def ')) and not line.startswith('        '):
        in_method = True
        fixed_lines.append(line)
        continue
    
    # If we're in a method, check if we should be fixing indentation
    if in_method:
        # Check if this line starts a new method at the same level (4 spaces)
        if (line.startswith('    async def ') or line.startswith('    def ')) and not line.startswith('        '):
            in_method = True
            fixed_lines.append(line)
            continue
        
        # Check if we've reached the PlanAnalytics class definition (end of AdaptiveTracker)
        if line.startswith('class '):
            in_method = False
            fixed_lines.append(line)
            continue
        
        # Fix docstring lines (they should have 8 spaces, add 4 if they have 4)
        if line.startswith('    """') and not line.startswith('        '):
            fixed_lines.append('    ' + line)
            continue
        
        # Fix code lines (add 4 spaces if they start with 4 spaces and aren't already at 8+)
        if line.startswith('    ') and not line.startswith('        ') and line.strip():
            # This line has 4 spaces but should have 8
            fixed_lines.append('    ' + line)
            continue
        
        # Keep empty lines and already correct lines as-is
        fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('services/progress_tracker.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('✅ Fixed indentation in method bodies')
