"""Burn previously minted tokens using the same policy information."""

# pylint: disable=E0611

import sys

from config import TOKEN_NAME, context, mint_amount
from library import (
    client_address,
    client_skey,
    client_vkey,
    collateral_address,
    collateral_skey,
    collateral_vkey,
    get_contract_script,
    get_policy_id,
    logger,
    save_transaction,
    submit_and_log_tx,
)
from pycardano import InvalidDataException, MultiAsset, Redeemer, TransactionBuilder


def burn_script():
    """Burn previously created tokens."""

    logger.info("collateral address: %s", collateral_address)
    logger.info("client address: %s", client_address)

    collateral_utxo = context.utxos(collateral_address)

    if not collateral_utxo:
        logger.error("no collateral utxo for this minting policy")
        sys.exit(1)

    # NB. this is a placeholder until we can find a way of returning
    # the change to the collateral holder correctly as this one UTxO
    # needs to be big enough on its own.
    collateral_utxo = collateral_utxo[0]

    utxos_to_consume = []
    input_utxos = context.utxos(client_address)
    for input_utxo in input_utxos:
        if input_utxo.output.amount.multi_asset:
            tokens = input_utxo.output.amount.multi_asset.data
            for _, v in tokens.items():
                for vk, vv in v.items():
                    if str(vk) == TOKEN_NAME and vv >= 1:
                        utxos_to_consume.append(input_utxo)

    builder = TransactionBuilder(context)
    for utxo in utxos_to_consume:
        builder.add_input(utxo)
    builder.add_input_address(client_address)
    contract_script = get_contract_script()
    builder.add_minting_script(script=contract_script, redeemer=Redeemer(0))
    builder.collaterals.append(collateral_utxo)
    policy_id = get_policy_id()
    builder.mint = MultiAsset.from_primitive(
        {bytes.fromhex(policy_id): {TOKEN_NAME: -1 * mint_amount}}
    )
    builder.required_signers = [client_vkey.hash(), collateral_vkey.hash()]
    try:
        signed_tx = builder.build_and_sign(
            [client_skey, collateral_skey], change_address=client_address
        )
    except InvalidDataException as err:
        logger.error("ensure there are tokens to burn: %s", err)
        sys.exit(1)
    save_transaction(signed_tx, "tx_burn.signed")
    submit_and_log_tx(signed_tx)


def main():
    """Primary entry point for this script."""
    burn_script()


if __name__ == "__main__":
    main()
