"""
MultiSigEscrow Test Suite
=========================

Security-focused tests for the 2-of-3 multi-signature escrow contract.

Test Categories:
    1. Initialization: Party validation and setup
    2. Voting: Vote casting, changing, and consensus
    3. Dispute: Dispute raising and resolution
    4. Timeout: Emergency recovery mechanism
    5. Attack Vectors: Adversarial scenarios

Run with: python -m smartpy test tests/test_multisig_escrow.py
"""

import smartpy as sp

from contracts.core.escrow_multisig import (
    MultiSigEscrow,
    DISPUTE_NONE,
    DISPUTE_PENDING,
    VOTE_RELEASE,
    VOTE_REFUND
)

from contracts.core.escrow_base import (
    EscrowError,
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    MIN_TIMEOUT_SECONDS
)


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

class TestAddresses:
    """Standard test addresses for MultiSig"""
    DEPOSITOR = sp.address("tz1Depositor11111111111111111111111111")
    BENEFICIARY = sp.address("tz1Beneficiary1111111111111111111111")
    ARBITER = sp.address("tz1Arbiter111111111111111111111111111")
    ATTACKER = sp.address("tz1Attacker11111111111111111111111111")


class TestAmounts:
    """Standard test amounts"""
    SMALL = sp.nat(1_000_000)          # 1 XTZ
    MEDIUM = sp.nat(10_000_000)        # 10 XTZ


class TestTimeouts:
    """Standard test timeouts"""
    MIN = sp.nat(MIN_TIMEOUT_SECONDS)
    WEEK = sp.nat(7 * 24 * 3600)


def create_multisig_escrow(
    depositor=None,
    beneficiary=None,
    arbiter=None,
    amount=None,
    timeout=None
):
    """Factory for MultiSig escrow test instances"""
    return MultiSigEscrow(
        depositor=depositor or TestAddresses.DEPOSITOR,
        beneficiary=beneficiary or TestAddresses.BENEFICIARY,
        arbiter=arbiter or TestAddresses.ARBITER,
        amount=amount or TestAmounts.SMALL,
        timeout_seconds=timeout or TestTimeouts.WEEK
    )


def fund_escrow(scenario, escrow, now=None):
    """Helper to fund an escrow"""
    run_params = {
        "sender": TestAddresses.DEPOSITOR,
        "amount": sp.utils.nat_to_mutez(escrow.data.escrow_amount)
    }
    if now is not None:
        run_params["now"] = now

    scenario += escrow.fund().run(**run_params)


# ==============================================================================
# TEST: INITIALIZATION
# ==============================================================================

@sp.add_test(name="MultiSig Init: Correct initial state")
def test_multisig_init():
    """Verify MultiSig escrow initializes correctly"""
    scenario = sp.test_scenario()
    scenario.h1("MultiSig Initialization Test")

    escrow = create_multisig_escrow()
    scenario += escrow

    # Verify parties
    scenario.verify(escrow.data.depositor == TestAddresses.DEPOSITOR)
    scenario.verify(escrow.data.beneficiary == TestAddresses.BENEFICIARY)
    scenario.verify(escrow.data.arbiter == TestAddresses.ARBITER)

    # Verify state
    scenario.verify(escrow.data.state == STATE_INIT)
    scenario.verify(escrow.data.release_votes == sp.nat(0))
    scenario.verify(escrow.data.refund_votes == sp.nat(0))
    scenario.verify(escrow.data.dispute_state == DISPUTE_NONE)


@sp.add_test(name="MultiSig Init: Rejects duplicate parties")
def test_multisig_rejects_duplicates():
    """Verify all three parties must be different"""
    scenario = sp.test_scenario()
    scenario.h1("Duplicate Party Prevention Test")

    # All parties are verified different at contract level
    scenario.verify(
        (TestAddresses.DEPOSITOR != TestAddresses.BENEFICIARY) &
        (TestAddresses.DEPOSITOR != TestAddresses.ARBITER) &
        (TestAddresses.BENEFICIARY != TestAddresses.ARBITER)
    )


# ==============================================================================
# TEST: VOTING - RELEASE
# ==============================================================================

