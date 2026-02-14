"""
FortiEscrow Validation Utilities
================================

Reusable validation functions for escrow contracts.

These validators ensure:
    - Input parameters are within safe bounds
    - Security invariants are maintained
    - Error messages are consistent

Usage:
    from contracts.utils.validators import Validators

    # In contract
    Validators.require_positive_amount(amount)
    Validators.require_valid_timeout(timeout)
"""

import smartpy as sp


# ==============================================================================
# VALIDATION ERROR CODES
# ==============================================================================

class ValidationError:
    """Validation-specific error codes"""

    ZERO_AMOUNT = "VALIDATION_ZERO_AMOUNT"
    NEGATIVE_AMOUNT = "VALIDATION_NEGATIVE_AMOUNT"
    AMOUNT_TOO_LARGE = "VALIDATION_AMOUNT_TOO_LARGE"
    AMOUNT_MISMATCH = "VALIDATION_AMOUNT_MISMATCH"

    TIMEOUT_TOO_SHORT = "VALIDATION_TIMEOUT_TOO_SHORT"
    TIMEOUT_TOO_LONG = "VALIDATION_TIMEOUT_TOO_LONG"

    SAME_ADDRESS = "VALIDATION_SAME_ADDRESS"
    ZERO_ADDRESS = "VALIDATION_ZERO_ADDRESS"

    INVALID_STATE = "VALIDATION_INVALID_STATE"


# ==============================================================================
# VALIDATION CONSTANTS
# ==============================================================================

class ValidationConstants:
    """Validation bounds and limits"""

    # Timeout bounds
    MIN_TIMEOUT_SECONDS = 3600              # 1 hour
    MAX_TIMEOUT_SECONDS = 365 * 24 * 3600   # 1 year

    # Amount bounds
    MIN_AMOUNT = 1                          # 1 mutez minimum
    MAX_AMOUNT = 100_000_000_000_000        # 100M XTZ in mutez

    # Valid escrow states
    VALID_STATES = [0, 1, 2, 3]             # INIT, FUNDED, RELEASED, REFUNDED


# ==============================================================================
# VALIDATORS CLASS
# ==============================================================================

