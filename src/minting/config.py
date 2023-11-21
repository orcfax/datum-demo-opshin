"""Script configuration."""

from os import getcwd
from typing import Final

from pycardano import Network, OgmiosChainContext

OGMIOS_URL: Final[str] = "ws://ogmios.preprod.orcfax.io:1337"
network = Network.TESTNET
context = OgmiosChainContext(ws_url=OGMIOS_URL, network=network)
contract_cbor: Final[str] = "build/contract/script.cbor"
policy_id_file: Final[str] = "build/contract/script.policy_id"

stake_derivation_path: Final[str] = "m/1852'/1815'/0'/2/0"
payment_derivation_path: Final[str] = "m/1852'/1815'/0'/0/0"
workdir = getcwd()
base_path = workdir[0 : workdir.find("/src")]
transactions_path = base_path + "/.transactions"
wallet_path = base_path + "/.wallet"
mnemonic_file_name = wallet_path + "/phrase.prv"
ADDRESSES_COUNT: Final[int] = 4
LOVELACE_AMOUNT: Final[int] = 2000000
AMOUNT: Final[int] = 1000000000
DECIMALS: Final[int] = 6
TOKEN_NAME: Final[bytes] = "SuperDexToken".encode().hex()

mint_amount: Final[int] = AMOUNT * pow(10, DECIMALS)

tx_template: Final[dict] = {
    "type": "Witnessed Tx BabbageEra",
    "description": "Ledger Cddl Format",
    "cborHex": "",
}
