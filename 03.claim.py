"""Request to claim the deposited tokens using the smart contract."""

# pylint: disable=R0914, R0915, E0611

import sys

import cbor2
from config import ADA_USD_ORACLE_ADDR, context, network
from contract import HelloWorldRedeemer, PublishParams
from datetime import datetime, timezone
from typing import final
from library import (
    client_address,
    client_skey,
    client_vkey,
    collateral_address,
    collateral_skey,
    collateral_vkey,
    decode_utxo,
    get_contract_script,
    get_latest_utxo,
    logger,
    save_transaction,
    payment_address,
    payment_skey,
    payment_vkey,
    submit_and_log_tx,
)
from pycardano import (
    Address,
    Redeemer,
    TransactionBuilder,
    TransactionFailedException,
    TransactionOutput,
    UTxO,
    VerificationKeyHash,
    plutus_script_hash,
    AuxiliaryData,
    AlonzoMetadata,
    Metadata,
    Value,
)

from collections import OrderedDict


def claim_script():
    """Todo..."""

    # Pay one ada to yourself.
    AMOUNT = 1
    ada_amount = AMOUNT * pow(10, 6)

    # Metadata label registry: https://github.com/cardano-foundation/CIPs/blob/868ae58447c953cc6115b61064af6d5ad30edd87/CIP-0010/registry.json
    hello_world_key = 674
    hello_world_value = ""

    contract_script = get_contract_script()
    script_hash = plutus_script_hash(contract_script)
    script_address = Address(script_hash, network=network)
    logger.info("script address: %s", script_address)

    logger.info("entering this script... ")
    logger.info("oracle smart contract: %s", ADA_USD_ORACLE_ADDR)
    oracle_utxo = get_latest_utxo(ADA_USD_ORACLE_ADDR)

    if not oracle_utxo:
        logger.error("no oracle data found")
        sys.exit(0)

    decoded = decode_utxo(oracle_utxo)
    feed_name = decoded["name"].split("|")
    feed_value = decoded["value"]
    feed_time = decoded["valueReference"][0]["value"]
    feed_values = list(zip(feed_name, feed_value))
    feed_timestamp_human = datetime.utcfromtimestamp(int(feed_time) / 1000).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    hello_world_value = OrderedDict()
    hello_world_value["title"] = "Hello Orcfax! 🚀"
    hello_world_value["message"] = "You have successfully consumed a price-feed datum!"
    hello_world_value[
        "note"
    ] = "To inspect please look at the reference inputs for this Tx."
    hello_world_value[f"{feed_values[0][0]}".lower()] = f"{feed_values[0][1]}"
    hello_world_value[f"{feed_values[1][0]}".lower()] = f"{feed_values[1][1]}"
    hello_world_value["timestamp"] = f"{feed_timestamp_human}"

    script_utxos = context.utxos(str(script_address))
    sc_utxo = None
    claimable_utxos = []

    for item in script_utxos:
        if item.output.script:
            sc_utxo: UTxO = item
        elif item.output.datum:
            datum = cbor2.loads(item.output.datum.cbor)
            # Create a PublishParams object to validate in the smart
            # contract.
            datum_obj = PublishParams(datum.value[0], datum.value[1], datum.value[2])
            fee_address = Address(
                VerificationKeyHash.from_primitive(datum_obj.fee_address),
                network=network,
            )
            claimable_utxos.append(
                {"fee_address": str(fee_address), "fee": datum_obj.fee, "utxo": item}
            )

    if not sc_utxo:
        logger.error("smart contract UTxO not found!")
        sys.exit(0)

    if not claimable_utxos:
        logger.warning("no utxo to claim!")
        sys.exit(0)

    # logger.info("collateral address: %s", collateral_address)
    logger.info("script address: %s", script_address)
    logger.info("client address: %s", client_address)
    logger.info("payment address: %s", payment_address)

    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...

    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...

    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...
    ## BUILD THE TRANSACTION...

    transaction = TransactionBuilder(context)
    for item in context.utxos(str(payment_address)):
        transaction.add_input(item)

    transaction.add_input_address(payment_address)
    transaction.add_output(TransactionOutput(payment_address, Value(ada_amount)))

    transaction.reference_inputs.add(sc_utxo)
    transaction.reference_inputs.add(oracle_utxo)

    for utxo_to_spend in claimable_utxos:
        transaction.add_script_input(
            utxo_to_spend["utxo"], redeemer=Redeemer(HelloWorldRedeemer())
        )
        transaction.add_output(
            TransactionOutput.from_primitive(
                [utxo_to_spend["fee_address"], utxo_to_spend["fee"]]
            )
        )

    # here seems to be the error...
    # transaction.add_script_input(utxo_to_spend, redeemer=Redeemer(HelloWorldRedeemer()))

    # Add collateral to cover the cost of the validating node executing
    # a failing script
    collateral_amount: Final[int] = 3607615
    collateral_utxos = context.utxos(str(payment_address))
    collateral_utxo = None
    for collateral in collateral_utxos:
        if int(collateral.output.amount.coin) > collateral_amount:
            collateral_utxo = collateral
            break

    transaction.collaterals.append(collateral_utxo)
    # transaction.required_signers = [client_vkey.hash(), collateral_vkey.hash()]

    transaction.required_signers = [payment_vkey.hash()]
    transaction.validity_start = context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600

    tx_metadata = {hello_world_key: hello_world_value}
    transaction.auxiliary_data = AuxiliaryData(
        AlonzoMetadata(metadata=Metadata(tx_metadata))
    )

    # SIGN THE TX
    # SIGN THE TX
    # SIGN THE TX

    # SIGN THE TX
    # SIGN THE TX
    # SIGN THE TX

    # SIGN THE TX
    # SIGN THE TX
    # SIGN THE TX

    logger.info("signing the transaction...")
    try:
        # signed_tx = transaction.build_and_sign(
        #    [client_skey, collateral_skey], change_address=client_address
        # )
        signed_tx = transaction.build_and_sign(
            [payment_skey], change_address=payment_address
        )
    except TransactionFailedException as err:
        logger.error("signing tx failed: %s", err)
        sys.exit(1)

    logger.info("tx signed")
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_claim.signed")
    logger.info("submitting the transaction...")

    submit_and_log_tx(signed_tx)

    logger.info("Done.")


def main():
    """Primary entry point for this script."""
    claim_script()


if __name__ == "__main__":
    main()
