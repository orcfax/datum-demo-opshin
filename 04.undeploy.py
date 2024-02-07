"""Undeploy the smart contract."""


import sys

from config import context, network
from contract import RefundRedeemer  # pylint: disable=E0611
from library import (
    get_contract_script,
    logger,
    payment_address,
    payment_skey,
    payment_vkey,
    save_transaction,
    submit_and_log_tx,
)
from pycardano import Address, Redeemer, TransactionBuilder, plutus_script_hash


def undeploy_contract():
    """Undeploy the smart contract."""
    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)
    logger.info("script address: %s", script_address)

    script_utxos = context.utxos(str(script_address))
    sc_utxo = ""
    utxo_to_spend = ""
    for item in script_utxos:
        if item.output.script:
            sc_utxo = item
            utxo_to_spend = item

    if not sc_utxo or not utxo_to_spend:
        logger.warning("no script input or not utxo to spend!")
        sys.exit(0)

    collateral_address = payment_address
    collateral_amount: Final[int] = 3607615
    collateral_utxos = context.utxos(str(collateral_address))
    collateral_utxo = None
    for collateral in collateral_utxos:
        if int(collateral.output.amount.coin) > collateral_amount:
            collateral_utxo = collateral
            break

    redeemer = Redeemer(RefundRedeemer())

    logger.info("creating the transaction...")
    transaction = TransactionBuilder(context)
    transaction.add_script_input(sc_utxo, redeemer=redeemer)
    transaction.collaterals.append(collateral_utxo)
    transaction.validity_start = context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600
    transaction.required_signers = [payment_vkey.hash()]
    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [payment_skey], change_address=payment_address
    )
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_client_undeploy.signed")
    logger.info("submitting the transaction...")
    submit_and_log_tx(signed_tx)
    logger.info("done")


def main():
    """Primary entry point for this script."""
    undeploy_contract()


if __name__ == "__main__":
    main()
