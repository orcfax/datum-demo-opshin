"""Token minting script."""

import os
import sys

from config import mint_amount  # pylint: disable=E0611
from config import LOVELACE_AMOUNT, TOKEN_NAME, context
from library import get_policy_id  # pylint: disable=E0611
from library import (
    client_address,
    collateral_address,
    collateral_skey,
    collateral_vkey,
    get_contract_script,
    logger,
    payment_address,
    payment_skey,
    payment_vkey,
    save_transaction,
    submit_and_log_tx,
)
from pycardano import MultiAsset, Redeemer, TransactionBuilder, TransactionOutput, Value


def output_policy_id():
    """Output the policy ID to the caller."""

    path = os.path.join("build", "contract", "script.policy_id")
    policy_id = None
    conf_file = os.path.join("..", "opshin-datum-demo", "config.py")
    if not os.path.exists(path):
        logger.error(
            "cannot find '%s', ensure it exists in the minting folder and add its contents to the datum-demo-opshin config file '%s' as 'POLICY_ID'",
            path,
            conf_file,
        )
        return
    with open(path, "r", encoding="utf-8") as f:
        policy_id = f.read()
    logger.info(
        "policy id: '%s', please ensure it matches `POLICY_ID` in `%s`",
        policy_id,
        conf_file,
    )


def mint_script():
    """Mint the configured tokens."""

    logger.info("collateral address: %s", collateral_address)
    logger.info("payment address: %s", payment_address)

    collateral_utxo = context.utxos(collateral_address)

    if not collateral_utxo:
        logger.error("no collateral utxo for this minting policy")
        sys.exit(1)

    # NB. this is a placeholder until we can find a way of returning
    # the change to the collateral holder correctly as this one UTxO
    # needs to be big enough on its own.
    collateral_utxo = collateral_utxo[0]

    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    contract_script = get_contract_script()
    builder.add_minting_script(script=contract_script, redeemer=Redeemer(0))
    builder.collaterals.append(collateral_utxo)
    policy_id = get_policy_id()
    builder.mint = MultiAsset.from_primitive(
        {bytes.fromhex(policy_id): {TOKEN_NAME: mint_amount}}
    )
    logger.info(
        "minting '%s' tokens into the client '%s' address", TOKEN_NAME, client_address
    )
    builder.add_output(
        TransactionOutput(
            client_address,
            Value.from_primitive(
                [LOVELACE_AMOUNT, {bytes.fromhex(policy_id): {TOKEN_NAME: mint_amount}}]
            ),
        )
    )

    builder.required_signers = [payment_vkey.hash(), collateral_vkey.hash()]
    signed_tx = builder.build_and_sign(
        [payment_skey, collateral_skey], change_address=payment_address
    )
    save_transaction(signed_tx, "tx_mint.signed")
    submit_and_log_tx(signed_tx)

    # And finally
    output_policy_id()


def main():
    """Primary entry point for this script."""
    mint_script()


if __name__ == "__main__":
    main()
