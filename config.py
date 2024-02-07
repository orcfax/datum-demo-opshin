"""Configuration for the smart contract consuming the Orcfax datum."""

from os import getcwd
from typing import Final


from pycardano import Address, Network, OgmiosChainContext

# Preprod
#
OGMIOS_URL: Final[str] = "ws://ogmios.preprod.orcfax.io:1337"
network = Network.TESTNET

# smart contract
ADA_USD_ORACLE_ADDR: Final[
    str
] = "addr_test1wrtcecfy7np3sduzn99ffuv8qx2sa8v977l0xql8ca7lgkgmktuc0"

# policy ID for the Auth tokens
AUTH_POLICY: Final[str] = "104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21"

context: Final[str] = OgmiosChainContext(ws_url=OGMIOS_URL, network=network)

contract_script_file: Final[str] = "build/contract/script.cbor"
policy_id_file: Final[str] = "build/contract/script.policy_id"

stake_derivation_path: Final[str] = "m/1852'/1815'/0'/2/0"
payment_derivation_path: Final[str] = "m/1852'/1815'/0'/0/0"
base_path = getcwd()
transactions_path = base_path + "/.transactions"
wallet_path = base_path + "/.wallet"
mnemonic_file_name = wallet_path + "/phrase.prv"
ADDRESSES_COUNT: Final[int] = 1
LOVELACE_AMOUNT: Final[int] = 10000000

# Transaction template.
tx_template: Final[dict] = {
    "type": "Witnessed Tx BabbageEra",
    "description": "Ledger Cddl Format",
    "cborHex": "",
}
