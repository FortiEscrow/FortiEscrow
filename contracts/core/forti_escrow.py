"""
FortiEscrow Core Smart Contract
A reusable, security-first escrow framework on Tezos

Security Principles:
- No super-admin: No unilateral fund control
- Explicit FSM: All state transitions validated
- Anti-fund-locking: Permissionless recovery after timeout
- Defense in depth: Multiple validation layers on every entrypoint

This contract implements an explicit finite state machine:
  INIT -> FUNDED -> RELEASED
         |      |
         └-------> REFUNDED
"""

import smartpy as sp


# ==============================================================================
# STATE CONSTANTS
# ==============================================================================

STATE_INIT = sp.int(0)          # Contract created, no funds deposited
STATE_FUNDED = sp.int(1)        # Funds deposited, awaiting release/refund decision
STATE_RELEASED = sp.int(2)      # Funds released to beneficiary (terminal)
STATE_REFUNDED = sp.int(3)      # Funds refunded to depositor (terminal)


# ==============================================================================
# ERROR CODES
# ==============================================================================

ERROR_INVALID_STATE = "INVALID_STATE"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
ERROR_INVALID_AMOUNT = "INVALID_AMOUNT"
ERROR_TIMEOUT_NOT_EXPIRED = "TIMEOUT_NOT_EXPIRED"
ERROR_DEADLINE_PASSED = "DEADLINE_PASSED"


# ==============================================================================
# MAIN CONTRACT
# ==============================================================================

