# Using the Orcfax ADA-USD price feed Datum with Opshin and PyCardano

For further information see:

* [OpShin][links-1].
* [PyCardano][links-2].

[links-1]: https://github.com/OpShin/opshin
[links-2]: https://pycardano.readthedocs.io/en/latest/tutorial.html

## Script background

The latest published datum must be identified off-chain, then the transaction
must be created and submitted to a node.

The smart contract must check the following:

* the datum was published by the real Oracle (this is true when the UTxO
contains a token created with the correct minting policy).
* the datum is still inside the validity period.
* other checks specific to the DApp using the datum.

### Script status

The current script attempts to show a smart contract workflow using Orcfax data
but serves primarily to demonstrate how to decode the structure of an Orcfax
datum and verify some of its details using a OpShin smart-contract.

In this first iteration, instead of completing the transaction, the smart
contract will "fail" outputting to the user the contents as parsed from
on-chain. This information can be reworked by others to serve their own smart
contract needs.

The contract and data structure potentially of most interest to users is under:
`src/datum-demo-opshin/contract.py`.

## The minting contract in this example

This smart contract (the files are in `src/minting`) is a simple minting
contract with the purpose of minting the tokens used by the example DApp.

Minting tokens with this smart contract will be possible using a dedicated
signing key for this purpose.

### The DApp contract example using the Datum

This smart contract is used to exchange tokens for ADA at a price published by
the Oracle, and a fee will be paid for this to a payment address whose hash is
published in the DApp UTxO Datum. The scripts are in the `src/datum-demo-opshin`
subfolder.

## The wallets

For each of the smart contracts, a different payment address is used.

All the payment addresses are obtained by starting from the same seed phrase,
using different derivation paths.

Seed phrase example:

<!-- markdownlint-disable -->

```text
penalty style orient dinner fabric gift genuine problem over february hybrid material pottery ensure pond annual icon pole dish decide embody able connect four
```

<!-- markdownlint-enable -->

With the virtual environment (venv) setup (below) you can create a phrase with
the following script call:

```sh
python generate_mnemonic_phrase.py
```

> Note: If the script has already been run once and a Bip32 pass phrase file
> exists the command will output the phrase and the associated wallet addresses
> without overwriting anything. This can be helpful to remind yourself of the
> addresses that you're working with. (do not run the script in public on
> mainnet!)

### Funding wallets

A preprod wallet will need to be created and funded.

#### Wallet creation

Look at [eternl.io][eternl-1] for wallet creation.

[eternl-1]: https://eternl.io/app/preprod/

#### Wallet funding

Once you have a preprod wallet, it can be funded from the Cardano
[Faucet][faucet-1]. Directions on how to use this service can be found on the
faucet website.

[faucet-1]: https://docs.cardano.org/cardano-testnet/tools/faucet/

The funded wallet can then be used to fund the wallets used during the remainder
of this demo.

#### Funding amounts

The script `generate_mnemonic_phrase.py` will output addresses with feedback
as follows:

```text
payment addr (requires 75 ADA): 'addr_test1qrc...e3'
collateral addr (requires 5 ADA): 'addr_test1qr6...h6'
client addr (requires 10 ADA): 'addr_test1qq6...qn'
exchange client addr: 'addr_test1qp7...wz'
```

We can see the wallets need to be funded as follows:

* Payment wallet: 75 ADA, 1 UTxO.
* Collateral wallet: 5 ADA, 1 UTxO.
* Client wallet: 10 ADA, 1 UTxO.

## Installing and using the contracts

All the contracts are in distinct folders, arranged by the order in which they
will be used. The configuration for each smart contract is in the `config.py`
file, and the `library.py` contains a few functions and assigns a few variables
that are used by the other scripts.

To complete the steps, preferably install a new venv with the required packages.

```shell
python3 -m venv venv
```

Activate the virtual environment:

```shell
source venv/bin/activate
```

> NB. from hereon out `python` can be called as an alias for `python3` although
> will work just fine.

Install the required modules:

```shell
python -m pip install --upgrade pip
python -m pip install -r requirements/local.txt
```

### Tokens minting contract

Before building the contract, we need to know the public key hash of the
payment key used by the Oracle master node.

It can be displayed by running the `key_hash.py` script from the `src/minting`
folder:

```bash
python key_hash.py
```

The result is (depending on the wallet seed phrase used):

```text
2023-10-22T12:50:33Z INFO :: key_hash.py:4:<module>() :: b1ef135fb7f3b8ddff50d69f9ecd659a2f9fb86b973f8ec60ebee479
```

Given the above output the contract would then be built using the following
command:

```shell
opshin build minting contract.py '{"bytes": "b1ef135fb7f3b8ddff50d69f9ecd659a2f9fb86b973f8ec60ebee479"}'
```

The build files will be found in the `build/contract` subfolder.

Now the contract can be used to mint the tokens by running:

```shell
python mint.py
```

The token name (`SuperDexToken`) is set in `config.py`.

The amount of tokens to be minted is set to 1 Billion with 6 decimals in
`config.py`, and the tokens will be minted into the `client_address` payment
address from `library.py` (the address is also displayed when running the
script).

If you didn't retrieve the minting policy and update the smart contract config
at minting, use `make get-minting-policy` to retrieve the minting policy ID.
It will need to be added to `datum-demo-opshin/config.py` replacing the current
`POLICY_ID`.

To run the script:

```sh
make get-minting-policy
```

#### Cleaning up - reclaiming the tokens

