"""OpShin contract.

Will be built using the command:

    * opshin build minting contract.py '{"bytes": "<payment_address_key>"}'

"""

from opshin.prelude import *


def validator(pkh: PubKeyHash, redeemer: None, context: ScriptContext) -> None:
    """Minting validation function."""
    purpose = context.purpose
    if isinstance(purpose, Minting):
        p = purpose.policy_id
    else:
        assert False, "Wrong redeeming purpose"
    if any([x > 0 for x in context.tx_info.mint.get(p, {b"": 0}).values()]):
        # Checking the public key hash of the owner.
        sig_present = pkh in context.tx_info.signatories
        master_sig_present = pkh in context.tx_info.signatories
        assert sig_present or master_sig_present, "Required signature missing"
    else:
        # Burning is allowed.
        pass
