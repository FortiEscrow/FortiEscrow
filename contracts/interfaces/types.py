"""
FortiEscrow Type Definitions

Shared type definitions for all escrow contracts.
"""

import smartpy as sp


# State Machine States
STATE_INIT = "INIT"
STATE_FUNDED = "FUNDED"
STATE_RELEASED = "RELEASED"
STATE_REFUNDED = "REFUNDED"

VALID_STATES = [STATE_INIT, STATE_FUNDED, STATE_RELEASED, STATE_REFUNDED]


# Party Information
class PartyInfo(sp.Record):
    """Information about a party in the escrow"""
    depositor = sp.TAddress
    beneficiary = sp.TAddress
    relayer = sp.TAddress


# Escrow Parameters
class EscrowParams(sp.Record):
    """Escrow configuration parameters"""
    escrow_amount = sp.TNat
    timeout_seconds = sp.TNat


# Escrow State
class EscrowState(sp.Record):
    """Current state of escrow"""
    state = sp.TString
    funded_timestamp = sp.TInt
    is_locked = sp.TBool
