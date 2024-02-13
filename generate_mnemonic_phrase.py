"""Create a mnemonic phrase for deriving a Cardano wallet."""

import logging
import sys
from pathlib import Path
from typing import Final

import pycardano

logger = logging.getLogger(__name__)

stake_derivation_path: Final[str] = "m/1852'/1815'/0'/2/0"
payment_derivation_path: Final[str] = "m/1852'/1815'/0'/0/0"

hello_orcfax: Final[
    str
] = """
      ::::::::  :::::::::   ::::::::  ::::::::::   :::     :::    :::          :::::::::  ::::::::::   :::   :::    ::::::::
    :+:    :+: :+:    :+: :+:    :+: :+:        :+: :+:   :+:    :+:          :+:    :+: :+:         :+:+: :+:+:  :+:    :+:
   +:+    +:+ +:+    +:+ +:+        +:+       +:+   +:+   +:+  +:+           +:+    +:+ +:+        +:+ +:+:+ +:+ +:+    +:+
  +#+    +:+ +#++:++#:  +#+        :#::+::# +#++:++#++:   +#++:+            +#+    +:+ +#++:++#   +#+  +:+  +#+ +#+    +:+
 +#+    +#+ +#+    +#+ +#+        +#+      +#+     +#+  +#+  +#+           +#+    +#+ +#+        +#+       +#+ +#+    +#+
#+#    #+# #+#    #+# #+#    #+# #+#      #+#     #+# #+#    #+#          #+#    #+# #+#        #+#       #+# #+#    #+#
########  ###    ###  ########  ###      ###     ### ###    ###          #########  ########## ###       ###  ########

"""


def output_addresses(wallets: dict) -> None:
    """Return the addresses from the wallet info."""

    # NB. The configuration for these wallets needs to be centralized
    # as the order changing in the DApp scripts will cause problems
    # here.

    payment_address: pycardano.Address = wallets[0]["addr"]
    # collateral_address: pycardano.Address = wallets[1]["addr"]
    # client_address: pycardano.Address = wallets[2]["addr"]
    # exchange_client_address: pycardano.Address = wallets[3]["addr"]

    preprod_faucet: Final[
        str
    ] = "addr_test1qqr585tvlc7ylnqvz8pyqwauzrdu0mxag3m7q56grgmgu7sxu2hyfhlkwuxupa9d5085"
    print(
        f"please fund the payment addr (requires ⩾ 75 ADA): '{payment_address}'",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print(
        f"NB. when you have finished with your ADA, consider returning it to the preprod faucet: {preprod_faucet}",
        file=sys.stderr,
    )
    print("", file=sys.stderr)


def derive_wallet_info(mnemonic: str) -> dict:
    """Derive the wallet info from the mnemonic."""
    hdw = pycardano.HDWallet.from_mnemonic(mnemonic)
    stk = hdw.derive_from_path(stake_derivation_path)
    stk_skey = pycardano.StakeExtendedSigningKey.from_hdwallet(stk)
    stk_vkey = pycardano.StakeExtendedVerificationKey.from_signing_key(stk_skey)
    stk_addr = pycardano.Address(
        staking_part=stk_vkey.hash(), network=pycardano.Network.TESTNET
    )
    wallets = {}
    for i in range(1):
        payment = hdw.derive_from_path(payment_derivation_path[0:-1] + str(i))
        p_skey = pycardano.ExtendedSigningKey.from_hdwallet(payment)
        p_vkey = pycardano.PaymentExtendedVerificationKey.from_signing_key(p_skey)
        p_addr = pycardano.Address(
            p_vkey.hash(), stk_vkey.hash(), pycardano.Network.TESTNET
        )
        wallets[i] = {"addr": p_addr, "skey": p_skey, "vkey": p_vkey}
    wallets["stake"] = {"addr": stk_addr, "skey": stk_skey, "vkey": stk_vkey}
    return wallets


def generate_mnemonic() -> None:
    """Generate a mnemonic to be saved in a phrase file."""
    print("Welcome to the:", file=sys.stderr)
    print(hello_orcfax, file=sys.stderr)
    wallet_dir = Path(".wallet")
    wallet_dir.mkdir(exist_ok=True)
    wallet = wallet_dir / Path("phrase.prv")
    if wallet.exists():
        with wallet.open(encoding="utf-8") as wallet_file:
            mnemonic = wallet_file.read()
        return mnemonic
    mnemonic = pycardano.HDWallet.generate_mnemonic()
    print(f"creating mnemonic and writing to: {wallet}\n", file=sys.stderr)
    with wallet.open("w", encoding="utf-8") as wallet_file:
        wallet_file.write(mnemonic)
    return mnemonic


def main() -> None:
    """Primary entry point for this script."""
    mnemonic = generate_mnemonic()
    print("your mnemonic is:\n", file=sys.stderr)
    print(f"-{'-'*len(mnemonic)}", file=sys.stderr)
    print(mnemonic, file=sys.stdout)
    print(f"-{'-'*len(mnemonic)}", file=sys.stderr)
    print("", file=sys.stderr)
    wallet_info = derive_wallet_info(mnemonic)
    output_addresses(wallet_info)


if __name__ == "__main__":
    main()
