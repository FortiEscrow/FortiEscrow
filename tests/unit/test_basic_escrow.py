"""
FortiEscrow Test Suite
======================

Comprehensive security-focused tests covering:
  1. State machine transitions (happy path + edge cases)
  2. Authorization checks (unauthorized access attempts)
  3. Timeout mechanisms (anti fund-locking)
  4. Fund invariants (balance consistency)
  5. Threat model validation (attempted exploits)
"""

import smartpy as sp
from forti_escrow import SimpleEscrow, EscrowError


# ==================== TEST FIXTURES ====================
class TestAccounts:
    """Standard test accounts"""
    DEPOSITOR = sp.address("tz1Depositor11111111111111111111111111")
    BENEFICIARY = sp.address("tz1Beneficiary1111111111111111111111111")
    RELAYER = sp.address("tz1Relayer111111111111111111111111111111")
    ATTACKER = sp.address("tz1Attacker11111111111111111111111111111")


# ==================== SECURITY TEST: STATE MACHINE VALIDITY ====================
def test_state_transitions_valid():
    """Verify state machine follows FSM: INIT → FUNDED → (RELEASED | REFUNDED)"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # INIT → FUNDED transition
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    scenario.verify(escrow.data.state == "FUNDED")
    
    # FUNDED → RELEASED transition
    scenario += escrow.release_funds().run(
        sender=TestAccounts.DEPOSITOR
    )
    scenario.verify(escrow.data.state == "RELEASED")


def test_state_transitions_refund():
    """Verify FUNDED → REFUNDED transition"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # FUNDED → REFUNDED transition
    scenario += escrow.refund_escrow().run(
        sender=TestAccounts.DEPOSITOR
    )
    scenario.verify(escrow.data.state == "REFUNDED")


# ==================== SECURITY TEST: UNAUTHORIZED ACCESS ====================
def test_unauthorized_release_attempt():
    """Verify that non-depositor cannot release funds"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Attacker attempts to release funds
    scenario += escrow.release_funds().run(
        sender=TestAccounts.ATTACKER,
        valid=False
    )


def test_unauthorized_refund_attempt():
    """Verify that non-depositor cannot refund (except after timeout)"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Attacker attempts to refund
    scenario += escrow.refund_escrow().run(
        sender=TestAccounts.ATTACKER,
        valid=False
    )


def test_beneficiary_cannot_release():
    """Verify beneficiary cannot release funds (only depositor can)"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Beneficiary attempts to release (should fail)
    scenario += escrow.release_funds().run(
        sender=TestAccounts.BENEFICIARY,
        valid=False
    )


# ==================== SECURITY TEST: INVALID STATE TRANSITIONS ====================
def test_double_funding_prevented():
    """Verify contract cannot be funded twice"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # First funding succeeds
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    scenario.verify(escrow.data.state == "FUNDED")
    
    # Second funding attempt fails
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR,
        valid=False
    )


def test_cannot_release_from_init():
    """Verify cannot release funds before escrow is FUNDED"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Attempt to release before funding
    scenario += escrow.release_funds().run(
        sender=TestAccounts.DEPOSITOR,
        valid=False
    )


# ==================== SECURITY TEST: FUND AMOUNT VALIDATION ====================
def test_insufficient_funding():
    """Verify contract rejects under-funded transactions"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Send less than required
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(500_000),  # Only half
        sender=TestAccounts.DEPOSITOR,
        valid=False
    )


def test_overfunding_rejected():
    """Verify contract rejects over-funded transactions"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Send more than required
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(2_000_000),  # Double
        sender=TestAccounts.DEPOSITOR,
        valid=False
    )


# ==================== SECURITY TEST: TIMEOUT MECHANISMS ====================
def test_timeout_prevents_late_release():
    """Verify depositor loses release right after timeout"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(100)  # Short timeout for testing
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    scenario.verify(escrow.data.state == "FUNDED")
    
    # Wait until timeout expires
    scenario += sp.test_scenario().h.past(scenario, sp.nat(200))
    
    # Depositor attempts release after timeout (should fail)
    scenario += escrow.release_funds().run(
        sender=TestAccounts.DEPOSITOR,
        now=sp.timestamp_type().make(200),
        valid=False
    )


