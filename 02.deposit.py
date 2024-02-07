"""Deposit tokens with the smart contract address."""

# pylint: disable=E0611

import logging
import sys

import pycardano as pyc

import config
import contract
import library

logger = logging.getLogger(__name__)


def deposit_value():
    """Deposit a small token value for someone to claim.

    If the deposit isn't claimed before the smart contract is taken
    off-chain then a `refund.py` script must be used to return the
    value to the payee.
    """
    contract_script = library.get_contract_script()
    script_hash = pyc.plutus_script_hash(contract_script)
    script_address = pyc.Address(script_hash, network=config.network)
    source = library.payment_vkey.hash().to_primitive()
    fee_address = library.payment_address.payment_part.to_primitive()
    logger.info("script address: %s", script_address)
    logger.info(
        "fee address: %s",
        pyc.Address(library.payment_address.payment_part, network=config.network),
    )
    fee = 1000000
    datum = contract.PublishParams(source, fee_address, fee)
    logger.info("creating the transaction...")
    transaction = pyc.TransactionBuilder(config.context)
    transaction.add_input_address(library.payment_address)
    amount = 2000000
    transaction.add_output(
        pyc.TransactionOutput(address=script_address, amount=amount, datum=datum)
    )
    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [library.payment_skey], change_address=library.payment_address
    )
    logger.info("signed tx id: %s", signed_tx.id)
    library.save_transaction(signed_tx, "tx_client_deposit.signed")
    library.submit_and_log_tx(signed_tx)


def main():
    """Primary entry point for this script."""
    try:
        deposit_value()
    except pyc.PyCardanoException as err:
        logger.error("deposit value script failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
