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

CIRCUIT_BREAKER = 990000


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
class HelloOrcfaxRedeemer(PlutusData):
    CONSTR_ID = 0
    pass


@dataclass
class RefundRedeemer(PlutusData):
    CONSTR_ID = 1
    pass


def validate_fee_paid(context: ScriptContext, datum: PublishParams):
    """Validate a small token fee was paid foe this transaction. The
    fee could be combined with further checks alongside the
    Oracle datum.
    """
    fee_address_found = False  # fee address found
    fee_paid = False  # fee paid
    for item in context.tx_info.outputs:
        if datum.fee_address == item.address.payment_credential.credential_hash:
            fee_address_found = True
            if item.value.get(b"", {b"": 0}).get(b"", 0) >= datum.fee:
                fee_paid = True
    assert fee_address_found, "redeemer fee address not found in outputs!"
    assert fee_paid, "redeemer fee too small!"


def validate_not_reference_script(reference_input: TxInInfo) -> bool:
    """Validate whether or not this is a script so that we know we're
    working with a datum. If it is a script, return False, if it isn't
    return True.
    """
    reference_script = reference_input.resolved.reference_script
    if isinstance(reference_script, NoScriptHash):
        return True
    return False


def validate_circuit_breaker(price: int, precision: int):
    """Validate circuit breaker parameters for this contract.

    The circuit breaker may come from another reference input placed
    on-chain by the DApp.
    """
    # ADA safety breaker: 0.99. This value might be encoded in another
    # reference datum belonging to the liquidator/client using this
    # smart contract.
    ada_circuit_breaker = CIRCUIT_BREAKER
    # Convert ada_price to six decimal places so that we can work with
    # it correctly.
    precision = -(precision)
    ada_price = price
    if precision > 6:
        # Purely for this script we constrain the price to six decimal
        # places. In future Orcfax datum we will make sure the precision
        # is constrained beforehand, i.e. will always be 6 for ADA/USD.
        # The precision will also be visible in the datum.
        ada_price_bytes = bytes(price)[:6]
        ada_price = int(str(ada_price_bytes))
    assert (
        ada_price < ada_circuit_breaker
    ), f"ada price '{ada_price}' is greater than breaker: {CIRCUIT_BREAKER}"


def validate_authentication_policy(reference_input: TxInInfo) -> bool:
    """Validate the authentication policy associated with the Orcfax
    datum.
    """
    reference_input_datum = reference_input.resolved.datum
    if isinstance(reference_input_datum, SomeOutputDatum):  # Ensure it's a datum.
        values = reference_input.resolved.value
        if any([value > 0 for value in values.get(policy_id, {b"": 0}).values()]):
            return True
    return False


def validate_price_feed(reference_input: TxInInfo) -> None:
    """An Orcfax v0 price-feed datum contains the target price-pair and
    reversed value. We want to validate against the target value [0],
    which is ADA in the case of ADA-USD.
    """
    reference_input_datum = reference_input.resolved.datum
    if isinstance(reference_input_datum, SomeOutputDatum):  # # Ensure it's a datum.
        price_feed: PriceFeed = reference_input_datum.datum
        assert isinstance(price_feed, PriceFeed)
        price_feed_name: bytes = price_feed.value_dict[b"name"]
        assert price_feed_name == b"ADA-USD|USD-ADA"
        price_feed_value: List[ValuePair] = price_feed.value_dict[b"value"]
        price_feed_value_0: ValuePair = price_feed_value[0]
        precision = price_feed_value_0.precision - uint_64_limit
        price = price_feed_value_0.price
        validate_circuit_breaker(price, precision)


def validate_data_from_reference_inputs(context: ScriptContext):
    """Validate the data in the reference inputs."""
    for reference_input in context.tx_info.reference_inputs:
        if validate_not_reference_script(reference_input):
            assert validate_authentication_policy(
                reference_input
            ), "datum source has no authentication policy"
            # Given an authenticated  datum Validate our application data.
            validate_price_feed(reference_input)


def validator(
    datum: PublishParams,
    redeemer: Union[HelloOrcfaxRedeemer, RefundRedeemer],
    context: ScriptContext,
) -> None:
    """OpShin validator."""

    # provides a mechanism to create a unique script address for testing.
    salt = "O2c1TU6Jr14nSGyJJuAk9"

    if isinstance(redeemer, HelloOrcfaxRedeemer):
        validate_fee_paid(context, datum)
        validate_data_from_reference_inputs(context)
    elif isinstance(redeemer, RefundRedeemer):
        # Allow the script to be undeployed.
        assert (
            datum.source in context.tx_info.signatories
        ), f"the refund signature '{datum.source}' missing!"
    else:
        assert False, f"wrong redeemer for this script ({salt})"
