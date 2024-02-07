"""Library functions for the smart contract code."""

import json
import logging
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone

import cbor2
import numpy
import requests
from config import (
    ADA_USD_ORACLE_ADDR,
    ADDRESSES_COUNT,
    AUTH_POLICY,
    PLUTUS_CHAIN_INDEX_API,
    context,
    contract_script_file,
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
    UTxO,
)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    level="INFO",
)

logger = logging.getLogger(__name__)


def get_contract_script() -> PlutusV2Script:
    """Read the smart contract bytecode from disk."""
    with open(contract_script_file, "r", encoding="utf-8") as f:
        script_hex = f.read().strip()
    return PlutusV2Script(bytes.fromhex(script_hex))


@dataclass
class PricePair:
    """Stores our values."""

    ada_usd: int
    usd_ada: int


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
    """Generate the wallet from a mnemonic phrase existing in a file on
    disk If the mnemonic file does not exist, generate a new mnemonic
    and save it.

    :param mnemonic_file: The file where the mnemonic is saved
    :param address_count: The number of addresses to generate
    """
    try:
        with open(mnemonic_file, "r", encoding="utf-8") as f:
            mnem = f.read().strip()
    except FileNotFoundError:
        mnem = HDWallet.generate_mnemonic()
        with open(mnemonic_file, "w", encoding="utf-8") as f:
            f.write(mnem)
    hdw = HDWallet.from_mnemonic(mnem)

    # Derive the staking key
    stk = hdw.derive_from_path(stake_derivation_path)
    stk_skey = StakeExtendedSigningKey.from_hdwallet(stk)
    stk_vkey = StakeExtendedVerificationKey.from_signing_key(stk_skey)
    stk_addr = Address(staking_part=stk_vkey.hash(), network=network)

    # Derive the first payment address
    wlts = {}
    for i in range(address_count):
        payment = hdw.derive_from_path(payment_derivation_path[0:-1] + str(i))
        p_skey = ExtendedSigningKey.from_hdwallet(payment)
        p_vkey = PaymentExtendedVerificationKey.from_signing_key(p_skey)
        p_addr = Address(p_vkey.hash(), stk_vkey.hash(), network)
        wlts[i] = {"addr": p_addr, "skey": p_skey, "vkey": p_vkey}
    wlts["stake"] = {"addr": stk_addr, "skey": stk_skey, "vkey": stk_vkey}
    return wlts


def display_utxo(utxo: UTxO):
    """Display the details in a UTxO.

    Example UTxO:

    ```json
        {'input': {
        'index': 0,
        'transaction_id': TransactionId(hex='6812900646a00e1cf994e969bed7dd6556950cafbea23d773cb9d61b278f05cc'),
        }, 'output': {
        'address': addr_test1wrtcecfy7np3sduzn99ffuv8qx2sa8v977l0xql8ca7lgkgmktuc0,
        'amount': {
            'coin': 3413520,
            'multi_asset': {ScriptHash(hex='104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21'): {AssetName(b'\xcc\x02\xc7,\xb3\xef\x8e8\x99Vy\x95\x85\xc0Y\x04S\xf3\xec\xcfpO\xe5\xd7\xdd\xa2\xcbb/\x8b2u'): 1}},
        },
        'datum': RawCBOR(cbor=b'\xd8y\x9f\xa7H@contextRhttps://schema.orgR_:contentSignatureX@d10c6c3167060a8e82f2c1a8bb8b271ec796f3379a2473d522e478aabd1f6a5fJidentifier\xa3JpropertyIDPArkly IdentifierDtypeMPropertyValueEvalueX/urn:orcfax:d72786af-d8fa-4488-8f53-d4578b2f6f23DnameOADA-USD|USD-ADADtypeMPropertyValueEvalue\x9f\xd8|\x9f\x19_\x9b\x1b\xff\xff\xff\xff\xff\xff\xff\xfb\xff\xd8|\x9f\x1b\x00\x0e\x84\x03\xdf6\x89\x8b\x1b\xff\xff\xff\xff\xff\xff\xff\xf1\xff\xffNvalueReference\x9f\xa3E@typeMPropertyValueDnameIvalidFromEvalue\x1b\x00\x00\x01\x8a\xbc-\x9e\x85\xa3E@typeMPropertyValueDnameLvalidThroughEvalue\x1b\x00\x00\x01\x8a\xbcd\x8d\x05\xffX 04CA0001HAY2VBEC6PP7P1DSEA2V2VHY\xd8z\x9f\x1b\x00\x00\x01\x8a\xbcd\x8d\x05\xffX\x1c\x90\xb1!\xaakh\x92\x00\xad\xf7\xed\x11P@\xa9cu\xd2\xb6\x8e#c=hd\xc5:\x91\xff'),
        'datum_hash': None,
        'post_alonzo': False,
        'script': None,
        }}
    ```

    """
    logger.info("(input) transaction id: %s", str(utxo.input.transaction_id))
    logger.info("(output) transaction addr: %s", str(utxo.output.address))
    logger.info(
        "(output) datum cbor:\n\n%s\n", cbor2.dumps(utxo.output.datum.cbor).hex()
    )
    logger.info("(output) Tx cost: %s ADA", utxo.output.amount.coin / 1000000)


