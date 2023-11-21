"""Smart contract to perform some operation based on the validity of
an Orcfax smart contract.
"""


from opshin.ledger.interval import *  # pylint ignore=W0401

# policy ID of the Oracle AUTH tokens
# auth_policy_id = '104d51dd927761bf5d50d32e1ede4b2cff477d475fe32f4f780a4b21'
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
    """Smart Contract Datum format
    source: the published, who can also reclaim the UTxO anytime (refund)
    fee_address: the address where the fee must be paid
    fee: the fee amount which must be paid
    """

    source: PubKeyHash
    fee_address: bytes
    fee: int


@dataclass
class ExchangeRedeemer(PlutusData):
    CONSTR_ID = 0
    pass


@dataclass
class RefundRedeemer(PlutusData):
    CONSTR_ID = 1
    pass


def validator(
    datum: PublishParams,
    redeemer: Union[ExchangeRedeemer, RefundRedeemer],
    context: ScriptContext,
) -> None:
    # salt provides a user-controlled mechanism to create a unique
    # script address for testing.
    salt = "O2c1TU6Jr12nSGyJJuAkp"  # replace using nanoid, uuid, ulid, etc.
    if isinstance(redeemer, ExchangeRedeemer):
        # check if the fee has been paid to the fee address
        fee_address_found = False  # fee address found
        fee_paid = False  # fee paid
        for item in context.tx_info.outputs:
            if datum.fee_address == item.address.payment_credential.credential_hash:
                fee_address_found = True
                if item.value.get(b"", {b"": 0}).get(b"", 0) >= datum.fee:
                    fee_paid = True
        assert fee_address_found, "Fee address not found in outputs!"
        assert fee_paid, "Fee too small!"

        # Check if the datum was published by the oracle by checking
        # if the token attached to the datum is the correct one
        auth_policy = False  # Datum has the token with the correct auth policy attached
        datum_is_price_feed = False  # Datum is a PriceFeed object
        datum_condition = False  # datum condition
        price_feed_valid_through = 0  # Validity expiration time

        # An Orcfax price-feed datum contains the target price-pair and
        # reversed value, so ADA/USD and USD/ADA in the case of ADA/USD.
        # l_ denotes left-hand price, and  r_ right-hand or reversed price.
        l_price = 0  # Price
        l_precision = 0  # Precision
        r_price = 0  # Reversed price
        r_precision = 0  # Reversed price precision

        valid_from = 0  # Valid from
        valid_through = 0  # Valid through
        for reference_input in context.tx_info.reference_inputs:
            reference_script = reference_input.resolved.reference_script
            if isinstance(reference_script, NoScriptHash):  # if this is not a script
                reference_input_datum = reference_input.resolved.datum
                if isinstance(
                    reference_input_datum, SomeOutputDatum
                ):  # if this is a Datum
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

                        # price_feed_identifier = price_feed.identifier
                        price_feed_valid_through = price_feed.valid_through.val
                        # price_feed_signature = price_feed.signature

                        price_feed_name: bytes = price_feed.value_dict[b"name"]
                        if price_feed_name == b"ADA-USD|USD-ADA":
                            price_feed_value: List[ValuePair] = price_feed.value_dict[
                                b"value"
                            ]

                            # read the price
                            price_feed_value_0: ValuePair = price_feed_value[0]
                            l_precision = price_feed_value_0.precision - uint_64_limit
                            l_price = price_feed_value_0.price

                            # read the reversed price
                            price_feed_value_1: ValuePair = price_feed_value[1]
                            r_precision = price_feed_value_1.precision - uint_64_limit
                            r_price = price_feed_value_1.price
                            # read valid_from and valid_through
                            price_feed_value_reference: List[
                                Anything
                            ] = price_feed.value_dict[b"valueReference"]
                            dict_valid_from: Dict[
                                bytes, Anything
                            ] = price_feed_value_reference[0]
                            dict_valid_through: Dict[
                                bytes, Anything
                            ] = price_feed_value_reference[1]
                            valid_from: int = dict_valid_from.get(b"value", 0)
                            valid_through: int = dict_valid_through.get(b"value", 0)
                            datum_condition = True
        # Oracle data must be within a certain validity range. We are
        # not yet checking for this in the conditions below.
        validity_range = make_range(price_feed_valid_through, price_feed_valid_through)
        # Assert that various smart contract conditions are met in order
        # to let the Tx be processed.
        assert auth_policy, "Oracle not authenticated!"
        assert datum_is_price_feed, "Oracle Datum is not a PriceFeed object!"
        assert datum_condition, "Datum condition is False!"
        # Finally, fail validation artificially to display the feed
        # data to users. Users can take this information and convert it
        # to conditions in their own OpShin smart contracts.
        assert False, (
            f"ADA price: {l_price} / precision: {l_precision} "
            f"| USD price: {r_price} / precision: {r_precision} "
            f"| valid from: {valid_from} -> valid to: {valid_through}"
        )
    elif isinstance(redeemer, RefundRedeemer):
        # Allow the owner key to reclaim the funds anytime.
        assert datum.source in context.tx_info.signatories, "Refund signature missing!"
    else:
        assert False, "wrong redeemer (" + str(salt) + ")"