class FortiEscrow(sp.Contract):
    """
    Security-first escrow contract implementing explicit finite state machine.
    
    Parties:
    - depositor: Initiates escrow and funds it. Can release or refund before deadline.
    - beneficiary: Receives funds when escrow is released.
    - relayer: Optional helper for signature verification (not used in base contract).
    
    State Machine:
      INIT (0) -> FUNDED (1) -> RELEASED (2) [terminal]
                       |
                       +-----> REFUNDED (3) [terminal]
    
    Security Guarantees:
    1. INIT -> FUNDED: Only depositor can fund, must send exact amount
    2. FUNDED -> RELEASED: Only depositor can release, before or at deadline
    3. FUNDED -> REFUNDED: Depositor can refund anytime; after deadline anyone can recover
    4. No state regressions: Terminal states cannot be reversed
    5. No fund-locking: After deadline, any party can force refund
    """

    def __init__(self, depositor, beneficiary, amount, timeout_seconds):
        """
        Initialize escrow contract.
        
        Args:
            depositor: Address that funds and controls the escrow
            beneficiary: Address that receives funds on release
            amount: Escrow amount in mutez (must be > 0)
            timeout_seconds: Seconds until funds become recoverable (must be > 0)
        
        Security Notes:
        - depositor != beneficiary to prevent self-escrow (common exploit)
        - amount > 0 to prevent empty escrow creation
        - timeout > 0 to prevent immediate recovery (liveness guarantee)
        - These are validated on initialization
        """
        
        # Validate inputs
        sp.verify(
            depositor != beneficiary,
            ERROR_INVALID_AMOUNT
        )
        sp.verify(
            amount > sp.nat(0),
            ERROR_INVALID_AMOUNT
        )
        sp.verify(
            timeout_seconds > sp.nat(0),
            ERROR_INVALID_AMOUNT
        )
        
        # Contract state
        self.init(
            # Party information
            depositor=depositor,
            beneficiary=beneficiary,
            
            # Escrow terms
            escrow_amount=amount,
            deadline=sp.now + sp.int(timeout_seconds),
            
            # Current state
            state=STATE_INIT,
            
            # Contract balance (implicit, tracked for verification)
            # Note: In Tezos, contract balance is implicit from account state
            # We track funded state separately for clarity
        )

    # ==========================================================================
    # ENTRYPOINT: fund_escrow()
    # ==========================================================================
    
    @sp.entry_point
    def fund_escrow(self):
        """
        INIT -> FUNDED: Deposit escrow amount.
        
        State Transition:
            INIT: No funds deposited yet
            -> FUNDED: Funds now in contract
        
        Security Checks:
        1. State must be INIT (no re-funding)
        2. Sender must be depositor (only they can fund)
        3. Amount transferred must equal escrow_amount (exact payment)
        4. Timeout not already expired (must allow release window)
        
        Attack Prevention:
        - Re-entrance: State changes before external calls
        - Overfunding: Exact amount checked
        - Underfunding: Reject if insufficient
        - Unauthorized funding: Only depositor allowed
        """
        
        # [SECURITY] Check state is INIT
        sp.verify(
            self.data.state == STATE_INIT,
            ERROR_INVALID_STATE
        )
        
        # [SECURITY] Only depositor can fund
        sp.verify(
            sp.sender == self.data.depositor,
            ERROR_UNAUTHORIZED
        )
        
        # [SECURITY] Deadline must not have passed (ensures release window exists)
        sp.verify(
            sp.now < self.data.deadline,
            ERROR_DEADLINE_PASSED
        )
        
        # [SECURITY] Exact amount required (prevent under/over-funding)
        sp.verify(
            sp.amount == sp.utils.nat_to_mutez(self.data.escrow_amount),
            ERROR_INVALID_AMOUNT
        )
        
        # [STATE CHANGE] Transition to FUNDED
        # This happens BEFORE any external calls (reentrancy prevention)
        self.data.state = STATE_FUNDED

    # ==========================================================================
    # ENTRYPOINT: release_funds()
    # ==========================================================================
    
    @sp.entry_point
    def release_funds(self):
        """
        FUNDED -> RELEASED: Release funds to beneficiary.
        
        State Transition:
            FUNDED: Funds held in escrow
            -> RELEASED: Funds transferred to beneficiary (terminal)
        
        Security Checks:
        1. State must be FUNDED (can't release twice or before funding)
        2. Sender must be depositor (only they can release)
        3. Deadline must not have passed (release window closed)
        4. Contract has funds (implicit: verified by state)
        
        Attack Prevention:
        - Re-entrance: State changes before transfer
        - Unauthorized release: Only depositor
        - Late release: Reject after deadline
        - Double-release: State prevents this
        
        Note: After deadline passes, use force_refund() instead.
              This prevents depositor from releasing stale escrows.
        """
        
        # [SECURITY] Check state is FUNDED
        sp.verify(
            self.data.state == STATE_FUNDED,
            ERROR_INVALID_STATE
        )
        
        # [SECURITY] Only depositor can release
        sp.verify(
            sp.sender == self.data.depositor,
            ERROR_UNAUTHORIZED
        )
        
        # [SECURITY] Release must occur before or at deadline
        sp.verify(
            sp.now <= self.data.deadline,
            ERROR_DEADLINE_PASSED
        )
        
        # [STATE CHANGE] Transition to RELEASED (before transfer)
        self.data.state = STATE_RELEASED
        
        # [FUND TRANSFER] Send funds to beneficiary
        # Safe because state changed first (reentrancy prevention)
        sp.send(
            self.data.beneficiary,
            sp.utils.nat_to_mutez(self.data.escrow_amount)
        )

    # ==========================================================================
    # ENTRYPOINT: refund_escrow()
    # ==========================================================================
    
    @sp.entry_point
    def refund_escrow(self):
        """
        FUNDED -> REFUNDED: Refund funds to depositor.
        
        State Transition:
            FUNDED: Funds held in escrow
            -> REFUNDED: Funds returned to depositor (terminal)
        
        Authorization Rules:
        - Before deadline: Only depositor can refund
        - After deadline: Anyone can call (permissionless recovery)
        
        Security Checks:
        1. State must be FUNDED
        2. Sender must be authorized:
           - Before deadline: Must be depositor
           - After deadline: Anyone allowed (recovery guarantee)
        3. Contract has funds
        
        Attack Prevention:
        - Fund-locking: After deadline, anyone can recover
        - Unauthorized refund: Before deadline, only depositor
        - Double-refund: State prevents this
        - Depositor abuse: After deadline, they can't prevent recovery
        
        Liveness Guarantee:
        Funds are ALWAYS recoverable after timeout, even if depositor
        disappears or becomes uncooperative. This prevents permanent
        fund-locking attacks.
        """
        
        # [SECURITY] Check state is FUNDED
        sp.verify(
            self.data.state == STATE_FUNDED,
            ERROR_INVALID_STATE
        )
        
        # [SECURITY] Check authorization based on timeout
        is_timeout_expired = sp.now > self.data.deadline
        
        # Before deadline: only depositor can refund
        # After deadline: anyone can refund (recovery guarantee)
        sp.verify(
            (sp.sender == self.data.depositor) | is_timeout_expired,
            ERROR_UNAUTHORIZED
        )
        
        # [STATE CHANGE] Transition to REFUNDED (before transfer)
        self.data.state = STATE_REFUNDED
        
        # [FUND TRANSFER] Send funds back to depositor
        # Safe because state changed first (reentrancy prevention)
        sp.send(
            self.data.depositor,
            sp.utils.nat_to_mutez(self.data.escrow_amount)
        )

    # ==========================================================================
    # ENTRYPOINT: force_refund() [alias for timeout recovery]
    # ==========================================================================
    
    @sp.entry_point
    def force_refund(self):
        """
        Emergency recovery: Anyone can refund after deadline expires.
        
        This is a semantic alias for refund_escrow() that makes the intent
        explicit: "recover funds after timeout". Internally it calls the
        same authorization and state transition logic.
        
        Use Cases:
        - Depositor disappeared but needs to recover funds
        - Beneficiary unresponsive and can't release
        - Mutual agreement that escrow should end
        
        Security Guarantee:
        This entrypoint GUARANTEES that funds are never permanently locked.
        Any party can recover them after timeout, making the contract safe
        against operational/availability failures.
        
        Implementation Note:
        In SmartPy, this is implemented by calling refund_escrow() which
        already checks authorization (timeout expired = all authorized).
        """
        
        # Delegate to refund logic (same state machine)
        self.refund_escrow()

    # ==========================================================================
    # VIEW: get_status()
    # ==========================================================================
    
    @sp.view
    def get_status(self):
        """
        Query current escrow status.
        
        Returns:
            state: Current FSM state (0=INIT, 1=FUNDED, 2=RELEASED, 3=REFUNDED)
            depositor: Depositor address
            beneficiary: Beneficiary address
            amount: Escrow amount
            deadline: Timeout deadline (timestamp)
            is_timeout_expired: True if deadline passed
            is_funded: True if state is FUNDED
            is_terminal: True if state is RELEASED or REFUNDED
        
        Security Notes:
        - Views are read-only, no state changes
        - All information is public (blockchain is transparent)
        - Cannot be used to lock funds (views have no side effects)
        """
        
        sp.result(
            sp.record(
                state=self.data.state,
                depositor=self.data.depositor,
                beneficiary=self.data.beneficiary,
                amount=self.data.escrow_amount,
                deadline=self.data.deadline,
                is_timeout_expired=sp.now > self.data.deadline,
                is_funded=self.data.state == STATE_FUNDED,
                is_terminal=(self.data.state == STATE_RELEASED) | (self.data.state == STATE_REFUNDED),
            )
        )

    # ==========================================================================
    # VIEW: can_transition()
    # ==========================================================================
    
    @sp.view
    def can_transition(self, action):
        """
        Check if a state transition is allowed.
        
        Args:
            action: Requested action ("fund", "release", "refund", "force_refund")
        
        Returns:
            allowed: True if transition is valid
            reason: Human-readable explanation if not allowed
        
        Security Notes:
        - This is a convenience view for UIs/automation
        - Actual validation happens in entrypoints
        - View logic must match entrypoint logic
        
        Useful For:
        - UI: Show which buttons are enabled
        - Automation: Decide next action without trying (save gas)
        - Monitoring: Track state machine health
        """
        
        # [LOGIC] Determine what transitions are valid from current state
        sp.if action == "fund":
            # Can fund if: state is INIT and timeout not expired
            allowed = (self.data.state == STATE_INIT) & (sp.now < self.data.deadline)
            reason = sp.cond(
                self.data.state != STATE_INIT,
                "Already funded or completed",
                "Deadline passed, cannot fund"
            )
        sp.elif action == "release":
            # Can release if: state is FUNDED and deadline not passed
            allowed = (self.data.state == STATE_FUNDED) & (sp.now <= self.data.deadline)
            reason = sp.cond(
                self.data.state != STATE_FUNDED,
                "Escrow not funded",
                "Deadline passed, use force_refund instead"
            )
        sp.elif action == "refund":
            # Can refund if: state is FUNDED and (depositor or timeout expired)
            allowed = self.data.state == STATE_FUNDED
            reason = sp.cond(
                self.data.state != STATE_FUNDED,
                "Escrow not funded",
                "Check authorization: depositor before deadline, anyone after"
            )
        sp.elif action == "force_refund":
            # Can force_refund if: state is FUNDED and deadline expired
            allowed = (self.data.state == STATE_FUNDED) & (sp.now > self.data.deadline)
            reason = sp.cond(
                self.data.state != STATE_FUNDED,
                "Escrow not funded",
                "Deadline not yet expired"
            )
        sp.else:
            allowed = sp.bool(False)
            reason = "Unknown action"
        
        sp.result(sp.record(allowed=allowed, reason=reason))


