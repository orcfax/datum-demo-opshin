"""Create a mnemonic phrase for deriving a Cardano wallet."""

import os
import sys
from typing import Final

import pycardano

stake_derivation_path: Final[str] = "m/1852'/1815'/0'/2/0"
payment_derivation_path: Final[str] = "m/1852'/1815'/0'/0/0"


def output_addresses(wallets: dict) -> None:
    """Return the addresses from the wallet info."""

    # NB. The configuration for these wallets needs to be centralized
    # as the order changing in the DApp scripts will cause problems
    # here.

    payment_address: pycardano.Address = wallets[0]["addr"]
    collateral_address: pycardano.Address = wallets[1]["addr"]
    client_address: pycardano.Address = wallets[2]["addr"]
    exchange_client_address: pycardano.Address = wallets[3]["addr"]

    print(f"payment addr (requires 75 ADA): '{payment_address}'")
    print(f"collateral addr (requires 5 ADA): '{collateral_address}'")
    print(f"client addr (requires 10 ADA): '{client_address}'")
    print(f"exchange client addr: '{exchange_client_address}'")
    print("")


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
    for i in range(4):
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
    path: Final[str] = os.path.join(".wallet", "phrase.prv")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            mnemonic = f.read()
        return mnemonic
    mnemonic = pycardano.HDWallet.generate_mnemonic()
    print(f"mnemonic is:\n\n{mnemonic}\n", file=sys.stdout)
    print(f"writing to: {path}", file=sys.stderr)
    with open(path, "w", encoding="utf-8") as f:
        f.write(mnemonic)
    return mnemonic


def main() -> None:
    """Primary entry point for this script."""
    mnemonic = generate_mnemonic()
    print(f"mnemonic is:\n\n{mnemonic}\n", file=sys.stdout)
    wallet_info = derive_wallet_info(mnemonic)
    output_addresses(wallet_info)


if __name__ == "__main__":
    main()
