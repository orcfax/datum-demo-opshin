"""Refund the deposited tokens."""

import sys

from config import context, network
from contract import RefundRedeemer  # pylint: disable=E0611
from library import (
    client_address,
    client_skey,
    client_vkey,
    collateral_address,
    collateral_skey,
    collateral_vkey,
    get_contract_script,
    logger,
    save_transaction,
    submit_and_log_tx,
)
from pycardano import Address, Redeemer, TransactionBuilder, UTxO, plutus_script_hash


def refund_tokens():
    """Refund the deposited tokens."""
    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)
    logger.info("script address: %s", script_address)

    script_utxos = context.utxos(str(script_address))
    sc_utxo = None
    utxo_to_spend = None
    for item in script_utxos:
        if item.output.script:
            sc_utxo: UTxO = item
        elif item.output.datum:
            utxo_to_spend: UTxO = item

    if not sc_utxo:
        logger.warning("smart contract UTxO not found!")
        sys.exit(0)

    if not utxo_to_spend:
        logger.warning("no utxo to refund!")
        sys.exit(0)

    collateral_utxo = context.utxos(str(collateral_address))[0]
    redeemer = Redeemer(RefundRedeemer())

    logger.info("Creating the transaction...")
    transaction = TransactionBuilder(context)
    transaction.reference_inputs.add(sc_utxo)
    transaction.add_script_input(utxo_to_spend, redeemer=redeemer)
    # transaction.add_script_input(utxo_to_spend, redeemer=redeemer, script=contract_script)
    transaction.collaterals.append(collateral_utxo)
    transaction.required_signers = [client_vkey.hash(), collateral_vkey.hash()]
    transaction.validity_start = context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600
    logger.info("Signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [client_skey, collateral_skey], change_address=client_address
    )
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_client_refund.signed")
    submit_and_log_tx(signed_tx)


def main():
    """Primary entry point for this script."""
    refund_tokens()


if __name__ == "__main__":
    main()
