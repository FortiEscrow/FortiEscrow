#!/usr/bin/env python3
"""
FortiEscrow Framework Validation Script
========================================

Validates core contract structure and invariants without requiring SmartPy.
This is a quick smoke test to ensure the framework is properly structured.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all core modules can be imported."""
    print("=" * 70)
    print("TEST 1: Validating Module Imports")
    print("=" * 70)
    
    try:
        from contracts.core import escrow_base
        print("✅ contracts.core.escrow_base")
        
        from contracts.core import forti_escrow
        print("✅ contracts.core.forti_escrow")
        
        from contracts.interfaces import types
        print("✅ contracts.interfaces.types")
        
        from contracts.interfaces import errors
        print("✅ contracts.interfaces.errors")
        
        from contracts.interfaces import events
        print("✅ contracts.interfaces.events")
        
        from contracts.utils import validators
        print("✅ contracts.utils.validators")
        
        from contracts.utils import amount_validator
        print("✅ contracts.utils.amount_validator")
        
        from contracts.utils import timeline_manager
        print("✅ contracts.utils.timeline_manager")
        
        from contracts.invariants_enforcement import check_invariants
        print("✅ contracts.invariants_enforcement")
        
        print("\n✅ All modules imported successfully\n")
        return True
    except ImportError as e:
        print(f"\n❌ Import Error: {e}\n")
        return False


def test_contract_structure():
    """Test that contract classes have required methods."""
    print("=" * 70)
    print("TEST 2: Validating Contract Structure")
    print("=" * 70)
    
    try:
        from contracts.core.escrow_base import SimpleEscrow
        from contracts.core.forti_escrow import FortiEscrow
        
        # Check SimpleEscrow
        simple = SimpleEscrow.__dict__
        required_methods = ['fund', 'release', 'refund', 'force_refund', 'get_status']
        
        for method in required_methods:
            if method in simple:
                print(f"✅ SimpleEscrow.{method}")
            else:
                print(f"❌ SimpleEscrow.{method} - MISSING")
                return False
        
        # Check FortiEscrow
        forti = FortiEscrow.__dict__
        for method in required_methods:
            if method in forti:
                print(f"✅ FortiEscrow.{method}")
            else:
                print(f"❌ FortiEscrow.{method} - MISSING")
                return False
        
        print("\n✅ All required methods present\n")
        return True
    except Exception as e:
        print(f"\n❌ Structure Error: {e}\n")
        return False


def test_interfaces():
    """Test that interface definitions are correct."""
    print("=" * 70)
    print("TEST 3: Validating Interface Definitions")
    print("=" * 70)
    
    try:
        from contracts.interfaces import types, errors, events
        
        # Check error codes
        error_attrs = [
            'ERROR_INVALID_STATE',
            'ERROR_UNAUTHORIZED', 
            'ERROR_INVALID_AMOUNT',
            'ERROR_DEADLINE_PASSED'
        ]
        
        for attr in error_attrs:
            if hasattr(errors, attr):
                print(f"✅ errors.{attr}")
            else:
                print(f"❌ errors.{attr} - MISSING")
                return False
        
        # Check event types
        event_attrs = [
            'EscrowFunded',
            'FundsReleased',
            'EscrowRefunded'
        ]
        
        for attr in event_attrs:
            if hasattr(events, attr):
                print(f"✅ events.{attr}")
            else:
                print(f"⚠️  events.{attr} - OPTIONAL")
        
        print("\n✅ Interface definitions valid\n")
        return True
    except Exception as e:
        print(f"\n❌ Interface Error: {e}\n")
        return False


def test_invariants():
    """Test that invariants can be loaded."""
    print("=" * 70)
    print("TEST 4: Validating Invariants")
    print("=" * 70)
    
    try:
        from contracts import invariants
        
        # Check state constants
        states = ['STATE_INIT', 'STATE_FUNDED', 'STATE_RELEASED', 'STATE_REFUNDED']
        for state in states:
            if hasattr(invariants, state):
                value = getattr(invariants, state)
                print(f"✅ invariants.{state} = {value}")
            else:
                print(f"❌ invariants.{state} - MISSING")
                return False
        
        print("\n✅ Invariants validated\n")
        return True
    except Exception as e:
        print(f"\n❌ Invariants Error: {e}\n")
        return False


def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "FortiEscrow Framework Validation" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    tests = [
        test_imports,
        test_contract_structure,
        test_interfaces,
        test_invariants,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ Framework validation PASSED - Ready for SmartPy testing\n")
        return 0
    else:
        print("\n❌ Framework validation FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
