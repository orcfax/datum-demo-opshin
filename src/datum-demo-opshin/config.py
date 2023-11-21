"""Configuration for the smart contract consuming the Orcfax datum."""

from os import getcwd
from typing import Final

from pycardano import Address, Network, OgmiosChainContext

# Preprod
#
OGMIOS_URL: Final[str] = "ws://ogmios.preprod.orcfax.io:1337"
network = Network.TESTNET

# plutus chain index api
PLUTUS_CHAIN_INDEX_API: Final[
    str
] = "http://plutus-chain-index.preprod.orcfax.io:9084/tx"

# smart contract
ADA_USD_ORACLE_ADDR: Final[
    str
] = "addr_test1wrtcecfy7np3sduzn99ffuv8qx2sa8v977l0xql8ca7lgkgmktuc0"

auth_addr: Final[str] = Address.from_primitive(
    "addr_test1vrc7lrdcsz08vxuj4278aeyn4g82salal76l54gr6rw4ync86tfse"
)

# policy ID for the Auth tokens
AUTH_POLICY: Final[str] = "5ec8416ecd8af5fe338068b2aee00a028dc1f4c0cd5978fb86d7c038"

context: Final[str] = OgmiosChainContext(ws_url=OGMIOS_URL, network=network)

contract_script_file: Final[str] = "build/contract/script.cbor"
policy_id_file: Final[str] = "build/contract/script.policy_id"

stake_derivation_path: Final[str] = "m/1852'/1815'/0'/2/0"
payment_derivation_path: Final[str] = "m/1852'/1815'/0'/0/0"
workdir = getcwd()
base_path = workdir[0 : workdir.find("/src")]
transactions_path = base_path + "/.transactions"
wallet_path = base_path + "/.wallet"
mnemonic_file_name = wallet_path + "/phrase.prv"
ADDRESSES_COUNT: Final[int] = 4
LOVELACE_AMOUNT: Final[int] = 10000000

auth_policy_id: Final[str] = "5ec8416ecd8af5fe338068b2aee00a028dc1f4c0cd5978fb86d7c038"

# the token we mint for testing this
TOKENS_AMOUNT: Final[int] = 1000000000
DECIMALS: Final[int] = 6

# Policy ID found in: minting/build/contract/script.policy_id
POLICY_ID: Final[str] = "b578c124b775356e513470027bba2b0a294275024afe82f848973952"

TOKEN_NAME: Final[str] = "SuperDexToken".encode().hex()
tokens_amount: Final[str] = TOKENS_AMOUNT * pow(10, DECIMALS)

# Transaction template.
tx_template: Final[dict] = {
    "type": "Witnessed Tx BabbageEra",
    "description": "Ledger Cddl Format",
    "cborHex": "",
}
