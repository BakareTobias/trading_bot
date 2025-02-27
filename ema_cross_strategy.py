import pandas
import mt5_lib
import indicator_lib
import helper_library
import telegram_lib
   
#function to run strategy(this is the function to call in main.py)
def run_strategy(project_settings):
    """ function to run stategy for trading bot 
    param:  project_settings: json of login details
    return: Boolean. True = stategy ran successfully with no errors.else = false """

    #symbol to trade
    symbols = project_settings['mt5']['symbols']
    #timeframe to trade 
    timeframe= project_settings['mt5']['timeframe']

    

    #run through strategy for specified symbols 
    for symbol in symbols:
        #Strategy Risk Management
        #Generate comment string 
        comment_string = f'EMA_Cross_Strategy_{symbol}' #as to be consistent with other definitions through out project

        #use json for ema values
        ema_one = project_settings["symbols"][f"{symbol}"][0]
        ema_two = project_settings["symbols"][f"{symbol}"][1] 
        #cancel orders related to symbol and strategy 
        """ mt5_lib.cancel_filtered_orders(
            symbol=symbol,
            comment=comment_string
        ) """
        #Trade strategy 
        data = ema_cross_strategy(
            symbol=symbol,
            timeframe=timeframe,
            ema_one=ema_one,
            ema_two=ema_two,
            balance=2000,
            amount_to_risk=20
            ) 
        if data:
            print(f'Trade signal detected. EMA cross strategy trade placed successfully on {symbol}:{timeframe} ')      
        else:
            print(f'No trade signal detected for {symbol}')



#function to run EMA strategy 
def ema_cross_strategy(symbol,timeframe, ema_one, ema_two, balance, amount_to_risk):
    """ function which runs EMA cross strategy 
    params: symbol- string of the symbol/pair
            timeframe: string of timeframe to be queried 
            ema_one: integer of lowest timeframe EMA
            ema_two: integer of higher timeframe EMA
            balance: float of current balance
            amount_to_risk: float of amount to risk er trade on stategy
    return: trade eent dataframe """

    """ PSEUDO CODE STEPS
    Step 1: Retrieve data -> get data()
    Step 2: Calculate indicators - calc_indicators()
    Step 3: Determine if trade event has occured and calculate parameters for all info available- det_trade()
    Step 4: check most recent candle for trading opportunity 
    Step 5: if trade event has occured send order and telegram signal   """

    #Step 1
    data = get_data(
        symbol=symbol,
        timeframe=timeframe,
        
    )

    #Step 2
    data = calc_indicators(
        data=data,
        ema_one=ema_one,
        ema_two=ema_two
    )

    #Step 3 
    data = det_trade(
        data=data,
        ema_one=ema_one,
        ema_two=ema_two
    )

    #Step 4
    trade_event = data.tail(1).copy( )#copy info for most recent formed candle 
    if trade_event['ema_cross'].values:
        #Make trade requires balance, comment, amount_to_risk
        #Create comment
        comment_string = f'EMA_Cross_Strategy_{symbol}'
        print(comment_string)
        
        #calculate lot-size to pass to telegram function
        lot_size = helper_library.calc_lot_size(
            balance=balance,
            amount_to_risk=amount_to_risk,
            stop_loss=trade_event['stop_loss'].values,
            stop_price=trade_event['stop_price'].values,
            symbol=symbol
        )

        #do not place a new trade till old trade is closed
        open_trades = mt5_lib.get_filtered_list_of_orders(
            symbol=symbol, 
            comment=comment_string)
    
        if open_trades:
            print(f"EMA cross Trade already open for {symbol}. Skipping new trade.")
            return False  # Do not open a new trade


        #function to send telegram message 
        telegram_lib.send_telegram_message(
            stop_price=trade_event['stop_price'].values,
            stop_loss=trade_event['stop_loss'].values,
            take_profit=trade_event['take_profit'].values,
            lot_size=lot_size,
            comment=comment_string,
            symbol = symbol
        )

        

        #Make trade 
        make_trade_outcome = helper_library.make_trade(
            balance=balance,
            comment=comment_string,
            amount_to_risk=amount_to_risk,
            symbol=symbol,
            take_profit=trade_event['take_profit'].values,
            stop_loss=trade_event['stop_loss'].values,
            stop_price=trade_event['stop_price'].values
        )
    else: 
        make_trade_outcome = False
    return make_trade_outcome

