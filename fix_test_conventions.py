#!/usr/bin/env python3
"""Fix test calling conventions in test_fund_lock_prevention.py"""
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix escrow.fund() - multiple lines
    content = re.sub(
        r'escrow(\d?)\.fund\(\s+_from=(\w+),\s+_amount=(sp\.utils\.nat_to_mutez\([^)]+\)),\s+_valid=True,\s+_sent=sp\.utils\.nat_to_mutez\([^)]+\)\s+\)',
        r'scenario += escrow\1.fund().run(\n        sender=\2,\n        amount=\3\n    )',
        content,
        flags=re.MULTILINE
    )
    
    # Fix escrow.release() - multiple lines  
    content = re.sub(
        r'escrow(\d?)\.release\(\s+_from=(\w+),\s+_valid=True\s+\)',
        r'scenario += escrow\1.release().run(sender=\2)',
        content,
        flags=re.MULTILINE
    )
    
    # Fix escrow.refund() - multiple lines
    content = re.sub(
        r'escrow(\d?)\.refund\(\s+_from=(\w+),\s+_valid=True\s+\)',
        r'scenario += escrow\1.refund().run(sender=\2)',
        content,
        flags=re.MULTILINE
    )
    
    # Fix escrow.force_refund() - multiple lines
    content = re.sub(
        r'escrow(\d?)\.force_refund\(\s+_from=(\w+),\s+_valid=True\s+\)',
        r'scenario += escrow\1.force_refund().run(sender=\2)',
        content,
        flags=re.MULTILINE
    )
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes needed in {filepath}")

if __name__ == '__main__':
    fix_file('tests/adversarial/test_fund_lock_prevention.py')
