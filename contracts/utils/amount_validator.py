"""
Amount Validation Utilities

Helper functions for validating escrow amounts.
"""

import smartpy as sp


def validate_positive_amount(amount):
    """
    Validate that amount is positive (non-zero).
    
    Args:
        amount: Amount in mutez (sp.TNat)
    
    Raises:
        Error if amount is zero
    """
    sp.verify(amount > 0, "ZERO_AMOUNT")


def validate_exact_funding(received, expected):
    """
    Validate that received amount matches exactly.
    
    Args:
        received: Received tez amount
        expected: Expected amount in mutez
    
    Raises:
        Error if amounts don't match exactly
    """
    sp.verify(received == sp.utils.nat_to_tez(expected), "INSUFFICIENT_FUNDS")


def validate_amount_is_reasonable(amount):
    """
    Validate that amount is within reasonable bounds.
    
    Args:
        amount: Amount in mutez
    
    Raises:
        Error if amount is unreasonably large
    """
    # Max 100 million XTZ (100M * 1M mutez)
    max_reasonable = sp.nat(100_000_000_000_000)
    sp.verify(amount <= max_reasonable, "INVALID_PARAMETERS")