#function to run EMA strategy 
def ema_cross_strategy_backtest(symbol,timeframe, ema_one, ema_two, test_period):
    """ function which backtests EMA cross strategy 
    params: symbol- string of the symbol/pair
            timeframe: string of timeframe to be queried 
            ema_one: integer of lowest timeframe EMA
            ema_two: integer of higher timeframe EMA
            test_period - integer of number of rows to test 
    return: trade  dataframe """

    """ PSEUDO CODE STEPS
    Step 1: Retrieve data -> get data()
    Step 2: Calculate indicators - calc_indicators()
    Step 3: Determine if trade event has occured and calculate parameters for all info available- det_trade()
     """

    #Step 1
    data = get_data(
        symbol=symbol,
        timeframe=timeframe,
        test_period=test_period
        
        
    )

    #Step 2
    data = calc_indicators(
        data=data,
        ema_one=ema_one,
        ema_two=ema_two
    )

    #Step 3 
    data = det_trade(
        data=data,
        ema_one=ema_one,
        ema_two=ema_two
    )
    return data
    

#Step 1: retrieve data
def get_data(symbol, timeframe,test_period=300):
    """ function to get data from mt5. data is in from of candlesticks
    param:  symbol: string
            timeframe: string
    return: dataframe of data  """

    data = mt5_lib.get_candlesticks(
        symbol=symbol,
        timeframe=timeframe,
        number_of_candles=test_period
    )
    return data

#function to calculate indicators
def calc_indicators(data,ema_one,ema_two):
    """ function to calculate both EMA, and calculate an EMA cross
     param: data-dataframe of candle info
            ema_one - ineger of lower EMA
            ema_two - integer of higher EMA
             
    return: dataframe with updated columns """

    #calculate EMA 1
    dataframe = indicator_lib.calc_custom_ema(
        dataframe=data,
        ema_size=ema_one)

    #calculate EMA 2
    dataframe = indicator_lib.calc_custom_ema(
        dataframe=dataframe,
        ema_size=ema_two)
    
    #calculate EMA cross
    dataframe = indicator_lib.ema_cross_calculator(
        dataframe=dataframe,
        ema_one=ema_one,
        ema_two=ema_two
    )
    

    #return dataframe
    return dataframe

#function to determine if trade event has ocured, and calculate trade signal parameters
def det_trade(data, ema_one, ema_two):
    """
    Function to calculate the trade values for the strategy. For the EMA Cross strategy, rules are as follows:
    1. For each trade, stop_loss is the corresponding highest EMA (i.e. if ema_one is 50 and ema_two is 200, stop_loss
    is ema_200)
    2. For a BUY (GREEN Candle), the entry price (stop_price) is the high of the previous completed candle
    3. For a SELL (RED Candle), the entry price (stop_price) is the low of the previous completed candle
    4. The take_profit is the absolute distance between the stop_price and stop_loss, added to a BUY stop_price and
    subtracted from a SELL stop_price
    :param dataframe: dataframe of data with indicators
    :param ema_one: integer of EMA size
    :param ema_two: integer of EMA size
    :return: dataframe with trade values added
    """
     
    #Get the column names 
    ema_one_column = 'ema' + str(ema_one)
    ema_two_column = 'ema' + str(ema_two)

    #choose largest EMA (EMA that will be used for stop loss)
    if ema_one > ema_two:
        ema_column = ema_one_column
        min_value  = ema_one
    elif ema_two > ema_one:
        ema_column = ema_two_column
        min_value = ema_two
    else:
        #EMA values are equal, raise an error
        raise ValueError('EMA values are the same...')
    
    #copy data frame to avoid panda copy warnings 
    dataframe = data.copy()

    #add TP, SL, and stop price column to dataframe 
    dataframe['take_profit'] = 0.00 #trade values on mt5 must be float 
    dataframe['stop_price'] = 0.00
    dataframe['stop_loss'] = 0.00
     
    #iterate through the dataframe and calculate trade signal for EMA cross
    for i in range(len(dataframe)):
        #skip rows until EMA starts 
        if i<= (min_value ):
            continue
        else:
            
            #find when EMA cross is True
            if dataframe.loc[i,'ema_cross']:
                #determine if green candle
                if dataframe.loc[i,'open'] < dataframe.loc[i,'close']:
                    #stop loss = larger EMA 
                    stop_loss = dataframe.loc[i,ema_column]
                    #stop price = high of recently closed candle 
                    stop_price = dataframe.loc[i,'high'] 
                    #take profit = (stop price - stop loss) + stop price
                    distance = stop_price-stop_loss
                    take_profit = 2.5*distance + stop_price
                #elif candle is red
                elif dataframe.loc[i,'close'] < dataframe.loc[i,'open']:
                    #stop loss = larger EMA 
                    stop_loss = dataframe.loc[i,ema_column]
                    #stop price = high of recently closed candle 
                    stop_price = dataframe.loc[i,'low'] 
                    #take profit = (stop price - stop loss) + stop price
                    distance = stop_loss-stop_price
                    take_profit =  stop_price - 2.5*distance 
                else:
                    stop_loss = 0.0
                    stop_price = 0.0
                    take_profit = 0.0
                #add calculated values back to dataframe
                dataframe.loc[i, 'stop_loss'] = stop_loss
                dataframe.loc[i, 'stop_price'] = stop_price
                dataframe.loc[i, 'take_profit'] = take_profit
    #return dataframe
    return dataframe