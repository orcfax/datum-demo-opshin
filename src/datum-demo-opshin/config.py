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


# auth_addr: Final[str] = Address.from_primitive(
#    "addr_test1vrc7lrdcsz08vxuj4278aeyn4g82salal76l54gr6rw4ync86tfse"
# )

# auth_addr: Final[str] = Address.from_primitive(
#    "addr_test1vre0zcsrhdsef2u4u20sxvjlsq063q0any8zj3j9hpra8nqq5rhwv"
# )


# policy ID for the Auth tokens
AUTH_POLICY: Final[str] = "104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21"
# AUTH_POLICY: Final[str] = "49baf539a84ee88c6bbbf74389fb580b74c6e30b8e62714c6d47eee0"

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

auth_policy_id: Final[str] = "104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21"
# auth_policy_id: Final[str] = "49baf539a84ee88c6bbbf74389fb580b74c6e30b8e62714c6d47eee0"

# Transaction template.
tx_template: Final[dict] = {
    "type": "Witnessed Tx BabbageEra",
    "description": "Ledger Cddl Format",
    "cborHex": "",
}
