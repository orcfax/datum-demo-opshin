"""Smart contract to perform some operation based on the validity of
an Orcfax smart contract.

An original version of this contract can be found at the link below. It
provides a useful reference point for some of what is being done here:

* https://github.com/orcfax/datum-demo-opshin/blob/bf3641760c8c2ec6ae9d2aeb9b1a47d026ba1033/src/datum-demo-opshin/contract.py

"""

from opshin.ledger.interval import *  # pylint ignore=W0401


# policy ID of the Oracle AUTH tokens
# hex = '104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21'
policy_id = b"\x10MQ\xdd\x92wa\xbf]P\xd3.\x1e\xdeK,\xffG}G_\xe3/Ox\nK!"

# Unsigned integer limit.
uint_64_limit = 18446744073709551616


@dataclass
class ValuePair(PlutusData):
    CONSTR_ID = 3
    price: int
    precision: int


@dataclass
class Expiry(PlutusData):
    CONSTR_ID = 1
    val: POSIXTime


@dataclass
class PriceFeed(PlutusData):
    """Orcfax Price Feed Datum format"""

    CONSTR_ID = 0
    value_dict: Dict[bytes, Anything]
    identifier: bytes
    valid_through: Expiry
    signature: bytes


@dataclass
class PublishParams(PlutusData):
    """Smart Contract Datum format.

    source: the publisher, who can also reclaim the UTxO anytime (refund)
    fee_address: the address where the fee must be paid
    fee: the fee amount which must be paid
    """

    source: PubKeyHash
    fee_address: bytes
    fee: int


@dataclass
class HelloWorldRedeemer(PlutusData):
    CONSTR_ID = 0
    pass


@dataclass
class RefundRedeemer(PlutusData):
    CONSTR_ID = 1
    pass


def validate_circuit_breaker(l_precision: int, l_price: int):
    """todo..."""
    # ADA safety breaker: 0.99. This value might be encoded in another
    # reference datum belonging to the liquidator/client using this
    # smart contract.
    ada_circuit_breaker = 990000

    # Calculate a signed integer value for the price.
    l_precision = -(l_precision)
    ada_price_precision = min([6, l_precision])
    ada_price_precision = max([ada_price_precision, 6])
    assert ada_price_precision <= 6, f"precision: {ada_price_precision}"
    diff = max([l_precision, ada_price_precision]) - min(
        [l_precision, ada_price_precision]
    )
    divisor = int(f"1{'0'*diff}")
    if divisor > 1000000:
        ada_price = l_price // divisor
    else:
        ada_price = l_price * divisor
    assert (
        ada_price < ada_circuit_breaker
    ), f"ada price is greater than breaker: {ada_price}"


def validator(
    datum: PublishParams,
    redeemer: Union[HelloWorldRedeemer, RefundRedeemer],
    context: ScriptContext,
) -> None:
    """OpShin validator."""

    # salt provides a user-controlled mechanism to create a unique
    # script address for testing. Replace using nanoid, uuid, ulid, etc.
    salt = "O2c1TU6Jr12nSGyJJuAkp"

    if isinstance(redeemer, HelloWorldRedeemer):
        # check if the fee has been paid to the fee address
        fee_address_found = False  # fee address found
        fee_paid = False  # fee paid
        for item in context.tx_info.outputs:
            if datum.fee_address == item.address.payment_credential.credential_hash:
                fee_address_found = True
                if item.value.get(b"", {b"": 0}).get(b"", 0) >= datum.fee:
                    fee_paid = True
        assert fee_address_found, "redeemer fee address not found in outputs!"
        assert fee_paid, "redeemer fee too small!"

        # Check if the datum was published by the oracle by checking
        # if the token attached to the datum is the correct one
        auth_policy = False  # Datum has the token with the correct auth policy attached
        datum_is_price_feed = False  # Datum is a PriceFeed object

        # An Orcfax v0 price-feed datum contains the target price-pair
        # and reversed value. We want to validate against the left hand
        # target value, so ADA in the case of ADA-USD.

        # Price and precision work together to inform us about scientific
        # notation, e.g. x * 10^-y.
        l_price = 0  # Price.
        l_precision = 0  # Precision.

        for reference_input in context.tx_info.reference_inputs:
            reference_script = reference_input.resolved.reference_script
            if isinstance(reference_script, NoScriptHash):  # if this is not a script/
                reference_input_datum = reference_input.resolved.datum
                if isinstance(
                    reference_input_datum, SomeOutputDatum
                ):  # if this is a Datum.
                    values = reference_input.resolved.value
                    if any(
                        [
                            value > 0
                            for value in values.get(policy_id, {b"": 0}).values()
                        ]
                    ):
                        auth_policy = True
                        price_feed: PriceFeed = reference_input_datum.datum
                        datum_is_price_feed = True
                        price_feed_name: bytes = price_feed.value_dict[b"name"]
                        if price_feed_name == b"ADA-USD|USD-ADA":
                            price_feed_value: List[ValuePair] = price_feed.value_dict[
                                b"value"
                            ]
                            # Read the price.
                            price_feed_value_0: ValuePair = price_feed_value[0]
                            l_precision = price_feed_value_0.precision - uint_64_limit
                            l_price = price_feed_value_0.price

        # Assert features of this Tx are correct.
        assert auth_policy, "datum source could not be authenticated!"
        assert datum_is_price_feed, "oracle Datum is not a PriceFeed object!"

        validate_circuit_breaker(l_precision, l_price)

    elif isinstance(redeemer, RefundRedeemer):
        # Allow the script to be undeployed.
        assert (
            datum.source in context.tx_info.signatories
        ), f"the refund signature '{datum.source}' missing!"
    else:
        assert False, f"wrong redeemer for this script ({salt})"
