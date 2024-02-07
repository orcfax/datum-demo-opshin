"""Deploy the smart contract example."""

import binascii
import sys

from config import context, network
from contract import PublishParams  # pylint: disable=E0611
from library import (
    get_contract_script,
    logger,
    payment_address,
    payment_skey,
    payment_vkey,
    save_transaction,
    submit_and_log_tx,
)
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    UTxOSelectionException,
    Value,
    plutus_script_hash,
)


def deploy_contract():
    """Deploy the smart contract."""
    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)
    deployer_address = payment_address
    deployer = payment_vkey.hash().to_primitive()
    deployer_skey = payment_skey
    fee_address = payment_address.payment_part.to_primitive()

    logger.info("Script deployer address: %s", payment_address)
    logger.info("Script address: %s", script_address)
    logger.info(
        "Fee address derived from payment address: %s",
        Address(payment_address.payment_part),
    )
    logger.info("Fee address PKH: %s", binascii.hexlify(fee_address).decode())

    script_value = Value(70000000)

    fee = 1000000
    datum = PublishParams(source=deployer, fee_address=fee_address, fee=fee)

    logger.info("Creating the transaction...")
    transaction = TransactionBuilder(context)
    transaction.add_input_address(deployer_address)
    transaction.add_output(
        TransactionOutput(
            script_address, amount=script_value, datum=datum, script=contract_script
        )
    )
    logger.info("Signing the transaction...")
    try:
        signed_tx = transaction.build_and_sign(
            [deployer_skey], change_address=deployer_address
        )
    except UTxOSelectionException as err:
        logger.error("ensure wallet: '%s' is funded: %s", deployer_address, err)
        sys.exit(1)
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_client_deploy.signed")
    logger.info("Submitting the transaction...")
    submit_and_log_tx(signed_tx)
    logger.info("Done.")


def main():
    """Primary entry point for this script."""
    deploy_contract()


if __name__ == "__main__":
    main()
