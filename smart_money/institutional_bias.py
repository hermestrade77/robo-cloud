from smart_money.bos import detect_bos
from smart_money.choch import detect_choch
from smart_money.sweep import detect_sweep
from smart_money.displacement import (
    detect_displacement
)

from smart_money.mitigation import (
    detect_mitigation
)

from smart_money.premium_discount import (
    premium_discount
)


def institutional_bias(df):

    bos = detect_bos(df)

    choch = detect_choch(df)

    sweep = detect_sweep(df)

    displacement = detect_displacement(df)

    mitigation = detect_mitigation(df)

    pd_zone = premium_discount(df)

    bullish = 0
    bearish = 0

    signals = [
        bos,
        choch,
        sweep,
        displacement,
        mitigation
    ]

    for s in signals:

        if s == "BUY":
            bullish += 1

        elif s == "SELL":
            bearish += 1

    # desconto favorece compra
    if pd_zone == "DISCOUNT":
        bullish += 1

    # premium favorece venda
    if pd_zone == "PREMIUM":
        bearish += 1

    if bullish >= 4:
        return "BUY"

    if bearish >= 4:
        return "SELL"

    return "NONE"