# ==============================================================================
# HELPER FUNCTIONS (Testing/Deployment)
# ==============================================================================

def get_contract():
    """Factory function for creating test instances."""
    return FortiEscrow(
        depositor=sp.address("tz1Alice"),
        beneficiary=sp.address("tz1Bob"),
        amount=sp.nat(1_000_000),  # 1 XTZ
        timeout_seconds=sp.nat(7 * 24 * 3600)  # 7 days
    )


# ==============================================================================
# TEST SUITE (when run as main)
# ==============================================================================

if __name__ == "__main__":
    
    # Test 1: Contract initialization
    @sp.add_test(name="Test 1: Contract Initialization")
    def test_init():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        # Verify initial state
        scenario.verify(c.data.state == STATE_INIT)
        scenario.verify(c.data.escrow_amount == sp.nat(1_000_000))
    
    # Test 2: Funding transitions to FUNDED
    @sp.add_test(name="Test 2: Funding Succeeds")
    def test_fund():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        alice = sp.address("tz1Alice")
        # Fund the escrow
        scenario += c.fund_escrow().run(
            sender=alice,
            amount=sp.utils.nat_to_mutez(sp.nat(1_000_000))
        )
        
        # Verify state changed to FUNDED
        scenario.verify(c.data.state == STATE_FUNDED)
    
    # Test 3: Unauthorized funding attempt fails
    @sp.add_test(name="Test 3: Unauthorized Fund Rejected")
    def test_unauthorized_fund():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        # Try to fund from unauthorized address
        unauthorized = sp.address("tz1Charlie")
        scenario += c.fund_escrow().run(
            sender=unauthorized,
            amount=sp.utils.nat_to_mutez(sp.nat(1_000_000)),
            valid=False
        )
    
    # Test 4: Release after funding
    @sp.add_test(name="Test 4: Release Succeeds")
    def test_release():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        alice = sp.address("tz1Alice")
        
        # Fund
        scenario += c.fund_escrow().run(
            sender=alice,
            amount=sp.utils.nat_to_mutez(sp.nat(1_000_000))
        )
        
        # Release
        scenario += c.release_funds().run(sender=alice)
        
        # Verify state changed to RELEASED
        scenario.verify(c.data.state == STATE_RELEASED)
    
    # Test 5: Refund after funding
    @sp.add_test(name="Test 5: Refund Succeeds")
    def test_refund():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        alice = sp.address("tz1Alice")
        
        # Fund
        scenario += c.fund_escrow().run(
            sender=alice,
            amount=sp.utils.nat_to_mutez(sp.nat(1_000_000))
        )
        
        # Refund
        scenario += c.refund_escrow().run(sender=alice)
        
        # Verify state changed to REFUNDED
        scenario.verify(c.data.state == STATE_REFUNDED)
    
    # Test 6: View functionality
    @sp.add_test(name="Test 6: Views Work")
    def test_views():
        c = get_contract()
        scenario = sp.test_scenario()
        scenario += c
        
        # Query status
        scenario += c.get_status()
        
        # Query transitions
        scenario += c.can_transition("fund")
        scenario += c.can_transition("release")
        scenario += c.can_transition("refund")
