"""Deploy the smart contract example."""

import binascii
import logging
import sys

import pycardano as pyc

import config
import contract
import library

logger = logging.getLogger(__name__)


def deploy_contract():
    """Deploy the smart contract on-chain.

    Once the script has been built and deployed and then finished with,
    it is a sensible idea to undeploy it and release the value associated
    with this script's UTxO. For this repository a script should be
    undeployed before a new one is built so that the script's address
    is preserved.
    """
    contract_script = library.get_contract_script()
    script_hash = pyc.plutus_script_hash(contract_script)
    script_address = pyc.Address(script_hash, network=config.network)
    deployer_address = library.payment_address
    deployer = library.payment_vkey.hash().to_primitive()
    deployer_skey = library.payment_skey
    fee_address = library.payment_address.payment_part.to_primitive()
    logger.info("script deployer address: %s", library.payment_address)
    logger.info("script address: %s", script_address)
    logger.info(
        "fee address derived from payment address: %s",
        pyc.Address(library.payment_address.payment_part),
    )
    logger.info("fee address PKH: %s", binascii.hexlify(fee_address).decode())
    script_value = pyc.Value(70000000)
    fee = 1000000
    datum = contract.PublishParams(source=deployer, fee_address=fee_address, fee=fee)
    logger.info("creating the transaction...")
    transaction = pyc.TransactionBuilder(config.context)
    transaction.add_input_address(deployer_address)
    transaction.add_output(
        pyc.TransactionOutput(
            script_address, amount=script_value, datum=datum, script=contract_script
        )
    )
    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [deployer_skey], change_address=deployer_address
    )
    logger.info("signed tx id: %s", signed_tx.id)
    library.save_transaction(signed_tx, "tx_client_deploy.signed")
    logger.info("submitting the transaction...")
    library.submit_and_log_tx(signed_tx)
    logger.info("done")


def main():
    """Primary entry point for this script."""
    try:
        deploy_contract()
    except pyc.PyCardanoException as err:
        logger.error("deploy script failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
