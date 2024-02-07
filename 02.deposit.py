"""Deposit tokens with the smart contract address."""

# pylint: disable=E0611

import sys

from config import (
    LOVELACE_AMOUNT,
    context,
    network,
)
from contract import PublishParams
from library import (
    get_contract_script,
    logger,
    payment_address,
    save_transaction,
    submit_and_log_tx,
    payment_skey,
    payment_vkey,
)
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    UTxOSelectionException,
    plutus_script_hash,
)


def deposit_script():
    """Deposit funds."""
    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)
    source = payment_vkey.hash().to_primitive()
    fee_address = payment_address.payment_part.to_primitive()

    logger.info("script address: %s", script_address)
    logger.info(
        "fee address: %s", Address(payment_address.payment_part, network=network)
    )

    fee = 1000000
    datum = PublishParams(source, fee_address, fee)

    logger.info("creating the transaction...")
    transaction = TransactionBuilder(context)
    transaction.add_input_address(payment_address)

    amount = 2000000
    transaction.add_output(
        TransactionOutput(address=script_address, amount=amount, datum=datum)
    )

    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [payment_skey], change_address=payment_address
    )
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_client_deposit.signed")
    submit_and_log_tx(signed_tx)


def main():
    """Primary entry point for this script."""
    deposit_script()


if __name__ == "__main__":
    main()
