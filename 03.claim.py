"""Request to claim the deposited tokens using the smart contract."""

# pylint: disable=R0914,R0915

import logging
import sys
from collections import OrderedDict
from datetime import datetime
from typing import Final

import cbor2
import pycardano as pyc

import config
import contract
import library

logger = logging.getLogger(__name__)


def get_script_and_claimables(
    script_address: pyc.Address,
) -> (pyc.UTxO, list[pyc.UTxO]):
    """Get UTxOs for the smart contract and claimable UTxOs."""
    script_utxos = config.context.utxos(str(script_address))
    sc_utxo = None
    claimable_utxos = []
    for item in script_utxos:
        if item.output.script:
            sc_utxo: pyc.UTxO = item
        elif item.output.datum:
            datum = cbor2.loads(item.output.datum.cbor)
            # PublishParams are validated in our smart contract.
            datum_obj = contract.PublishParams(
                datum.value[1][0], datum.value[1][1], datum.value[1][2]
            )
            fee_address = pyc.Address(
                pyc.VerificationKeyHash.from_primitive(datum_obj.fee_address),
                network=config.network,
            )
            claimable_utxos.append(
                {"fee_address": str(fee_address), "fee": datum_obj.fee, "utxo": item}
            )
    return sc_utxo, claimable_utxos


def decode_oracle_utxo(oracle_utxo: pyc.UTxO) -> (list, str):
    """Return values of interest from the Oracle UTxO."""
    decoded = library.decode_utxo(oracle_utxo)
    feed_name = decoded["name"].split("|")
    feed_value = decoded["value"]
    feed_time = decoded["valueReference"][0]["value"]
    feed_values = list(zip(feed_name, feed_value))
    timestamp = datetime.utcfromtimestamp(int(feed_time) / 1000).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return feed_values, timestamp


def generate_transaction_metadata(
    feed_values: list, timestamp: str
) -> (str, OrderedDict):
    """Create a metadata message to post alongside a successful smart-
    contract validation and transaction.

    More information about labels for Transaction Metadata can be
    found on the metadata registry.

       * https://github.com/cardano-foundation/CIPs/blob/868ae58447c953cc6115b61064af6d5ad30edd87/CIP-0010/registry.json

    """
    tag = 674  #  transaction message/comment metadata
    tx_metadata = OrderedDict()
    tx_metadata["title"] = "Hello Orcfax! 🚀"
    tx_metadata["message"] = "You have successfully consumed a price-feed datum!"
    tx_metadata["note"] = "To inspect please look at the reference inputs for this Tx."
    tx_metadata[f"{feed_values[0][0]}".lower()] = f"{feed_values[0][1]}"
    tx_metadata[f"{feed_values[1][0]}".lower()] = f"{feed_values[1][1]}"
    tx_metadata["timestamp"] = f"{timestamp}"
    return tag, tx_metadata


def claim_script():
    """Claim a small value from a smart contract pending validation.

    A UTxO containing a value must have been placed on-chain. The
    smart contract associated with that value must validate.
    """
    amount: Final[str] = 1  # Pay one ada to ourselves...
    ada_amount: Final[str] = amount * pow(10, 6)
    contract_script = library.get_contract_script()
    script_hash = pyc.plutus_script_hash(contract_script)
    script_address = pyc.Address(script_hash, network=config.network)
    logger.info("script address: %s", script_address)
    logger.info("entering this script... ")
    logger.info("script address: %s", script_address)
    logger.info("oracle smart contract: %s", config.ADA_USD_ORACLE_ADDR)
    logger.info("payment address: %s", library.payment_address)
    oracle_utxo = library.get_latest_utxo(config.ADA_USD_ORACLE_ADDR)
    if not oracle_utxo:
        logger.error("no oracle data found")
        sys.exit(0)
    feed_values, timestamp = decode_oracle_utxo(oracle_utxo)
    tag, tx_metadata = generate_transaction_metadata(feed_values, timestamp)
    sc_utxo, claimable_utxos = get_script_and_claimables(script_address)
    if not sc_utxo:
        logger.error("smart contract UTxO not found!")
        sys.exit(0)
    if not claimable_utxos:
        logger.warning("no utxo to claim!")
        sys.exit(0)
    logger.info("building transaction...")
    transaction = pyc.TransactionBuilder(config.context)
    for item in config.context.utxos(str(library.payment_address)):
        transaction.add_input(item)
    transaction.add_input_address(library.payment_address)
    transaction.add_output(
        pyc.TransactionOutput(library.payment_address, pyc.Value(ada_amount))
    )
    transaction.reference_inputs.add(sc_utxo)
    transaction.reference_inputs.add(oracle_utxo)
    for utxo_to_spend in claimable_utxos:
        transaction.add_script_input(
            utxo_to_spend["utxo"], redeemer=pyc.Redeemer(contract.HelloOrcfaxRedeemer())
        )
        transaction.add_output(
            pyc.TransactionOutput.from_primitive(
                [utxo_to_spend["fee_address"], utxo_to_spend["fee"]]
            )
        )
    # Add collateral to cover the cost of the validating node executing
    # a failing script
    collateral_address = library.payment_address
    collateral_amount: Final[int] = 3607615
    collateral_utxos = config.context.utxos(str(collateral_address))
    collateral_utxo = None
    for collateral in collateral_utxos:
        if int(collateral.output.amount.coin) > collateral_amount:
            collateral_utxo = collateral
            break
    transaction.collaterals.append(collateral_utxo)
    transaction.required_signers = [library.payment_vkey.hash()]
    transaction.validity_start = config.context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600
    tx_metadata = {tag: tx_metadata}
    transaction.auxiliary_data = pyc.AuxiliaryData(
        pyc.AlonzoMetadata(metadata=pyc.Metadata(tx_metadata))
    )
    logger.info("signing the transaction...")
    signed_tx = transaction.build_and_sign(
        [library.payment_skey], change_address=library.payment_address
    )
    logger.info("tx signed")
    logger.info("signed tx id: %s", signed_tx.id)
    library.save_transaction(signed_tx, "tx_claim.signed")
    logger.info("submitting the transaction...")
    library.submit_and_log_tx(signed_tx)
    logger.info("done")


def main():
    """Primary entry point for this script."""
    try:
        claim_script()
    except pyc.PyCardanoException as err:
        logger.error("claim value script failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
