"""Generic functions library."""

# pylint: disable=R0914

import json
import logging

from config import (
    ADDRESSES_COUNT,
    context,
    contract_cbor,
    mnemonic_file_name,
    network,
    payment_derivation_path,
    policy_id_file,
    stake_derivation_path,
    tx_template,
)
from pycardano import (
    Address,
    ExtendedSigningKey,
    HDWallet,
    PaymentExtendedSigningKey,
    PaymentExtendedVerificationKey,
    PlutusV2Script,
    StakeExtendedSigningKey,
    StakeExtendedVerificationKey,
    Transaction,
)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    level="INFO",
)

logger = logging.getLogger(__name__)


def get_contract_script() -> PlutusV2Script:
    """Retrieve the contract script."""
    with open(contract_cbor, "r", encoding="utf-8") as f:
        script_hex = f.read()
    return PlutusV2Script(bytes.fromhex(script_hex))


def get_policy_id() -> str:
    """Retrieve the policy ID."""
    policy_id = None
    with open(policy_id_file, "r", encoding="utf-8") as f:
        policy_id = f.read()
    return policy_id


def save_transaction(trans: Transaction, file: str):
    """Save transaction helper function saves a Tx object to file."""
    logger.info(
        "saving Tx to: %s , inspect with: 'cardano-cli transaction view --tx-file %s'",
        file,
        file,
    )
    tx = tx_template.copy()
    tx["cborHex"] = trans.to_cbor().hex()
    with open(file, "w", encoding="utf-8") as tf:
        tf.write(json.dumps(tx, indent=4))


def cexplorer_url(addr: str) -> str:
    """Return a cexplorer URL to the caller."""
    return f"https://preprod.cexplorer.io/address/{addr}"


def cexplorer_tx_url(tx_id: str) -> str:
    """Return a transaction UL to the caller."""
    return f"https://preprod.cexplorer.io/tx/{tx_id}"


def submit_and_log_tx(signed_tx: Transaction):
    """Submit and log a signed transaction.

    E.g. provide information form the Tx that is generic to all.
    """
    context.submit_tx(signed_tx.to_cbor())
    logger.info(
        "fee %s ADA",
        int(signed_tx.transaction_body.fee) / 1000000,
    )
    logger.info(
        "output %s ADA",
        int(signed_tx.transaction_body.outputs[0].amount.coin) / 1000000,
    )
    logger.info("transaction submitted: %s", cexplorer_tx_url(signed_tx.id))


def wallet_from_mnemonic(mnemonic_file: str, address_count: int) -> dict:
    """Generate the wallet from a mnemonic phrase existing in a file on disk
    If the mnemonic file does not exist, generate a new mnemonic and save it.

    :param mnemonic_file: The file where the mnemonic is saved
    :param address_count: The number of addresses to generate
    """
    logging.info("in wallet from mnemonic")
    try:
        with open(mnemonic_file, "r", encoding="utf-8") as f:
            mnem = f.read().strip()
    except FileNotFoundError as err:
        logger.info("creating new mnemonic phrase: %s", err)
        logger.info("mnemonic file: %s", mnemonic_file)
        mnem = HDWallet.generate_mnemonic()
        logger.info("mnemonic phrase: %s", mnem)
        with open(mnemonic_file, "w", encoding="utf-8") as f:
            f.write(mnem)
    hdw = HDWallet.from_mnemonic(mnem)

    # Derive the staking key.
    stk = hdw.derive_from_path(stake_derivation_path)
    stk_skey = StakeExtendedSigningKey.from_hdwallet(stk)
    stk_vkey = StakeExtendedVerificationKey.from_signing_key(stk_skey)
    stk_addr = Address(staking_part=stk_vkey.hash(), network=network)

    # Derive the first payment address.
    wlts = {}
    for i in range(address_count):
        payment = hdw.derive_from_path(payment_derivation_path[0:-1] + str(i))
        p_skey = ExtendedSigningKey.from_hdwallet(payment)
        p_vkey = PaymentExtendedVerificationKey.from_signing_key(p_skey)
        p_addr = Address(p_vkey.hash(), stk_vkey.hash(), network)
        wlts[i] = {"addr": p_addr, "skey": p_skey, "vkey": p_vkey}
    wlts["stake"] = {"addr": stk_addr, "skey": stk_skey, "vkey": stk_vkey}
    return wlts


wallets = wallet_from_mnemonic(mnemonic_file_name, ADDRESSES_COUNT)

payment_address: Address = wallets[0]["addr"]
payment_skey: PaymentExtendedSigningKey = wallets[0]["skey"]
payment_vkey: PaymentExtendedVerificationKey = wallets[0]["vkey"]

collateral_address: Address = wallets[1]["addr"]
collateral_skey: PaymentExtendedSigningKey = wallets[1]["skey"]
collateral_vkey: PaymentExtendedVerificationKey = wallets[1]["vkey"]

client_address: Address = wallets[2]["addr"]
client_skey: PaymentExtendedSigningKey = wallets[2]["skey"]
client_vkey: PaymentExtendedVerificationKey = wallets[2]["vkey"]

exchange_client_address: Address = wallets[3]["addr"]
exchange_client_skey: PaymentExtendedSigningKey = wallets[3]["skey"]
exchange_client_vkey: PaymentExtendedVerificationKey = wallets[3]["vkey"]