class Validators:
    """
    Static validation methods for escrow contracts.

    All methods use sp.verify() to enforce constraints.
    Failed validation raises the corresponding error.
    """

    # ==========================================================================
    # AMOUNT VALIDATORS
    # ==========================================================================

    @staticmethod
    def require_positive_amount(amount):
        """
        Verify amount is strictly positive (> 0).

        Args:
            amount: Amount in mutez (sp.TNat)

        Raises:
            VALIDATION_ZERO_AMOUNT if amount == 0
        """
        sp.verify(amount > sp.nat(0), ValidationError.ZERO_AMOUNT)

    @staticmethod
    def require_reasonable_amount(amount):
        """
        Verify amount is within reasonable bounds.

        Args:
            amount: Amount in mutez

        Raises:
            VALIDATION_ZERO_AMOUNT if amount == 0
            VALIDATION_AMOUNT_TOO_LARGE if amount > MAX_AMOUNT
        """
        sp.verify(amount > sp.nat(0), ValidationError.ZERO_AMOUNT)
        sp.verify(
            amount <= sp.nat(ValidationConstants.MAX_AMOUNT),
            ValidationError.AMOUNT_TOO_LARGE
        )

    @staticmethod
    def require_exact_amount(received, expected):
        """
        Verify received amount matches expected exactly.

        Args:
            received: sp.amount (received tez)
            expected: Expected amount in mutez (nat)

        Raises:
            VALIDATION_AMOUNT_MISMATCH if amounts differ
        """
        sp.verify(
            received == sp.utils.nat_to_mutez(expected),
            ValidationError.AMOUNT_MISMATCH
        )

    @staticmethod
    def require_sufficient_amount(received, minimum):
        """
        Verify received amount is at least minimum.

        Args:
            received: sp.amount (received tez)
            minimum: Minimum amount in mutez (nat)

        Raises:
            VALIDATION_AMOUNT_MISMATCH if received < minimum
        """
        sp.verify(
            received >= sp.utils.nat_to_mutez(minimum),
            ValidationError.AMOUNT_MISMATCH
        )

    # ==========================================================================
    # TIMEOUT VALIDATORS
    # ==========================================================================

    @staticmethod
    def require_valid_timeout(timeout_seconds):
        """
        Verify timeout is within allowed bounds.

        Args:
            timeout_seconds: Timeout duration in seconds

        Raises:
            VALIDATION_TIMEOUT_TOO_SHORT if < 1 hour
            VALIDATION_TIMEOUT_TOO_LONG if > 1 year
        """
        sp.verify(
            timeout_seconds >= sp.nat(ValidationConstants.MIN_TIMEOUT_SECONDS),
            ValidationError.TIMEOUT_TOO_SHORT
        )
        sp.verify(
            timeout_seconds <= sp.nat(ValidationConstants.MAX_TIMEOUT_SECONDS),
            ValidationError.TIMEOUT_TOO_LONG
        )

    @staticmethod
    def require_minimum_timeout(timeout_seconds, minimum):
        """
        Verify timeout is at least minimum value.

        Args:
            timeout_seconds: Timeout duration
            minimum: Minimum allowed seconds

        Raises:
            VALIDATION_TIMEOUT_TOO_SHORT if timeout < minimum
        """
        sp.verify(timeout_seconds >= minimum, ValidationError.TIMEOUT_TOO_SHORT)

    # ==========================================================================
    # ADDRESS VALIDATORS
    # ==========================================================================

    @staticmethod
    def require_different_addresses(addr1, addr2):
        """
        Verify two addresses are different.

        Args:
            addr1: First address
            addr2: Second address

        Raises:
            VALIDATION_SAME_ADDRESS if addresses match
        """
        sp.verify(addr1 != addr2, ValidationError.SAME_ADDRESS)

    @staticmethod
    def require_all_different(addr1, addr2, addr3):
        """
        Verify three addresses are all different.

        Args:
            addr1, addr2, addr3: Addresses to compare

        Raises:
            VALIDATION_SAME_ADDRESS if any pair matches
        """
        sp.verify(
            (addr1 != addr2) & (addr1 != addr3) & (addr2 != addr3),
            ValidationError.SAME_ADDRESS
        )

    @staticmethod
    def require_sender_is(expected, error_msg=None):
        """
        Verify sender matches expected address.

        Args:
            expected: Expected sender address
            error_msg: Custom error message (optional)

        Raises:
            error_msg or default UNAUTHORIZED
        """
        msg = error_msg if error_msg else "UNAUTHORIZED"
        sp.verify(sp.sender == expected, msg)

    # @staticmethod
    # def require_sender_in(allowed_list, error_msg=None):
    #     """
    #     Verify sender is in allowed list.
    #     
    #     NOTE: This function uses SmartPy-specific syntax (sp.for, sp.if_, sp.local)
    #     and should only be used within a SmartPy contract context, not in utilities.
    #     Left here for reference but commented out due to Python syntax incompatibility.
    #
    #     Args:
    #         allowed_list: List of allowed addresses
    #         error_msg: Custom error message (optional)
    #
    #     Raises:
    #         error_msg or default UNAUTHORIZED
    #     """
    #     msg = error_msg if error_msg else "UNAUTHORIZED"
    #     is_allowed = sp.local("is_allowed", False)
    #     sp.for addr in allowed_list:
    #         with sp.if_(sp.sender == addr):
    #             is_allowed.value = True
    #     sp.verify(is_allowed.value, msg)

    # ==========================================================================
    # STATE VALIDATORS
    # ==========================================================================

    @staticmethod
    def require_state(current, expected, error_msg=None):
        """
        Verify contract is in expected state.

        Args:
            current: Current state value
            expected: Expected state value
            error_msg: Custom error message (optional)

        Raises:
            error_msg or default VALIDATION_INVALID_STATE
        """
        msg = error_msg if error_msg else ValidationError.INVALID_STATE
        sp.verify(current == expected, msg)

    @staticmethod
    def require_not_terminal(state):
        """
        Verify state is not terminal (RELEASED or REFUNDED).

        Args:
            state: Current state value (int)

        Raises:
            VALIDATION_INVALID_STATE if state is 2 or 3
        """
        sp.verify(
            (state != 2) & (state != 3),
            ValidationError.INVALID_STATE
        )

    # ==========================================================================
    # TIMELINE VALIDATORS
    # ==========================================================================

    @staticmethod
    def require_before_deadline(deadline):
        """
        Verify current time is before deadline.

        Args:
            deadline: Deadline timestamp

        Raises:
            ESCROW_DEADLINE_PASSED if now > deadline
        """
        sp.verify(sp.now <= deadline, "ESCROW_DEADLINE_PASSED")

    @staticmethod
    def require_after_deadline(deadline):
        """
        Verify current time is after deadline.

        Args:
            deadline: Deadline timestamp

        Raises:
            ESCROW_TIMEOUT_NOT_EXPIRED if now <= deadline
        """
        sp.verify(sp.now > deadline, "ESCROW_TIMEOUT_NOT_EXPIRED")


# ==============================================================================
# INLINE HELPER FUNCTIONS
# ==============================================================================

def validate_escrow_params(depositor, beneficiary, amount, timeout_seconds):
    """
    Validate all escrow creation parameters at once.

    Convenience function combining multiple validations.

    Args:
        depositor: Depositor address
        beneficiary: Beneficiary address
        amount: Escrow amount in mutez
        timeout_seconds: Timeout duration

    Raises:
        Various validation errors if any check fails
    """
    Validators.require_different_addresses(depositor, beneficiary)
    Validators.require_reasonable_amount(amount)
    Validators.require_valid_timeout(timeout_seconds)


def validate_multisig_params(depositor, beneficiary, arbiter, amount, timeout_seconds):
    """
    Validate multi-sig escrow creation parameters.

    Args:
        depositor: Depositor address
        beneficiary: Beneficiary address
        arbiter: Arbiter address
        amount: Escrow amount in mutez
        timeout_seconds: Timeout duration

    Raises:
        Various validation errors if any check fails
    """
    Validators.require_all_different(depositor, beneficiary, arbiter)
    Validators.require_reasonable_amount(amount)
    Validators.require_valid_timeout(timeout_seconds)
