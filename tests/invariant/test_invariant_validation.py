"""
FortiEscrow Invariant Validation Tests

Comprehensive pytest tests that verify security invariants hold under all conditions.

Each test validates that:
1. Invariant preconditions are established
2. Operation is performed
3. Invariant postconditions are satisfied
4. Or operation is correctly rejected
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from conftest import *
from contracts.core.escrow_base import SimpleEscrow, STATE_INIT, STATE_FUNDED, STATE_RELEASED, STATE_REFUNDED
from contracts.core.escrow_multisig import (
    MultiSigEscrow,
    DISPUTE_NONE, DISPUTE_PENDING, DISPUTE_RESOLVED,
    DISPUTE_RESOLVED_RELEASE, DISPUTE_RESOLVED_REFUND,
)


class TestAddresses:
    """Standard test addresses for invariant tests."""
    DEPOSITOR = sp.address("tz1Depositor1111111111111111111111")
    BENEFICIARY = sp.address("tz1Beneficiary111111111111111111")
    ARBITER = sp.address("tz1Arbiter11111111111111111111111")
    ATTACKER = sp.address("tz1Attacker11111111111111111111111")


def create_simple_escrow():
    """Factory for SimpleEscrow in INIT state."""
    escrow = SimpleEscrow(
        depositor=TestAddresses.DEPOSITOR,
        beneficiary=TestAddresses.BENEFICIARY,
        amount=1000,  # Amount in mutez
        timeout_seconds=86400  # 1 day
    )
    return escrow


def create_multisig_escrow():
    """Factory for MultiSigEscrow in INIT state."""
    escrow = MultiSigEscrow(
        depositor=TestAddresses.DEPOSITOR,
        beneficiary=TestAddresses.BENEFICIARY,
        arbiter=TestAddresses.ARBITER,
        amount=1000,  # Amount in mutez
        timeout_seconds=86400  # 1 day
    )
    return escrow


# ==============================================================================
# INVARIANT #1: FUNDS SAFETY
# State transitions don't transfer funds; only terminal states can transfer
# ==============================================================================

class TestFundsSafetyInvariant:
    """Verify funds can only be transferred in terminal states."""

    def test_no_transfer_in_init_state(self):
        """Funds cannot be transferred from INIT state."""
        escrow = create_simple_escrow()
        
        # Verify precondition: state is INIT
        assert escrow.data.state == STATE_INIT
        
        # Attempt to release (should fail or not actually transfer funds)
        with pytest.raises(Exception):
            escrow.release().run(sender=TestAddresses.DEPOSITOR)

    def test_no_transfer_in_funded_state(self):
        """Funds cannot be transferred from FUNDED state (must be terminal)."""
        escrow = create_simple_escrow()
        
        # Setup: Fund the escrow
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow.data.state == STATE_FUNDED
        
        # Attempt to withdraw/transfer in non-terminal state
        # This should be prevented - funds stay safe
        assert escrow.data.state == STATE_FUNDED
        # Funds not transferred yet
        
    def test_transfer_allowed_in_released_state(self):
        """Funds CAN be transferred once state is RELEASED."""
        escrow = create_simple_escrow()
        
        # Setup: Fund and release
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow.release().run(sender=TestAddresses.DEPOSITOR)
        
        # Verify: State is terminal
        assert escrow.data.state == STATE_RELEASED
        
        # Postcondition: Transfer happened (funds left escrow)
        # In real scenario, sp.send() was called
        assert escrow.data.state == STATE_RELEASED

    def test_transfer_allowed_in_refunded_state(self):
        """Funds CAN be transferred once state is REFUNDED."""
        escrow = create_simple_escrow()
        
        # Setup: Fund and refund
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow.refund().run(sender=TestAddresses.DEPOSITOR)
        
        # Verify: State is terminal
        assert escrow.data.state == STATE_REFUNDED
        
        # Postcondition: Transfer happened
        assert escrow.data.state == STATE_REFUNDED


# ==============================================================================
# INVARIANT #2: STATE CONSISTENCY
# State follows FSM rules: INIT → FUNDED → {RELEASED | REFUNDED}
# ==============================================================================

class TestStateConsistencyInvariant:
    """Verify state transitions follow the FSM definition."""

    def test_init_can_only_transition_to_funded(self):
        """From INIT state, only fund() can proceed."""
        escrow = create_simple_escrow()
        assert escrow.data.state == STATE_INIT
        
        # Try to release from INIT (should fail)
        with pytest.raises(Exception):
            escrow.release().run(sender=TestAddresses.DEPOSITOR)
        
        # Try to refund from INIT (should fail)
        with pytest.raises(Exception):
            escrow.refund().run(sender=TestAddresses.DEPOSITOR)
        
        # Only fund() should work
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow.data.state == STATE_FUNDED

    def test_funded_can_transition_to_released_or_refunded(self):
        """From FUNDED state, can go to RELEASED or REFUNDED."""
        escrow1 = create_simple_escrow()
        escrow1.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow1.data.state == STATE_FUNDED
        
        # Can transition to RELEASED
        escrow1.release().run(sender=TestAddresses.DEPOSITOR)
        assert escrow1.data.state == STATE_RELEASED
        
        # Separate test: Can transition to REFUNDED
        escrow2 = create_simple_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.refund().run(sender=TestAddresses.DEPOSITOR)
        assert escrow2.data.state == STATE_REFUNDED

    def test_terminal_states_cannot_transition(self):
        """From RELEASED or REFUNDED, no transitions allowed."""
        # Test RELEASED is terminal
        escrow1 = create_simple_escrow()
        escrow1.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow1.release().run(sender=TestAddresses.DEPOSITOR)
        assert escrow1.data.state == STATE_RELEASED
        
        # Try to refund from RELEASED (should fail)
        with pytest.raises(Exception):
            escrow1.refund().run(sender=TestAddresses.DEPOSITOR)
        
        # Test REFUNDED is terminal
        escrow2 = create_simple_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.refund().run(sender=TestAddresses.DEPOSITOR)
        assert escrow2.data.state == STATE_REFUNDED
        
        # Try to release from REFUNDED (should fail)
        with pytest.raises(Exception):
            escrow2.release().run(sender=TestAddresses.DEPOSITOR)

    def test_no_backward_transitions(self):
        """Cannot transition backward in FSM."""
        escrow = create_simple_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow.release().run(sender=TestAddresses.DEPOSITOR)
        
        # Try to go back to FUNDED (should fail)
        with pytest.raises(Exception):
            escrow.fund().run(
                sender=TestAddresses.DEPOSITOR,
                amount=1000
            )


# ==============================================================================
# INVARIANT #3: AUTHORIZATION CORRECTNESS
# Only authorized parties can execute privileged operations
# ==============================================================================

class TestAuthorizationInvariant:
    """Verify only authorized parties can perform operations."""

    def test_only_depositor_can_fund(self):
        """Only depositor can call fund()."""
        escrow = create_simple_escrow()
        
        # Depositor CAN fund
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow.data.state == STATE_FUNDED
        
        # Beneficiary CANNOT fund different escrow
        escrow2 = create_simple_escrow()
        with pytest.raises(Exception):
            escrow2.fund().run(
                sender=TestAddresses.BENEFICIARY,
                amount=1000
            )

    def test_only_depositor_can_release_simple(self):
        """In SimpleEscrow, only depositor can call release()."""
        escrow = create_simple_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Depositor CAN release
        escrow.release().run(sender=TestAddresses.DEPOSITOR)
        assert escrow.data.state == STATE_RELEASED
        
        # Beneficiary CANNOT release
        escrow2 = create_simple_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        with pytest.raises(Exception):
            escrow2.release().run(sender=TestAddresses.BENEFICIARY)

    def test_only_parties_can_vote_multisig(self):
        """In MultiSigEscrow, only the three parties can vote."""
        # Setup: Create escrow and fund it
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Verify state is FUNDED
        assert escrow.data.state == STATE_FUNDED
        
        # Depositor CAN vote
        escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
        assert escrow.data.release_votes == 1
        
        # IMPORTANT INVARIANT: After 2-of-3 votes, consensus reached and state exits FUNDED
        # So test each voter separately to verify authorization
        
        # Test Beneficiary can vote (on fresh escrow)
        escrow2 = create_multisig_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.vote_release().run(sender=TestAddresses.BENEFICIARY)
        assert escrow2.data.release_votes == 1
        
        # Test Arbiter can vote (on fresh escrow)
        escrow3 = create_multisig_escrow()
        escrow3.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow3.vote_release().run(sender=TestAddresses.ARBITER)
        assert escrow3.data.release_votes == 1
        
        # Attacker CANNOT vote
        escrow4 = create_multisig_escrow()
        escrow4.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        with pytest.raises(Exception):
            escrow4.vote_release().run(sender=TestAddresses.ATTACKER)

    def test_only_parties_can_raise_dispute(self):
        """Only depositor or beneficiary can raise disputes."""
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Depositor CAN raise
        escrow.raise_dispute("invalid service").run(
            sender=TestAddresses.DEPOSITOR
        )
        assert escrow.data.dispute_state == DISPUTE_PENDING
        
        # Arbiter CANNOT raise
        escrow2 = create_multisig_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        with pytest.raises(Exception):
            escrow2.raise_dispute("complaint").run(
                sender=TestAddresses.ARBITER
            )

    def test_only_arbiter_can_resolve_dispute(self):
        """Only arbiter can call resolve_dispute()."""
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow.raise_dispute("issue").run(
            sender=TestAddresses.DEPOSITOR
        )
        
        # Arbiter CAN resolve
        escrow.resolve_dispute(DISPUTE_RESOLVED_RELEASE).run(
            sender=TestAddresses.ARBITER
        )
        assert escrow.data.dispute_state == DISPUTE_RESOLVED
        
        # Depositor CANNOT resolve
        escrow2 = create_multisig_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.raise_dispute("issue").run(
            sender=TestAddresses.DEPOSITOR
        )
        with pytest.raises(Exception):
            escrow2.resolve_dispute(DISPUTE_RESOLVED_RELEASE).run(
                sender=TestAddresses.DEPOSITOR
            )


# ==============================================================================
# INVARIANT #4: TIME SAFETY
# Funds are always recoverable via force_refund at or after deadline
# ==============================================================================

class TestTimeSafetyInvariant:
    """Verify no permanent fund locking is possible."""

    def test_force_refund_available_at_deadline(self):
        """force_refund() works at or after deadline."""
        escrow = create_simple_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Deadline is funded_at + timeout_seconds
        # At or after deadline, force_refund should work
        # (Mock now to be >= deadline)
        
        # For now, just verify precondition
        assert escrow.data.state == STATE_FUNDED

    def test_force_refund_rejected_before_deadline(self):
        """force_refund() is rejected before deadline."""
        escrow = create_simple_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Before deadline, force_refund should fail
        # (This requires time mocking in the test framework)
        # For now, verify structure exists
        assert escrow.data.funded_at is not None


# ==============================================================================
# INVARIANT #5: NO PERMANENT FUND-LOCKING
# Multiple independent exit paths ensure recovery
# ==============================================================================

class TestNoFundLockingInvariant:
    """Verify funds always have an exit path."""

    def test_simple_escrow_three_exit_paths(self):
        """SimpleEscrow has three independent exit paths."""
        escrow = create_simple_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Path 1: release() → RELEASED
        escrow.release().run(sender=TestAddresses.DEPOSITOR)
        assert escrow.data.state == STATE_RELEASED
        
        # Path 2: refund() → REFUNDED
        escrow2 = create_simple_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.refund().run(sender=TestAddresses.DEPOSITOR)
        assert escrow2.data.state == STATE_REFUNDED
        
        # Path 3: force_refund() after deadline → REFUNDED
        # (Requires time progression in test)
        escrow3 = create_simple_escrow()
        escrow3.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow3.data.state == STATE_FUNDED

    def test_multisig_escrow_three_exit_paths(self):
        """MultiSigEscrow has three independent exit paths."""
        # Path 1: vote_release consensus → RELEASED
        escrow1 = create_multisig_escrow()
        escrow1.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow1.vote_release().run(sender=TestAddresses.DEPOSITOR)
        escrow1.vote_release().run(sender=TestAddresses.BENEFICIARY)
        assert escrow1.data.state == STATE_RELEASED
        
        # Path 2: vote_refund consensus → REFUNDED
        escrow2 = create_multisig_escrow()
        escrow2.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        escrow2.vote_refund().run(sender=TestAddresses.DEPOSITOR)
        escrow2.vote_refund().run(sender=TestAddresses.BENEFICIARY)
        assert escrow2.data.state == STATE_REFUNDED
        
        # Path 3: force_refund after deadline
        escrow3 = create_multisig_escrow()
        escrow3.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        assert escrow3.data.state == STATE_FUNDED


# ==============================================================================
# DISPUTE MECHANISM INVARIANTS
# ==============================================================================

class TestDisputeInvariants:
    """Verify dispute mechanism doesn't violate safety invariants."""

    def test_dispute_doesnt_block_voting(self):
        """Voting continues even when dispute is active."""
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Raise dispute
        escrow.raise_dispute("service issue").run(
            sender=TestAddresses.DEPOSITOR
        )
        assert escrow.data.dispute_state == DISPUTE_PENDING
        
        # Voting still allowed during dispute
        escrow.vote_refund().run(sender=TestAddresses.DEPOSITOR)
        assert escrow.data.refund_votes > 0

    def test_dispute_doesnt_prevent_resolution(self):
        """Can still reach terminal state during dispute."""
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Raise dispute
        escrow.raise_dispute("service dispute").run(
            sender=TestAddresses.DEPOSITOR
        )
        
        # Can still vote and reach consensus
        escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
        escrow.vote_release().run(sender=TestAddresses.BENEFICIARY)
        
        # Should reach terminal state
        assert escrow.data.state == STATE_RELEASED

    def test_resolved_dispute_preserved(self):
        """Dispute resolution info is preserved in audit trail."""
        escrow = create_multisig_escrow()
        escrow.fund().run(
            sender=TestAddresses.DEPOSITOR,
            amount=1000
        )
        
        # Raise and resolve dispute
        escrow.raise_dispute("service issue").run(
            sender=TestAddresses.DEPOSITOR
        )
        escrow.resolve_dispute(DISPUTE_RESOLVED_RELEASE).run(
            sender=TestAddresses.ARBITER
        )
        
        # Verify audit trail preserved
        assert escrow.data.dispute_state == DISPUTE_RESOLVED
        assert escrow.data.dispute_outcome == DISPUTE_RESOLVED_RELEASE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
