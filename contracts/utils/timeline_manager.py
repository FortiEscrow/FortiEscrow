"""
Timeline & Timeout Management Utilities

Helper functions for timeout calculations and timeline management.
"""

import smartpy as sp


def calculate_timeout_expiration(funded_timestamp, timeout_seconds):
    """
    Calculate when timeout expires.
    
    Args:
        funded_timestamp: Block timestamp when escrow was funded
        timeout_seconds: Timeout duration in seconds
    
    Returns:
        Timestamp when timeout expires
    """
    return funded_timestamp + sp.to_int(timeout_seconds)


def is_timeout_expired(funded_timestamp, timeout_seconds):
    """
    Check if timeout has expired.
    
    Args:
        funded_timestamp: Block timestamp when escrow was funded
        timeout_seconds: Timeout duration in seconds
    
    Returns:
        Boolean indicating if timeout expired
    """
    current_time = sp.now
    timeout_expiration = calculate_timeout_expiration(funded_timestamp, timeout_seconds)
    return current_time >= timeout_expiration


def validate_minimum_timeout(timeout_seconds):
    """
    Validate timeout is at least minimum (1 hour).
    
    Args:
        timeout_seconds: Timeout duration in seconds
    
    Raises:
        Error if timeout too short
    """
    ONE_HOUR = 3600
    sp.verify(timeout_seconds >= ONE_HOUR, "INVALID_PARAMETERS")


def validate_reasonable_timeout(timeout_seconds):
    """
    Validate timeout is within reasonable bounds.
    
    Args:
        timeout_seconds: Timeout duration in seconds
    
    Raises:
        Error if timeout unreasonably long
    """
    ONE_YEAR = 365 * 24 * 3600
    sp.verify(timeout_seconds <= ONE_YEAR, "INVALID_PARAMETERS")
