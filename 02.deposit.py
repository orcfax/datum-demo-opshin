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
    client_address,
    client_skey,
    client_vkey,
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
    Value,
    plutus_script_hash,
)


def deposit_script():
    """Deposit funds."""
    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)

    # logger.info("publisher address: %s", client_address)
    logger.info("script address: %s", script_address)

    source = client_vkey.hash().to_primitive()
    fee_address = payment_address.payment_part.to_primitive()
    logger.info(
        "fee address: %s", Address(payment_address.payment_part, network=network)
    )

    fee = 1000000
    datum = PublishParams(source, fee_address, fee)

    logger.info("Creating the transaction...")
    transaction = TransactionBuilder(context)
    transaction.add_input_address(payment_address)

    # logger.info("lovelace amount: %s", LOVELACE_AMOUNT)
    # logger.info("token name: %s", TOKEN_NAME)
    # logger.info("policy id: %s", POLICY_ID)
    # logger.info("tokens amount: %s", tokens_amount)

    amount = 2000000

    transaction.add_output(
        TransactionOutput(address=script_address, amount=amount, datum=datum)
    )

    # transaction.add_output(
    #    TransactionOutput(
    #        script_address,
    #        Value.from_primitive(
    #            [
    #                LOVELACE_AMOUNT,
    #                {bytes.fromhex(POLICY_ID): {TOKEN_NAME: tokens_amount}},
    #            ]
    #        ),
    #        datum=datum,
    #    )
    # )

    logger.info("Signing the transaction...")

    try:
        signed_tx = transaction.build_and_sign(
            [payment_skey], change_address=payment_address
        )
    except UTxOSelectionException as err:
        logger.info("problem submitting tx check there are tokens minted: %s", err)
        sys.exit(1)

    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_client_deposit.signed")
    submit_and_log_tx(signed_tx)


def main():
    """Primary entry point for this script."""
    deposit_script()


if __name__ == "__main__":
    main()