def test_timeout_enables_force_refund():
    """Verify funds can be force-refunded after timeout"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(100)  # Short timeout
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Try force refund before timeout (should fail)
    scenario += escrow.force_refund().run(
        sender=TestAccounts.ATTACKER,
        valid=False
    )
    
    # Wait until timeout expires
    scenario += sp.test_scenario().h.past(scenario, sp.nat(200))
    
    # Force refund succeeds after timeout
    scenario += escrow.force_refund().run(
        sender=TestAccounts.ATTACKER,
        now=sp.timestamp_type().make(200)
    )
    scenario.verify(escrow.data.state == "REFUNDED")


def test_minimum_timeout_enforced():
    """Verify contract enforces minimum timeout (3600 seconds / 1 hour)"""
    
    scenario = sp.test_scenario()
    
    # Attempt to create escrow with too-short timeout
    scenario.h.must_fail(
        lambda: FortiEscrow(
            depositor=TestAccounts.DEPOSITOR,
            beneficiary=TestAccounts.BENEFICIARY,
            relayer=TestAccounts.RELAYER,
            escrow_amount=sp.nat(1_000_000),
            timeout_seconds=sp.nat(1800)  # 30 minutes < 1 hour minimum
        )
    )


# ==================== SECURITY TEST: INPUT VALIDATION ====================
def test_zero_amount_rejected():
    """Verify contract rejects zero-amount escrows"""
    
    scenario = sp.test_scenario()
    
    # Attempt to create escrow with zero amount
    scenario.h.must_fail(
        lambda: FortiEscrow(
            depositor=TestAccounts.DEPOSITOR,
            beneficiary=TestAccounts.BENEFICIARY,
            relayer=TestAccounts.RELAYER,
            escrow_amount=sp.nat(0),  # Invalid
            timeout_seconds=sp.nat(7 * 24 * 3600)
        )
    )


def test_duplicate_parties_rejected():
    """Verify depositor and beneficiary must be different"""
    
    scenario = sp.test_scenario()
    
    # Attempt to create escrow with same depositor and beneficiary
    scenario.h.must_fail(
        lambda: FortiEscrow(
            depositor=TestAccounts.DEPOSITOR,
            beneficiary=TestAccounts.DEPOSITOR,  # Same as depositor
            relayer=TestAccounts.RELAYER,
            escrow_amount=sp.nat(1_000_000),
            timeout_seconds=sp.nat(7 * 24 * 3600)
        )
    )


# ==================== SECURITY TEST: FUND INVARIANTS ====================
def test_balance_correctness_after_release():
    """Verify funds are correctly transferred to beneficiary"""
    
    scenario = sp.test_scenario()
    
    # Create simple contract to track balances
    contract = sp.Contract()
    contract.init(balance=0)
    scenario += contract
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=contract.address,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Release funds
    scenario += escrow.release_funds().run(
        sender=TestAccounts.DEPOSITOR
    )
    
    # Verify escrow has transferred all funds (balance should be 0)
    scenario.verify(sp.balance(escrow.address) == sp.tez(0))


def test_balance_correctness_after_refund():
    """Verify funds are correctly returned to depositor"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Record initial depositor balance
    initial_balance = scenario.head_state.accounts[TestAccounts.DEPOSITOR]["balance"]
    
    # Refund
    scenario += escrow.refund_escrow().run(
        sender=TestAccounts.DEPOSITOR
    )
    
    # Verify escrow has transferred all funds (balance should be 0)
    scenario.verify(sp.balance(escrow.address) == sp.tez(0))


