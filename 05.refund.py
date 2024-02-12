"""Refund the deposited tokens."""

import logging
import sys
from typing import Final

import pycardano as pyc

import config
import contract
import library

logger = logging.getLogger(__name__)


def refund_tokens():
    """Refund the deposited value if it hasn't already been claimed
    by the claimant.
    """
    contract_script = library.get_contract_script()
    script_hash = pyc.plutus_script_hash(contract_script)
    script_address = pyc.Address(script_hash, network=config.network)
    logger.info("script address: %s", script_address)
    logger.info("refund address: %s", library.payment_address)
    script_utxos = config.context.utxos(str(script_address))
    sc_utxo = None
    utxo_to_spend = None
    for item in script_utxos:
        if item.output.script:
            sc_utxo: pyc.UTxO = item
        elif item.output.datum:
            utxo_to_spend: pyc.UTxO = item
    if not sc_utxo:
        logger.warning("smart contract UTxO not found!")
        sys.exit(0)
    if not utxo_to_spend:
        logger.warning("no utxo to refund!")
        sys.exit(0)
    collateral_address = library.payment_address
    collateral_amount: Final[int] = 3607615
    collateral_utxos = config.context.utxos(str(collateral_address))
    collateral_utxo = None
    for collateral in collateral_utxos:
        if int(collateral.output.amount.coin) > collateral_amount:
            collateral_utxo = collateral
            break
    redeemer = pyc.Redeemer(contract.RefundRedeemer())
    logger.info("creating the transaction...")
    transaction = pyc.TransactionBuilder(config.context)
    transaction.reference_inputs.add(sc_utxo)
    transaction.add_script_input(utxo_to_spend, redeemer=redeemer)
    transaction.collaterals.append(collateral_utxo)
    transaction.required_signers = [library.payment_vkey.hash()]
    transaction.validity_start = config.context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600
    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [library.payment_skey], change_address=library.payment_address
    )
    logger.info(signed_tx.id)
    library.save_transaction(signed_tx, "tx_client_refund.signed")
    library.submit_and_log_tx(signed_tx)
    logger.info("done")


def main():
    """Primary entry point for this script."""
    try:
        refund_tokens()
    except pyc.PyCardanoException as err:
        logger.error("refund script failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
