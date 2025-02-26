import pandas as pd
import telegram_lib
import  helper_library


#function to return max streak of wins/losses
def max_consecutive_results(trade_log, result_type):
    """
    Returns the maximum number of consecutive trade results in trade_log that have the specified result_type.
    params: trade_log - tuple of trade info
            result_type: String- either WIN or LOSS

    return: int of max streak
        """
    max_streak = 0
    current_streak = 0
    for trade in trade_log:
        if trade[0] == result_type:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 0
    return max_streak

def backtest_data(symbol, balance, amount_to_risk, test_period,ema_one,ema_two):
    """ Functiont to backtest one of my strategies using trading singal data provided 
    param:  symbol      -  string of symbol being backtested
            balance     -  int of start account balance
            amount_to_risk - float of amount to risk per trade(not a %)
            test_period -  int of how many rows of backtest_data to run test for """
    
    #initialize variables
    OPEN_TRADE = None
    TRADE_LOG = []

    #set pip value depending on symbol. JPY crosses all have 0.01 pip value
    if ('JPY' in symbol) or ("XAU" in symbol):
        pip = 0.01
        dp  = 2#round values to 2 decimal places

    else:
        pip = 0.0001
        dp = 4#round values to 4 decimal places

    # Read OHLC + Spread data from a pickle file.
    backtest_data = pd.read_csv(f"{symbol}_{ema_one}_{ema_two}")
    backtest_data = backtest_data.tail(test_period)

    #for each row in backtes_data
    for i in range(len(backtest_data)):
        """ STAGE 1: preparing row and spread """
        row = backtest_data.iloc[i]
        # Convert spread to decimal
        #spread = row["spread"] / 100


        """ STAGE 2 Trade placement: only place a trade if row["place_trade"] is True and no trade is currently open. """
        if OPEN_TRADE is None and row["stop_price"]:

            """ STAGE 3: preparing trade parameters """
            # Adjust entry price for spread. Here, row["stop_price"] is used as the basis.
            entry_price = row["stop_price"]  
            sl = row["stop_loss"]         # Stop Loss price
            tp = row["take_profit"]     # Take Profit price

            # Determine trade type and calculate risk and reward.
            # For a BUY: risk = (entry - SL) and reward = (TP - entry)
            # For a SELL: risk = (SL - entry) and reward = (entry - TP)
            if entry_price > sl:
                order_type = 'BUY'
                entry_price = entry_price
                risk = entry_price - sl
                reward = tp - entry_price
            elif entry_price < sl:
                entry_price = entry_price 
                order_type = 'SELL'
                risk = sl - entry_price
                reward = entry_price - tp
            else:
                risk = 0
                reward = 0
                order_type = None

            # Calculate risk:reward ratio (absolute value to cover both BUY & SELL)
            risk_reward = abs(reward / risk) if risk != 0 else 0

            # Only place the trade if the risk:reward ratio is at least 1.5.
            if risk_reward >= 0:
                # Calculate lot size using the local calculator
                lot_size = helper_library.calc_lot_size(
                    balance,
                    amount_to_risk,
                    sl,
                    entry_price,
                    symbol=symbol
                )

                # Capture entry time from the data row.
                entry_time = row["std_time"]

                #capture pips risked (if loss)
                pips_risked = abs((entry_price-sl)/pip)

                #capture pips won (if profit)
                pips_to_be_made = abs((entry_price-tp)/pip)

                #capture pip value(necessary for profit/loss calculations)
                pip_value_numerator = 100000*pip
                pip_value = pip_value_numerator/entry_price
                
                OPEN_TRADE = {
                    "entry_time": entry_time,
                    "order_type": order_type,
                    "entry": entry_price,
                    "sl": sl,
                    "tp": tp,
                    "lot_size": lot_size,
                    "risk_reward": risk_reward,  # Store the pre-trade risk:reward ratio if needed.
                    "pip_value": pip_value, #value of a pip
                    "pips_risked":pips_risked, #potential pip loss
                    "pips_made" : pips_to_be_made
                }

                telegram_lib.send_telegram_message(
                    stop_price=entry_price,
                    stop_loss=sl,
                    take_profit=tp,
                    lot_size=lot_size,
                    comment=f'EMA_cross_{symbol}'
                )
            else:
                # If risk:reward is less than 1.5, skip placing the trade.
                pass

        elif OPEN_TRADE:  # If a trade is open, check SL first, then TP.
            # Capture exit time from the current row.
            exit_time = row["std_time"]

            # Recalculate the risk:reward ratio for logging (if desired, though it was computed at entry)
            if OPEN_TRADE["order_type"] == "BUY":
                risk = OPEN_TRADE["entry"] - OPEN_TRADE["sl"]
                reward = OPEN_TRADE["tp"] - OPEN_TRADE["entry"]
            else:  # SELL order
                risk = OPEN_TRADE["sl"] - OPEN_TRADE["entry"]
                reward = OPEN_TRADE["entry"] - OPEN_TRADE["tp"]

            risk_reward = abs(reward / risk) if risk != 0 else 0

            if OPEN_TRADE["order_type"] == "BUY":
                if row["low"] <= OPEN_TRADE["sl"]:  # Stop Loss hit for BUY
                    #loss = loss in pip * pip value * lot size
                    loss = OPEN_TRADE["pips_risked"] * OPEN_TRADE["lot_size"] *OPEN_TRADE["pip_value"]
                    balance -= loss
                    TRADE_LOG.append((
                        "LOSS", 
                        OPEN_TRADE["entry_time"], 
                        exit_time, 
                        "BUY", 
                        round(OPEN_TRADE["entry"], dp), 
                        round(OPEN_TRADE["sl"], dp),   # Exit price is the SL level
                        round(OPEN_TRADE["sl"], dp),   # Recorded Stop Loss
                        round(OPEN_TRADE["tp"], dp),   # Recorded Take Profit
                        round(OPEN_TRADE["lot_size"], 2),
                        round(risk_reward, 2)
                    ))
                    OPEN_TRADE = None
                elif row["high"] >= OPEN_TRADE["tp"]:  # Take Profit hit for BUY
                    #profit = profit in pip * pip value * lot size
                    profit = OPEN_TRADE["pips_made"] * OPEN_TRADE["lot_size"] * OPEN_TRADE["pip_value"]
                    balance += profit
                    TRADE_LOG.append((
                        "WIN", 
                        OPEN_TRADE["entry_time"], 
                        exit_time, 
                        "BUY", 
                        round(OPEN_TRADE["entry"], dp), 
                        round(OPEN_TRADE["tp"], dp),   # Exit price is the TP level
                        round(OPEN_TRADE["sl"], dp),
                        round(OPEN_TRADE["tp"], dp),
                        round(OPEN_TRADE["lot_size"], 2),
                        round(risk_reward, 2)
                    ))
                    OPEN_TRADE = None
            else:  # SELL order
                if row["high"] >= OPEN_TRADE["sl"]:  # Stop Loss hit for SELL (price rises)
                    #loss = loss in pip * pip value * lot size
                    loss = OPEN_TRADE["pips_risked"] * OPEN_TRADE["lot_size"] * OPEN_TRADE["pip_value"]
                    balance -= loss
                    TRADE_LOG.append((
                        "LOSS", 
                        OPEN_TRADE["entry_time"], 
                        exit_time, 
                        "SELL", 
                        round(OPEN_TRADE["entry"], dp), 
                        round(OPEN_TRADE["sl"], dp),   # Exit price is the SL level
                        round(OPEN_TRADE["sl"], dp),
                        round(OPEN_TRADE["tp"], dp),
                        round(OPEN_TRADE["lot_size"], 2),
                        round(risk_reward, 2)
                    ))
                    OPEN_TRADE = None
                elif row["low"] <= OPEN_TRADE["tp"]:  # Take Profit hit for SELL (price falls)
                    #profit = profit in pip * pip value * lot size
                    profit = OPEN_TRADE["pips_made"] * OPEN_TRADE["lot_size"] * OPEN_TRADE["pip_value"]
                    balance += profit
                    TRADE_LOG.append((
                        "WIN", 
                        OPEN_TRADE["entry_time"], 
                        exit_time, 
                        "SELL", 
                        round(OPEN_TRADE["entry"], dp), 
                        round(OPEN_TRADE["tp"], dp),   # Exit price is the TP level
                        round(OPEN_TRADE["sl"], dp),
                        round(OPEN_TRADE["tp"], dp),
                        round(OPEN_TRADE["lot_size"], 2),
                        round(risk_reward, 2)
                    ))
                    OPEN_TRADE = None

    # Performance Summary
    wins = sum(1 for trade in TRADE_LOG if trade[0] == "WIN")
    losses = len(TRADE_LOG) - wins
    win_rate = (wins / len(TRADE_LOG)) * 100 if TRADE_LOG else 0
    win_rate = round(win_rate,2)
    final_balance = round(balance,2)

    # Compute the overall average risk:reward ratio from all trades
    risk_reward_values = [trade[-1] for trade in TRADE_LOG if trade[-1] is not None]
    avg_risk_reward = sum(risk_reward_values) / len(risk_reward_values) if risk_reward_values else 0

    # Compute average risk:reward ratio for winning trades separately.
    winning_rr_values = [trade[-1] for trade in TRADE_LOG if trade[0] == "WIN"]
    avg_win_rr = sum(winning_rr_values) / len(winning_rr_values) if winning_rr_values else 0

    # Compute the average dollar loss for losing trades.
    losing_trades = [trade for trade in TRADE_LOG if trade[0] == "LOSS"]
    loss_amounts = []
    for trade in losing_trades:
        # trade tuple: (Result, EntryTime, ExitTime, OrderType, EntryPrice, ExitPrice, StopLoss, TakeProfit, LotSize, RiskReward)
        result, entry_time, exit_time, order_type, entry_price, exit_price, stop_loss, take_profit, lot_size, rr = trade
        if order_type == "BUY":
            loss_amt = (entry_price - exit_price) * lot_size
        else:  # SELL
            loss_amt = (exit_price - entry_price) * lot_size
        loss_amounts.append(loss_amt)
    avg_loss_amount = sum(loss_amounts) / len(loss_amounts) if loss_amounts else 0

    # Compute the average dollar profit for winning trades.
    winning_trades = [trade for trade in TRADE_LOG if trade[0] == "WIN"]
    profit_amounts = []
    for trade in winning_trades:
        # For winning trades, trade tuple: (Result, EntryTime, ExitTime, OrderType, EntryPrice, ExitPrice, StopLoss, TakeProfit, LotSize, RiskReward)
        result, entry_time, exit_time, order_type, entry_price, exit_price, stop_loss, take_profit, lot_size, rr = trade
        if order_type == "BUY":
            profit_amt = (exit_price - entry_price) * lot_size
        else:  # SELL
            profit_amt = (entry_price - exit_price) * lot_size
        profit_amounts.append(profit_amt)
    avg_profit_amount = sum(profit_amounts) / len(profit_amounts) if profit_amounts else 0

    # Calculate maximum consecutive wins and losses using the max_consecutive_results function.
    max_win_streak = max_consecutive_results(TRADE_LOG, "WIN")
    max_loss_streak = max_consecutive_results(TRADE_LOG, "LOSS")

    # Save trade log to CSV with additional columns for StopLoss, TakeProfit, and RiskReward.
    trade_df = pd.DataFrame(TRADE_LOG, columns=[
        "Result", "EntryTime", "ExitTime", "OrderType", 
        "EntryPrice", "ExitPrice", "StopLoss", "TakeProfit", "LotSize", "RiskReward"
    ])

    """ # Optionally, round numeric columns in the DataFrame.
    for col in ["EntryPrice", "ExitPrice", "StopLoss", "TakeProfit", "LotSize", "RiskReward"]:
        trade_df[col] = trade_df[col].astype(float).round(2) """
        
    trade_df.to_csv("trade_results.csv", index=False)

    backtest_results = {
        "Total Trades": len(TRADE_LOG),
        "Wins": wins,
        "Losses":losses,
        "Win Rate": f'{win_rate}%',
        "Final Balance": final_balance,
        "RR": avg_risk_reward,
        "RR(wins)": avg_win_rr,
        "M.C.W": max_win_streak,
        "M.C.L": max_loss_streak,
    }
    return backtest_results