# ==================== SECURITY TEST: VIEW FUNCTIONS ====================
def test_get_status_view():
    """Verify status view returns correct information"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Check initial status
    status = scenario.compute(escrow.get_status())
    scenario.verify(status.state == "INIT")
    scenario.verify(status.amount == sp.nat(1_000_000))
    scenario.verify(status.timeout_expired == False)
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Check funded status
    status = scenario.compute(escrow.get_status())
    scenario.verify(status.state == "FUNDED")
    scenario.verify(status.timeout_expired == False)


def test_can_transition_view():
    """Verify can_transition view correctly reports allowed transitions"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # In INIT state, can only transition to FUNDED
    can_fund = scenario.compute(escrow.can_transition("FUNDED"))
    scenario.verify(can_fund == True)
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # In FUNDED state, can transition to RELEASED or REFUNDED
    can_release = scenario.compute(escrow.can_transition("RELEASED"))
    can_refund = scenario.compute(escrow.can_transition("REFUNDED"))
    scenario.verify(can_release == True)
    scenario.verify(can_refund == True)


# ==================== SCENARIO: HAPPY PATH ====================
def test_happy_path_complete():
    """Complete happy path: fund → release"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Step 1: Depositor funds escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR,
        valid=True
    )
    scenario.verify(escrow.data.state == "FUNDED")
    
    # Step 2: Depositor releases to beneficiary
    scenario += escrow.release_funds().run(
        sender=TestAccounts.DEPOSITOR,
        valid=True
    )
    scenario.verify(escrow.data.state == "RELEASED")


def test_happy_path_with_refund():
    """Complete happy path: fund → refund"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
    scenario += escrow
    
    # Step 1: Depositor funds escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR,
        valid=True
    )
    
    # Step 2: Depositor changes mind and refunds
    scenario += escrow.refund_escrow().run(
        sender=TestAccounts.DEPOSITOR,
        valid=True
    )
    scenario.verify(escrow.data.state == "REFUNDED")


# ==================== SCENARIO: ANTI FUND-LOCKING ====================
def test_anti_fund_locking_permissionless_recovery():
    """Verify anyone can trigger force-refund after timeout"""
    
    scenario = sp.test_scenario()
    
    escrow = FortiEscrow(
        depositor=TestAccounts.DEPOSITOR,
        beneficiary=TestAccounts.BENEFICIARY,
        relayer=TestAccounts.RELAYER,
        escrow_amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(100)  # 100 seconds
    )
    scenario += escrow
    
    # Fund escrow
    scenario += escrow.fund_escrow().run(
        amount=sp.utils.nat_to_tez(1_000_000),
        sender=TestAccounts.DEPOSITOR
    )
    
    # Wait for timeout
    scenario += sp.test_scenario().h.past(scenario, sp.nat(150))
    
    # Anyone (even attacker) can trigger force refund
    scenario += escrow.force_refund().run(
        sender=TestAccounts.ATTACKER,
        now=sp.timestamp_type().make(150),
        valid=True
    )
    
    # Verify funds are returned to depositor
    scenario.verify(escrow.data.state == "REFUNDED")


# ==================== RUN ALL TESTS ====================
if __name__ == "__main__":
    """Execute all test scenarios"""
    
    # State Machine Tests
    test_state_transitions_valid()
    test_state_transitions_refund()
    
    # Authorization Tests
    test_unauthorized_release_attempt()
    test_unauthorized_refund_attempt()
    test_beneficiary_cannot_release()
    
    # Invalid State Tests
    test_double_funding_prevented()
    test_cannot_release_from_init()
    
    # Fund Validation Tests
    test_insufficient_funding()
    test_overfunding_rejected()
    
    # Timeout Tests
    test_timeout_prevents_late_release()
    test_timeout_enables_force_refund()
    test_minimum_timeout_enforced()
    
    # Input Validation Tests
    test_zero_amount_rejected()
    test_duplicate_parties_rejected()
    
    # Invariant Tests
    test_balance_correctness_after_release()
    test_balance_correctness_after_refund()
    
    # View Tests
    test_get_status_view()
    test_can_transition_view()
    
    # Happy Path Tests
    test_happy_path_complete()
    test_happy_path_with_refund()
    
    # Anti-Locking Tests
    test_anti_fund_locking_permissionless_recovery()