To burn the tokens and claim back the stored value run the script `burn.py`.
See "Resetting oracle DApp" [below](#resetting-dapp-state).

### The Example DApp contract using the Datum

The DApp contract can be built by running:

```shell
opshin build spending contract.py
```

The contract can be deployed on-chain as a Script Output and referenced when
being used. This is done by running the `01.deploy.py` script:

```shell
python 01.deploy.py
```

The script output looks like this:

```text
2023-10-22T12:18:53Z INFO :: 01.deploy.py:14:main() :: Script deployer address: addr_test1qzc77y6lklem3h0l2rtfl8kdvkdzl8acdwtnlrkxp6lwg7fcrzagkyjjgk4pr8yefs3klu8q3xlfhyhhgphefqvfgv4q6casrv
2023-10-22T12:18:53Z INFO :: 01.deploy.py:15:main() :: Script address: addr_test1wpst9j7l3qu99gfwzwlvqd6c3ujj8c087k8a62tqnfy7wls89sexm
2023-10-22T12:18:53Z INFO :: 01.deploy.py:16:main() :: Fee address PKH: b1ef135fb7f3b8ddff50d69f9ecd659a2f9fb86b973f8ec60ebee479
2023-10-22T12:18:53Z INFO :: 01.deploy.py:27:main() :: Creating the transaction...
2023-10-22T12:18:53Z INFO :: 01.deploy.py:31:main() :: Signing the transaction...
2023-10-22T12:18:55Z INFO :: 01.deploy.py:33:main() :: 71eed288aa29df2653c6b93678d529e1b008f6d63a577e4a080824621f2547ea
2023-10-22T12:18:55Z INFO :: 01.deploy.py:35:main() :: Submitting the transaction...
2023-10-22T12:18:56Z INFO :: 01.deploy.py:37:main() :: Done.
```

From the wallets that we have already funded, the contract owner or user
(the `client`) needs to deposit an amount of ADA (and tokens) to the contract
address. This will set the following parameters in the datum:

* who is the `owner` of the funds (who can claim them)
* what fee and to which address should be paid when claiming the funds

The funds can be deposited by running the `02.deposit.py` script:

```shell
python 02.deposit.py
```

The script will output some logging that may be useful in debugging if at all
necessary, e.g. the publisher address can be queried to ensure that it is funded
correctly, and the smart contract address to ensure that it is on-chain.

```text
2023-10-22T12:18:59Z INFO :: 02.deposit.py:8:main() :: Publisher address:    addr_test1qqw9456ez30pua6jqr8l8r86y2ygrqqyg2q73uxe3dyj3upcrzagkyjjgk4pr8yefs3klu8q3xlfhyhhgphefqvfgv4qzxpvw5
2023-10-22T12:18:59Z INFO :: 02.deposit.py:9:main() :: Script address:       addr_test1wpst9j7l3qu99gfwzwlvqd6c3ujj8c087k8a62tqnfy7wls89sexm
2023-10-22T12:18:59Z INFO :: 02.deposit.py:20:main() :: Creating the transaction...
2023-10-22T12:18:59Z INFO :: 02.deposit.py:38:main() :: Signing the transaction...
2023-10-22T12:19:01Z INFO :: 02.deposit.py:40:main() :: 277721a895066e5a4c6e7b863bca6fc565c2d8015ab5a2456ac2e8f881d21fcd
2023-10-22T12:19:01Z INFO :: 02.deposit.py:42:main() :: Submitting the transaction...
2023-10-22T12:19:02Z INFO :: 02.deposit.py:44:main() :: Done.
```

The claiming part is still work in progress and is not working yet.

The beneficiary will eventually be able to claim the funds by running:

```shell
python 03.claim.py
```

The script output will look something like as follows:

<!-- markdownlint-disable -->

```text
2023-10-22T12:30:20Z ERROR :: 03.claim.py:127:claim_script() :: signing tx failed: {'EvaluationFailure': {'ScriptFailures': {'spend:0': [{'validatorFailed': {'error': "An error has occurred:  User error:\nThe machine terminated because of an error, either from a built-in function or from an explicit use of 'error'.", 'traces': ['ADA price: 3691 / precision: -4 | USD price: 270929287455974 / precision: -14 | valid from: 1700579517301 -> valid to: 1700583237301']}}]}}}
```

This is expected in the early version of this script to demonstrate to you the
process of accessing the data in the datum. The values are presented in the
error trace. These can be more easily read below:

```json
{'EvaluationFailure':
   {'ScriptFailures':
      {'spend:0':
         [
            {'validatorFailed':
               {'error': "An error has occurred:  User error:\nThe machine terminated because of an error, either from a built-in function or from an explicit use of 'error'.", 'traces':
                  ['ADA price: 3691 / precision: -4 | USD price: 270929287455974 / precision: -14 | valid from: 1700579517301 -> valid to: 1700583237301']
                }
            }
         ]
      }
   }
}
```

<!-- markdownlint-enable -->

#### Cleaning up - reclaiming the deposit

The funds can be claimed back (refunded) and the smart contract removed from
on-chain. See "Resetting oracle DApp" [below](#resetting-dapp-state).

### Resetting DApp state

To reset the state established by the scripts here, e.g. to help debugging and
script development, the minting and claim scripts need to reclaim their value
and be undeployed.

We work backwards to do this, working first from the oracle based DApp.

#### Resetting oracle DApp

<!-- markdownlint-disable -->

1. From the `demo-datum-opshin` folder refund the value:

```sh
python refund.py
```

2. undeploy the script:

```sh
python 04.undeploy.py
```

<!-- markdownlint-enable -->

#### Reset minting state

1. From the minting folder, burn the tokens:

```sh
python burn.py
```