def _decode_number(value_pair: list):
    """Decode a number value."""
    significand = numpy.uint64(value_pair[0]).astype(numpy.int64)
    base10_component = numpy.uint64(value_pair[1]).astype(numpy.int64)
    value = significand * 10 ** numpy.float_(base10_component)
    return value


def decode_datum_bytes(json_datum: dict):
    """Decode a datum's key/value pairs from their respective
    encodings.
    """
    decoded = {}
    for key, value in json_datum.items():
        if isinstance(value, list):
            item_list = []
            if key.decode() == "value":
                if len(value) == 2:
                    for value_pair in value:
                        item_list.append(_decode_number(value_pair.value))
                decoded[key.decode()] = item_list
                continue
            for item in value:
                if isinstance(item, cbor2.CBORTag):
                    item_list.append(item.value)
                if isinstance(item, dict):
                    item_list.append(decode_datum_bytes(item))
            decoded[key.decode()] = item_list
            continue
        try:
            decoded[key.decode()] = value.decode()
        except AttributeError:
            if isinstance(value, int):
                decoded[key.decode()] = value
                continue
            decoded[key.decode()] = decode_datum_bytes(value)
    return decoded


def _recombine_datum(json_datum: dict):
    """Recombine the datum in a more familiar order.

    The dictionary order isn't guaranteed to be preserved when placed
    on-chain. We do the necessary gymnastics here to reorder it.
    """
    new_datum = OrderedDict()
    new_datum["@context"] = json_datum["@context"]
    new_datum["type"] = json_datum["type"]
    new_datum["name"] = json_datum["name"]
    new_datum["value"] = json_datum["value"]
    new_datum["valueReference"] = json_datum["valueReference"]
    new_datum["identifier"] = json_datum["identifier"]
    new_datum["_:contentSignature"] = json_datum["_:contentSignature"]
    return new_datum


def decode_utxo(utxo: UTxO):
    """Split a UTxO into the components that we need to process and
    initially return the Orcfax Datum."""
    oracle_datum = cbor2.loads(utxo.output.datum.cbor)
    json_datum = oracle_datum.value[0]
    json_datum = decode_datum_bytes(json_datum)
    json_datum = _recombine_datum(json_datum)
    logger.info("\n\n%s\n", json.dumps(json_datum, indent=2))
    logger.info("oracle datum identifier (internal): %s", oracle_datum.value[1])
    timestamp = oracle_datum.value[2].value[0]
    timestamp_human = datetime.utcfromtimestamp(int(timestamp) / 1000).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    logger.info("oracle datum timestamp: %s (%s)", timestamp_human, timestamp)
    labels = oracle_datum.value[0][b"name"].decode().split("|", 1)
    ada_usd_value = oracle_datum.value[0][b"value"][0].value
    usd_ada_value = oracle_datum.value[0][b"value"][1].value
    price_pair = PricePair(ada_usd=ada_usd_value, usd_ada=usd_ada_value)
    pretty_log_value(ada_usd_value, labels[0])
    pretty_log_value(usd_ada_value, labels[1])
    return json_datum


def pretty_log_value(value_pair: cbor2.CBORTag, label: str):
    """Return pretty logging information about a value pair."""
    value = _decode_number(value_pair)
    logger.info("%s: %s", label, value)


def validate_utxo(utxo: UTxO) -> bool:
    """check if the token included in the utxo is the correct one."""
    for item in utxo.output.amount.multi_asset:
        if str(item) == AUTH_POLICY:
            return True
    return False


def get_latest_utxo(oracle_addr: str):
    """return the latest Orcfax UTxO from those found on-chain."""
    oracle_utxos = context.utxos(oracle_addr)
    logger.info("inspecting '%s' UTxOs", len(oracle_utxos))
    latest_timestamp = 0
    latest_utxo = None
    latest_utxos = []
    for utxo in oracle_utxos:
        if utxo.output.script or not utxo.output.datum:
            continue
        if not validate_utxo(utxo):
            continue
        latest_utxos.append(utxo)
    for utxo in latest_utxos:
        oracle_datum = cbor2.loads(utxo.output.datum.cbor)
        try:
            timestamp = oracle_datum.value[2].value[0]
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_utxo = utxo
        except IndexError:
            pass
    return latest_utxo


def read_datum():
    """Return savings to an account when a profit has been made."""
    logger.info("entering this script... ")
    logger.info("oracle smart contract: %s", ADA_USD_ORACLE_ADDR)
    latest_utxo = get_latest_utxo(ADA_USD_ORACLE_ADDR)
    if not latest_utxo:
        logger.info("no oracle data found")
        sys.exit(0)
    display_utxo(latest_utxo)
    decode_utxo(latest_utxo)


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