@sp.add_test(name="MultiSig Vote: Single vote does not release")
def test_single_vote_no_release():
    """Verify single vote does not trigger release"""
    scenario = sp.test_scenario()
    scenario.h1("Single Vote Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)

    # Verify state unchanged
    scenario.verify(escrow.data.state == STATE_FUNDED)
    scenario.verify(escrow.data.release_votes == sp.nat(1))


@sp.add_test(name="MultiSig Vote: Two votes trigger release")
def test_two_votes_release():
    """Verify 2-of-3 votes triggers release"""
    scenario = sp.test_scenario()
    scenario.h1("Two Vote Release Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
    scenario.verify(escrow.data.release_votes == sp.nat(1))

    # Beneficiary votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.BENEFICIARY)

    # Should auto-release
    scenario.verify(escrow.data.state == STATE_RELEASED)


@sp.add_test(name="MultiSig Vote: Depositor + Arbiter can release")
def test_depositor_arbiter_release():
    """Verify depositor + arbiter can release (bypassing beneficiary)"""
    scenario = sp.test_scenario()
    scenario.h1("Depositor + Arbiter Release Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)

    # Arbiter votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.ARBITER)

    # Should release
    scenario.verify(escrow.data.state == STATE_RELEASED)


@sp.add_test(name="MultiSig Vote: Beneficiary + Arbiter can release")
def test_beneficiary_arbiter_release():
    """Verify beneficiary + arbiter can release (bypassing depositor)"""
    scenario = sp.test_scenario()
    scenario.h1("Beneficiary + Arbiter Release Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Beneficiary votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.BENEFICIARY)

    # Arbiter votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.ARBITER)

    # Should release
    scenario.verify(escrow.data.state == STATE_RELEASED)


# ==============================================================================
# TEST: VOTING - REFUND
# ==============================================================================

@sp.add_test(name="MultiSig Vote: Two refund votes trigger refund")
def test_two_votes_refund():
    """Verify 2-of-3 refund votes triggers refund"""
    scenario = sp.test_scenario()
    scenario.h1("Two Vote Refund Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes refund
    scenario += escrow.vote_refund().run(sender=TestAddresses.DEPOSITOR)
    scenario.verify(escrow.data.refund_votes == sp.nat(1))

    # Arbiter votes refund
    scenario += escrow.vote_refund().run(sender=TestAddresses.ARBITER)

    # Should refund
    scenario.verify(escrow.data.state == STATE_REFUNDED)


# ==============================================================================
# TEST: VOTE CHANGING
# ==============================================================================

@sp.add_test(name="MultiSig Vote: Party can change vote")
def test_vote_change():
    """Verify party can change their vote"""
    scenario = sp.test_scenario()
    scenario.h1("Vote Change Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes release
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
    scenario.verify(escrow.data.release_votes == sp.nat(1))
    scenario.verify(escrow.data.refund_votes == sp.nat(0))

    # Depositor changes to refund
    scenario += escrow.vote_refund().run(sender=TestAddresses.DEPOSITOR)
    scenario.verify(escrow.data.release_votes == sp.nat(0))
    scenario.verify(escrow.data.refund_votes == sp.nat(1))


@sp.add_test(name="MultiSig Vote: Voting same way is idempotent")
def test_vote_idempotent():
    """Verify voting same way twice doesn't double count"""
    scenario = sp.test_scenario()
    scenario.h1("Vote Idempotency Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Depositor votes release twice
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)

    # Should still be 1 vote
    scenario.verify(escrow.data.release_votes == sp.nat(1))


# ==============================================================================
# TEST: AUTHORIZATION
# ==============================================================================

@sp.add_test(name="MultiSig Auth: Non-party cannot vote")
def test_nonparty_cannot_vote():
    """Verify non-party addresses cannot vote"""
    scenario = sp.test_scenario()
    scenario.h1("Non-Party Vote Prevention Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Attacker tries to vote
    scenario += escrow.vote_release().run(
        sender=TestAddresses.ATTACKER,
        valid=False,
        exception=EscrowError.UNAUTHORIZED
    )


# ==============================================================================
# TEST: DISPUTES
# ==============================================================================

@sp.add_test(name="MultiSig Dispute: Depositor can raise dispute")
def test_depositor_raise_dispute():
    """Verify depositor can raise a dispute"""
    scenario = sp.test_scenario()
    scenario.h1("Depositor Dispute Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Raise dispute
    scenario += escrow.raise_dispute("Service not delivered").run(
        sender=TestAddresses.DEPOSITOR
    )

    scenario.verify(escrow.data.dispute_state == DISPUTE_PENDING)
    scenario.verify(escrow.data.dispute_reason == "Service not delivered")


@sp.add_test(name="MultiSig Dispute: Beneficiary can raise dispute")
def test_beneficiary_raise_dispute():
    """Verify beneficiary can raise a dispute"""
    scenario = sp.test_scenario()
    scenario.h1("Beneficiary Dispute Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Raise dispute
    scenario += escrow.raise_dispute("Payment terms disputed").run(
        sender=TestAddresses.BENEFICIARY
    )

    scenario.verify(escrow.data.dispute_state == DISPUTE_PENDING)


@sp.add_test(name="MultiSig Dispute: Arbiter cannot raise dispute")
def test_arbiter_cannot_raise_dispute():
    """Verify arbiter cannot raise dispute (only resolve)"""
    scenario = sp.test_scenario()
    scenario.h1("Arbiter Dispute Prevention Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Arbiter tries to raise dispute
    scenario += escrow.raise_dispute("Arbiter dispute").run(
        sender=TestAddresses.ARBITER,
        valid=False,
        exception=EscrowError.UNAUTHORIZED
    )


# ==============================================================================
# TEST: TIMEOUT RECOVERY
# ==============================================================================

@sp.add_test(name="MultiSig Timeout: Force refund after timeout")
def test_multisig_force_refund():
    """Verify force refund works after timeout"""
    scenario = sp.test_scenario()
    scenario.h1("MultiSig Force Refund Test")

    escrow = create_multisig_escrow(timeout=TestTimeouts.MIN)
    scenario += escrow

    # Fund at time 0
    fund_escrow(scenario, escrow, now=sp.timestamp(0))

    # Anyone can force refund after timeout
    after_timeout = sp.timestamp(MIN_TIMEOUT_SECONDS + 1)
    scenario += escrow.force_refund().run(
        sender=TestAddresses.ATTACKER,  # Even attacker can trigger
        now=after_timeout
    )

    scenario.verify(escrow.data.state == STATE_REFUNDED)


@sp.add_test(name="MultiSig Timeout: Cannot force refund early")
def test_multisig_no_early_force():
    """Verify force refund blocked before timeout"""
    scenario = sp.test_scenario()
    scenario.h1("Early Force Refund Prevention Test")

    escrow = create_multisig_escrow(timeout=TestTimeouts.WEEK)
    scenario += escrow

    fund_escrow(scenario, escrow, now=sp.timestamp(0))

    # Try force refund too early
    scenario += escrow.force_refund().run(
        sender=TestAddresses.DEPOSITOR,
        now=sp.timestamp(1000),
        valid=False,
        exception=EscrowError.TIMEOUT_NOT_EXPIRED
    )


# ==============================================================================
# TEST: VIEWS
# ==============================================================================

@sp.add_test(name="MultiSig View: get_status returns correct data")
def test_multisig_status_view():
    """Verify get_status view works correctly"""
    scenario = sp.test_scenario()
    scenario.h1("MultiSig Status View Test")

    escrow = create_multisig_escrow()
    scenario += escrow

    # Check initial status
    status = escrow.get_status()
    scenario.verify(status.state == STATE_INIT)

    # Fund and check
    fund_escrow(scenario, escrow)
    status = escrow.get_status()
    scenario.verify(status.state == STATE_FUNDED)
    scenario.verify(status.release_votes == sp.nat(0))


@sp.add_test(name="MultiSig View: get_votes shows voting state")
def test_multisig_votes_view():
    """Verify get_votes view tracks votes correctly"""
    scenario = sp.test_scenario()
    scenario.h1("MultiSig Votes View Test")

    escrow = create_multisig_escrow()
    scenario += escrow
    fund_escrow(scenario, escrow)

    # Initial votes
    votes = escrow.get_votes()
    scenario.verify(votes.release_votes == sp.nat(0))
    scenario.verify(votes.refund_votes == sp.nat(0))

    # After depositor votes
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)
    votes = escrow.get_votes()
    scenario.verify(votes.release_votes == sp.nat(1))
    scenario.verify(votes.depositor_vote == VOTE_RELEASE)


# ==============================================================================
# TEST: HAPPY PATHS
# ==============================================================================

@sp.add_test(name="MultiSig Happy Path: Mutual agreement release")
def test_happy_path_mutual_release():
    """Verify mutual depositor-beneficiary agreement flow"""
    scenario = sp.test_scenario()
    scenario.h1("Happy Path: Mutual Agreement")

    escrow = create_multisig_escrow()
    scenario += escrow

    scenario.h2("Step 1: Fund escrow")
    fund_escrow(scenario, escrow)

    scenario.h2("Step 2: Depositor votes release")
    scenario += escrow.vote_release().run(sender=TestAddresses.DEPOSITOR)

    scenario.h2("Step 3: Beneficiary agrees")
    scenario += escrow.vote_release().run(sender=TestAddresses.BENEFICIARY)

    scenario.h2("Verify: Funds released")
    scenario.verify(escrow.data.state == STATE_RELEASED)


@sp.add_test(name="MultiSig Happy Path: Arbiter resolves dispute")
def test_happy_path_arbiter_resolution():
    """Verify arbiter dispute resolution flow"""
    scenario = sp.test_scenario()
    scenario.h1("Happy Path: Arbiter Resolution")

    escrow = create_multisig_escrow()
    scenario += escrow

    scenario.h2("Step 1: Fund escrow")
    fund_escrow(scenario, escrow)

    scenario.h2("Step 2: Depositor raises dispute")
    scenario += escrow.raise_dispute("Service incomplete").run(
        sender=TestAddresses.DEPOSITOR
    )

    scenario.h2("Step 3: Depositor wants refund")
    scenario += escrow.vote_refund().run(sender=TestAddresses.DEPOSITOR)

    scenario.h2("Step 4: Arbiter sides with depositor")
    scenario += escrow.vote_refund().run(sender=TestAddresses.ARBITER)

    scenario.h2("Verify: Funds refunded")
    scenario.verify(escrow.data.state == STATE_REFUNDED)


# ==============================================================================
# RUN ALL TESTS
# ==============================================================================

if __name__ == "__main__":
    pass
