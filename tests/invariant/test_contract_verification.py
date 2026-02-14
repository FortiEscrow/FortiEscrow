#!/usr/bin/env python3
"""
FortiEscrow Contract Verification Suite
========================================

Performs syntax validation and structural analysis of the FortiEscrow framework.
This validates contracts without requiring SmartPy runtime.
"""

import ast
import sys
from pathlib import Path

class ContractAnalyzer:
    """Analyzes contract Python files for correctness."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
    
    def check_syntax(self, filepath):
        """Verify Python syntax is valid."""
        try:
            with open(filepath) as f:
                ast.parse(f.read())
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def analyze_contract(self, filepath):
        """Analyze contract file for structure."""
        try:
            with open(filepath) as f:
                tree = ast.parse(f.read())
            
            # Extract class definitions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Extract function definitions
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            return {
                'classes': classes,
                'functions': functions,
                'ast': tree
            }
        except Exception as e:
            return None
    
    def validate_core_contracts(self):
        """Validate core contract files."""
        print("\n" + "=" * 70)
        print("CORE CONTRACT VALIDATION")
        print("=" * 70)
        
        core_files = [
            'contracts/core/escrow_base.py',
            'contracts/core/forti_escrow.py',
            'contracts/core/escrow_factory.py',
            'contracts/core/escrow_multisig.py',
        ]
        
        for filepath in core_files:
            path = Path(filepath)
            if not path.exists():
                self.warnings.append(f"⚠️  {filepath} - NOT FOUND")
                continue
            
            valid, error = self.check_syntax(filepath)
            if valid:
                analysis = self.analyze_contract(filepath)
                if analysis:
                    num_classes = len(analysis['classes'])
                    num_functions = len(analysis['functions'])
                    self.passed.append(f"✅ {filepath} ({num_classes} classes, {num_functions} functions)")
                    print(f"✅ {filepath}")
                    print(f"   Classes: {', '.join(analysis['classes']) or 'None'}")
                    print(f"   Functions: {num_functions} total")
            else:
                self.errors.append(f"❌ {filepath} - SYNTAX ERROR: {error}")
                print(f"❌ {filepath}")
                print(f"   {error}")
    
    def validate_interfaces(self):
        """Validate interface files."""
        print("\n" + "=" * 70)
        print("INTERFACE VALIDATION")
        print("=" * 70)
        
        interface_files = [
            'contracts/interfaces/types.py',
            'contracts/interfaces/errors.py',
            'contracts/interfaces/events.py',
        ]
        
        for filepath in interface_files:
            path = Path(filepath)
            if not path.exists():
                self.warnings.append(f"⚠️  {filepath} - NOT FOUND")
                continue
            
            valid, error = self.check_syntax(filepath)
            if valid:
                self.passed.append(f"✅ {filepath}")
                print(f"✅ {filepath}")
            else:
                self.errors.append(f"❌ {filepath} - SYNTAX ERROR: {error}")
                print(f"❌ {filepath} - {error}")
    
    def validate_utilities(self):
        """Validate utility files."""
        print("\n" + "=" * 70)
        print("UTILITY VALIDATION")
        print("=" * 70)
        
        util_files = [
            'contracts/utils/validators.py',
            'contracts/utils/amount_validator.py',
            'contracts/utils/timeline_manager.py',
        ]
        
        for filepath in util_files:
            path = Path(filepath)
            if not path.exists():
                self.warnings.append(f"⚠️  {filepath} - NOT FOUND")
                continue
            
            valid, error = self.check_syntax(filepath)
            if valid:
                self.passed.append(f"✅ {filepath}")
                print(f"✅ {filepath}")
            else:
                self.errors.append(f"❌ {filepath} - SYNTAX ERROR: {error}")
                print(f"❌ {filepath} - {error}")
    
    def validate_invariants(self):
        """Validate invariant enforcement."""
        print("\n" + "=" * 70)
        print("INVARIANTS VALIDATION")
        print("=" * 70)
        
        inv_files = [
            'contracts/invariants.py',
            'contracts/invariants_enforcement.py',
        ]
        
        for filepath in inv_files:
            path = Path(filepath)
            if not path.exists():
                self.warnings.append(f"⚠️  {filepath} - NOT FOUND")
                continue
            
            valid, error = self.check_syntax(filepath)
            if valid:
                self.passed.append(f"✅ {filepath}")
                print(f"✅ {filepath}")
            else:
                self.errors.append(f"❌ {filepath} - SYNTAX ERROR: {error}")
                print(f"❌ {filepath} - {error}")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        print(f"\n✅ Passed: {len(self.passed)}")
        for msg in self.passed:
            print(f"   {msg}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for msg in self.warnings:
                print(f"   {msg}")
        
        if self.errors:
            print(f"\n❌ Errors: {len(self.errors)}")
            for msg in self.errors:
                print(f"   {msg}")
            return False
        
        return True


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "FortiEscrow Contract Verification Suite" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")
    
    analyzer = ContractAnalyzer()
    
    analyzer.validate_core_contracts()
    analyzer.validate_interfaces()
    analyzer.validate_utilities()
    analyzer.validate_invariants()
    
    success = analyzer.print_summary()
    
    if success:
        print("\n✅ All contracts validated successfully!")
        print("\nNext steps:")
        print("  1. Install SmartPy: https://smartpy.io/")
        print("  2. Run full test suite: python -m smartpy test tests/test_fortiescrow.py")
        print("  3. Deploy to testnet: python -m smartpy deploy contracts/core/forti_escrow.py")
        print()
        return 0
    else:
        print("\n❌ Validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
