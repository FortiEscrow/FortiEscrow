"""
FortiEscrow Error Codes

Centralized error definitions for all escrow contracts.
"""


class FortiEscrowError:
    """Error codes with semantic meanings"""
    
    # State Machine Errors
    INVALID_STATE = "INVALID_STATE"
    TIMEOUT_NOT_REACHED = "TIMEOUT_NOT_REACHED"
    TIMEOUT_EXCEEDED = "TIMEOUT_EXCEEDED"
    
    # Authorization Errors
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # Fund Validation Errors
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ZERO_AMOUNT = "ZERO_AMOUNT"
    
    # Parameter Validation Errors
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    DUPLICATE_PARTY = "DUPLICATE_PARTY"
    
    # Business Logic Errors
    BENEFICIARY_TRANSFER_FAILED = "BENEFICIARY_TRANSFER_FAILED"
    DEPOSITOR_TRANSFER_FAILED = "DEPOSITOR_TRANSFER_FAILED"
