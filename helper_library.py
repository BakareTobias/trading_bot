#function to calculate lot size 
import mt5_lib


def calc_lot_size(balance, amount_to_risk, stop_loss, stop_price, symbol):
    """ function to calculate lot size for a FOREX trade on mt5. balance passed as a static amount
    compounding is taken care of in parent function  
    param:  balance - float of account balance
            risk_percent - float of % to risk
            stop_loss - float of stop_loss
            stop_price - float of stop_price
            symbol - string of symbol 
    
    return: lot_size - float of lot_size"""

    #make sure account amount risked is less than account balance
    if amount_to_risk >= balance:
        raise ValueError(f" the amount to risk is too large. risk is {amount_to_risk}, balance is{balance}  ")
    

    #make sure symbol has any denotion of raw removed 
    symbol_name = symbol.split('.')
    symbol_name = symbol_name[0]

    #branch based on lot size 
    if 'JPY' or 'XAU' in symbol :
        #USDJPY pip size is 0.01
        pip_size = 0.01
        #calculate the amount of pips being risked 
        no_of_pips_risked = abs((stop_price - stop_loss) / pip_size)
        #calculate pip value 
        pip_value = (100000 * pip_size)/stop_price
       

        #calculate the raw lot size 
        raw_lot_size = amount_to_risk/(pip_value * no_of_pips_risked)
        
    elif symbol_name == 'USDCAD':
        #USDCAD pip size is 0.0001
        pip_size = 0.0001
        #calculate the amount of pips being risked 
        no_of_pips_risked = abs((stop_price - stop_loss) / pip_size)
        #calculate pip value 
        pip_value = amount_to_risk/no_of_pips_risked
        #add in exchange rate as USD is counter currency 
        pip_value = pip_value * stop_price #using the current price as the exchange rate

        #calculate the raw lot size 
        raw_lot_size = pip_value / 10
    else: #assuming pip size to be 0.0001
        pip_size = 0.0001
        #calculate the amount of pips being risked 
        no_of_pips_risked = abs((stop_price - stop_loss) / pip_size)
        #calculate pip value 
        pip_value = amount_to_risk/no_of_pips_risked
        #calculate the raw lot size 
        raw_lot_size = pip_value / 10
        
    #raise error if lot size is less than 0.01(smallest size most brokers accept)
    if raw_lot_size < 0.01:
            raise ValueError (f'lot size({raw_lot_size}) is too small: /n Entry Price:{stop_price}  Stop Loss:{stop_loss}')
    #format raw_lot_size to be broker friendly
    lot_size = float(raw_lot_size)
    #rounds to 2 decimal places.(on a small account ie <5000 USD this rounding may affect risk)
    lot_size = round(lot_size,2)
    #add in a catch to make sure lot size is not extreme 
    if lot_size >=10:
        lot_size = 9.99

    return lot_size



#function to make a trade 
def make_trade(balance, comment, amount_to_risk, symbol, take_profit, stop_loss, stop_price):
    """ function to place a trade once a price signal is retrieved 
    param:  balance - float of account balance 
            comment - string on strategy used for signal
            amount_to_risk - float % to risk per trade
            symbol  - string of pair 
            take_profit - float of tp price
            stop_loss  - float of sl price
            stop_price - float of stop price 
    
    return: trade outcome"""

    ###Pseudo code 
    #1. format all values 
    #2. determine lot size
    #3. send trade to mt5
    #4. return outcome
    #Future: send trade signal/outcome to discord/other third party app
    #Future: currency conversion for accounts in non-USD amounts 

    #format values
    balance = float(balance)
    balance = round(balance,2)

    take_profit = float(take_profit)
    take_profit = round(take_profit,4)

    stop_loss = float(stop_loss)
    stop_loss = round(stop_loss, 4)

    stop_price = float(stop_price)
    stop_price = round(stop_price, 4)

    #2. detrmine lot size
    lot_size = calc_lot_size(
        balance=balance,
        amount_to_risk=amount_to_risk,
        stop_loss=stop_loss,
        stop_price=stop_price,
        symbol=symbol
        )
    
    risk_reward = abs(take_profit-stop_price)/abs(stop_price-stop_loss)
    #only execute trades with a 1.5+ RR
    if risk_reward >= 1.5:
        #3. send trade to MT5
        #determine trade type
        if stop_price > stop_loss:
            trade_type = 'BUY_STOP'
        elif stop_price < stop_loss:
            trade_type = 'SELL_STOP'

        trade_outcome = mt5_lib.place_order(
            order_type=trade_type,
            symbol=symbol,
            volume=lot_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=comment,
            stop_price=stop_price,
            direct=False
        )
        
       
        
    else:
        trade_outcome = False

    #return outcome 
    return trade_outcome    