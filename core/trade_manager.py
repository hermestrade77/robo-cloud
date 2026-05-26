import MetaTrader5 as mt5

# =========================
# TRAILING STOP
# =========================

def manage_positions(symbol):

    positions = mt5.positions_get(
        symbol=symbol
    )

    if positions is None:

        return

    for position in positions:

        ticket = position.ticket

        price_open = position.price_open

        current_sl = position.sl

        current_tp = position.tp

        position_type = position.type

        volume = position.volume

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:

            continue

        # =====================
        # BUY
        # =====================

        if position_type == mt5.ORDER_TYPE_BUY:

            current_price = tick.bid

            profit_distance = (
                current_price - price_open
            )

            # =================
            # BREAKEVEN
            # =================

            if (
                profit_distance > 5
                and current_sl < price_open
            ):

                new_sl = price_open

                modify_position(
                    ticket,
                    new_sl,
                    current_tp
                )

                print(
                    f"\nBreakeven BUY {ticket}"
                )

            # =================
            # TRAILING
            # =================

            trailing_sl = (
                current_price - 3
            )

            if trailing_sl > current_sl:

                modify_position(
                    ticket,
                    trailing_sl,
                    current_tp
                )

                print(
                    f"\nTrailing BUY {ticket}"
                )

        # =====================
        # SELL
        # =====================

        elif (
            position_type
            == mt5.ORDER_TYPE_SELL
        ):

            current_price = tick.ask

            profit_distance = (
                price_open - current_price
            )

            # =================
            # BREAKEVEN
            # =================

            if (
                profit_distance > 5
                and (
                    current_sl > price_open
                    or current_sl == 0
                )
            ):

                new_sl = price_open

                modify_position(
                    ticket,
                    new_sl,
                    current_tp
                )

                print(
                    f"\nBreakeven SELL {ticket}"
                )

            # =================
            # TRAILING
            # =================

            trailing_sl = (
                current_price + 3
            )

            if (
                current_sl == 0
                or trailing_sl < current_sl
            ):

                modify_position(
                    ticket,
                    trailing_sl,
                    current_tp
                )

                print(
                    f"\nTrailing SELL {ticket}"
                )

# =========================
# MODIFICAR POSIÇÃO
# =========================

def modify_position(
    ticket,
    sl,
    tp
):

    request = {

        "action": mt5.TRADE_ACTION_SLTP,

        "position": ticket,

        "sl": sl,

        "tp": tp,
    }

    result = mt5.order_send(request)

    print(result)