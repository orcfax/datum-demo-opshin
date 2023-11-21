"""Request to claim the deposited tokens using the smart contract."""

# pylint: disable=R0914, R0915, E0611

import sys

import cbor2
from config import ADA_USD_ORACLE_ADDR, context, network
from contract import ExchangeRedeemer, PublishParams
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
)


def claim_script():
    """Todo..."""
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
    decode_utxo(oracle_utxo)

    oracle_datum = cbor2.loads(oracle_utxo.output.datum.cbor)
    # logger.info("----------------------------------------------------------------")
    # datum_info = decode_datum_bytes(oracle_datum.value[0])
    # logger.info(json.dumps(datum_info, indent=2))
    # logger.info("----------------------------------------------------------------")

    # logger.info("----------------------------------------------------------------")
    # logger.info(oracle_datum)
    logger.info("----------------------------------------------------------------")
    logger.info(oracle_datum.value[0])
    logger.info("----------------------------------------------------------------")
    logger.info(oracle_datum.value[1])
    logger.info("----------------------------------------------------------------")
    logger.info(oracle_datum.value[2])
    logger.info("----------------------------------------------------------------")
    logger.info(oracle_datum.value[3])  # the publisher PKH
    logger.info("----------------------------------------------------------------")

    if not oracle_datum:
        logger.error("oracle datum UTxO not found!")
        sys.exit(0)

    script_utxos = context.utxos(str(script_address))
    sc_utxo = None
    claimable_utxos = []

    for item in script_utxos:
        if item.output.script:
            sc_utxo: UTxO = item
        elif item.output.datum:
            datum = cbor2.loads(item.output.datum.cbor)
            # Create PublishParams object.
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

    collateral_utxo = context.utxos(str(collateral_address))[0]

    logger.info("Creating the transaction...")
    transaction = TransactionBuilder(context)
    for item in context.utxos(str(client_address)):
        transaction.add_input(item)
    transaction.reference_inputs.add(sc_utxo)
    transaction.reference_inputs.add(oracle_utxo)
    for utxo_to_spend in claimable_utxos:
        transaction.add_script_input(
            utxo_to_spend["utxo"], redeemer=Redeemer(ExchangeRedeemer())
        )
        transaction.add_output(
            TransactionOutput.from_primitive(
                [utxo_to_spend["fee_address"], utxo_to_spend["fee"]]
            )
        )

    transaction.collaterals.append(collateral_utxo)
    transaction.required_signers = [client_vkey.hash(), collateral_vkey.hash()]
    transaction.validity_start = context.last_block_slot
    transaction.ttl = transaction.validity_start + 3600
    logger.info("Signing the transaction...")
    try:
        signed_tx = transaction.build_and_sign(
            [client_skey, collateral_skey], change_address=client_address
        )
    except TransactionFailedException as err:
        logger.error("signing tx failed: %s", err)
        sys.exit(1)
    logger.info("tx signed")
    logger.info(signed_tx.id)
    save_transaction(signed_tx, "tx_claim.signed")
    logger.info("Submitting the transaction...")
    # submit_and_log_tx(signed_tx.to_cbor())
    logger.info("Done.")


def main():
    """Primary entry point for this script."""
    claim_script()


if __name__ == "__main__":
    main()
