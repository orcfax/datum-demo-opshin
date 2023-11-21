"""Return the public key hash of the payment key.

After running, the minting contract can be built in OpShin using:

    ```sh
       opshin build minting contract.py '{"bytes": "<vkey_hash_value>"}'
    ```
"""

from library import logger, payment_vkey


def return_payment_hash():
    """Return the hash of the payment key."""
    payment_hash = payment_vkey.hash()
    logger.info("payment hash: %s", payment_hash)
    logger.info(
        'build contract with: `opshin build minting contract.py \'{"bytes": "%s"}\'`',
        payment_hash,
    )


def main():
    """Primary entry point for this script."""
    return_payment_hash()


if __name__ == "__main__":
    main()
