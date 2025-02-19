import mt5_lib
import ta_indicator_lib
import helper_library
import candlestick_patterns_lib

#EMA CROSS STRATEGY 1
#INDICATORS: EMA, ATR
#RULES(Long)
#Conditions:1. 20 EMA must be above 200 EMA for buys and vice versa for sells
#           2. 1H,4H,1D
#           3. Risk 0.8% per trade
#
#ENTRY: candle i-2 close above EMA. candle i-1 close above i high. entry on i
#TP 1  : Entry + 2(Entry - SL)
#TP 2  : Entry + 4.0(Entry - SL)
#SL    :  Entry - ATR + 
#RULES(Short)
#Conditions:1. Price must be below EMA(20)[trend following] 
#           
#
#ENTRY: candle i-2 close below EMA. candle i-1 close below i low. entry on i
#TP 1  : Entry + 2( SL - Entry)
#TP 2  : Entry + 4.0( SL - Entry)
#SL    :  Entry + ATR 

#v1.1 2/14/25. Adding ADX indicator. same conditions AND ADX should be less than 20 

#indicator periods and oversold parameters, for easily manipulating trade parameters

ema_period_short = 20
ema_period_long = 200
ATR_period = 14


#function to run strategy
def trend_following_strategy(symbol,timeframe,balance,amount_to_risk=20):
    """ function that runs mean reversion strategy. all rules defined above
    params: symbol - string of pair being traded
            timeframe - string of timeframe to run strategy on
            balance - float of current trading balance 
            amount to risk - float of risk per trade(default 20 of balance)"""
    
    """ PSEUDO CODE STEPS
    Step 1: Retrieve data -> get data()
    Step 2: Calculate indicators - calc_indicators()
    Step 3: Check if each condition is met 
            if yes, calculate trade parameters
    Step 4: Check most recent candle for trading opportunity
    Step 5: If trade event has occured, send order """

    #Step 1
    data = get_data(
        symbol=symbol,
        timeframe=timeframe,
        
    )

    #Step 2
    data = calc_indicators(
        data=data,
        ema_period_short=ema_period_short,
        atr_period=ATR_period
    
    )    

    #Step 3
    data = det_trade(
        data=data
    )
    return data
    #Step 4
    trade_event = data.tail(1).copy( )#copy info for most recent formed candle 
    
    if trade_event['place_trade'].values:
        #Make trade requires balance, comment, amount_to_risk
        comment_string = f'Trend_Following_Strategy{symbol}'
        print(comment_string)

        #Make trade 
        make_trade_outcome = helper_library.make_trade(
            balance=balance,
            comment=comment_string,
            amount_to_risk=amount_to_risk,
            symbol=symbol,
            take_profit=trade_event['take_profit_1'].values,
            stop_loss=trade_event['stop_loss'].values,
            stop_price=trade_event['stop_price'].values
        )
    else: 
        make_trade_outcome = False
    return make_trade_outcome


#Step 1: retrieve data
def get_data(symbol, timeframe):
    """ function to get data from mt5. data is in from of candlesticks
    param:  symbol: string
            timeframe: string
    return: dataframe of data  """

    data = mt5_lib.get_candlesticks(
        symbol=symbol,
        timeframe=timeframe,
        number_of_candles=50000
    )
    return data

#Step 2: calculate indicators
def calc_indicators(data,ema_period_short,atr_period):
    """ function to calculate EMA 20, ATR 14
     param: data-dataframe of candle info
            ema-period 
            atr-period variables ttached here to make
                        manipulation of variables easy at the top
             
    return: dataframe with updated columns """

    #calculate EMA 200
    data = ta_indicator_lib.calc_ema(data,ema_period_long)

    #Calculate EMA 20
    data = ta_indicator_lib.calc_ema(data,ema_period_short)

    #calculat ATR
    data = ta_indicator_lib.ATR(data,atr_period)#period set to default 14

    
    #return dataframe
    return data

#Step 3: Determine trade event
def det_trade(data):
    """ Function to check if all conditions have been met 
    param: data= object of price data
            ema_period_short - integer of ema period default 200
            atr_period - integer of atr perios default 14

    return: object of price data 
     """
###PART 1 CHECK TRADE CONDITIONS/RULES
    """ CONDITIONS
    1. Bias      long if ema 20> ema 200 -> True
                short if ema 20< ema 200 -> False
                default -> None


    2. Determine entry condition 1.  True if price[open]<EMA  & price[close]> EMA
                        False if price[open]>EMA & price[close]< EMA
                         default = None
                         
    3. Candle 2 condition/entry condition 3   i - 1 close above i - 2 high -> True 
                            i - 1 close below i - 2 low -> False
                            Default -> None
    
    """
    

    #copy data to avoid panda copy warnng 
    data = data.copy()

    #extract open,close,high,low
    open = data['open']
    close = data['close']
    high = data['high']
    low = data['low']
    prev_high_2 = high.shift(2)
    prev_low_2 = low.shift(2)
    prev_close_1 = close.shift(1)
    ema_short = data[f'EMA_{ema_period_short}']
    ema_long = data[f'EMA_{ema_period_long}']
    
    #iterate through dataframe and check trading conditions
    for i in range(len(data)):
        #determine bias
        if ema_short[i]> ema_long[i]:
            data.loc[i,'ema_bias'] = True
        elif ema_short[i]< ema_long[i]:
            data.loc[i,'ema_bias'] = False
        else:
            data.loc[i,'ema_bias'] = None


        #determine direction price cross EMA
        if (open[i] < ema_short[i]) & (close[i]> ema_short[i]):
            data.loc[i,'candle_cross_ema'] = True
        elif (open[i] > ema_short[i]) & (close[i]< ema_short[i]):
            data.loc[i,'candle_cross_ema'] = False
        else:
            data.loc[i,'candle_cross_ema'] = None


        #shift candle_cross_ema forward two candles
        data['candle_cross_ema_shift'] = data["candle_cross_ema"].shift(2)

        ema_cross_candle = data['candle_cross_ema_shift']

        #check if 1 candle ago closed above/below 2 candles ago high/low
        #can only work from candle 2
        if i<1:
            data.loc[i,'candle_2_condition'] = None
        else:
            #candle -1 close above -2 high
            if prev_close_1[i] >  prev_high_2[i]:
                data.loc[i,'candle_2_condition'] = True
            #candle -1 close below -2 low
            elif prev_close_1[i] < prev_low_2[i]:
                data.loc[i,'candle_2_condition'] = False
            #default
            else:
                data.loc[i,'candle_2_condition'] = None




        
        

    

###PART 2: CALCULATE TRADE PARAMS
    """ for sells
        bias == False & price crosses below ema 2 candles ago  and current candle close below previous candle high - T & T
        entry = next candle open aka current candle close
        SL = current candle ATR*multiplier 
        TP = 1.5* (entry - sl)
        

        for buys
        bias == True & price crosses BOVE ema 2 candles ago  and current candle close above previous candle high - F & F
        entry = next candle open aka current candle close
        SL = current candle ATR*multiplier 
        TP = 1.5* (entry - sl)"""

    #fetch columns from data
    atr = data[f'ATR({ATR_period})']
    candle_2_condition = data['candle_2_condition']
    ema_bias = data['ema_bias']

    #add TP, SL, and stop price column to dataframe 
    data['take_profit_1'] = 0.00 #trade values on mt5 must be float 
    data['take_profit_2'] = 0.00
    data['stop_price'] = 0.00
    data['stop_loss'] = 0.00
    data['place_trade']= False


    for i in range(len(data)):
        #strategy can only work after 3 candles 
        if i< 3:
            pass
        else:

            #BUYS
            if ((ema_bias[i] == True) & (ema_cross_candle[i] == True) & (candle_2_condition[i] == True) ):
                data.loc[i,'stop_price'] = close[i]
                data.loc[i,'stop_loss']  = ema_short[i]-(atr[i]*1.0)
                data.loc[i,'take_profit_1']= data.loc[i,'stop_price']+abs((close[i])-(ema_short[i]-(atr[i]*1.0)))*2.5#2x SL
                data.loc[i,'take_profit_2']= data.loc[i,'stop_price']+abs((close[i])-(ema_short[i]-(atr[i]*1.0)))*3.5#4x SL
                data.loc[i,'place_trade']= True
            
            #SELLS
            elif ((ema_bias[i] == False) &(ema_cross_candle[i] == False) & (candle_2_condition[i] == False)):
                data.loc[i,'stop_price'] = close[i]
                data.loc[i,'stop_loss']  = ema_short[i]+(atr[i]*1.0)
                data.loc[i,'take_profit_1']= data.loc[i,'stop_price']-abs((close[i])-(ema_short[i]+(atr[i]*1.0)))*2.5#2x SL
                data.loc[i,'take_profit_2']= data.loc[i,'stop_price']-abs((close[i])-(ema_short[i]+(atr[i]*1.0)))*3.5#4x SL
                data.loc[i,'place_trade']= True

    #drop rows not needed
    #data = data.drop(columns=f'EMA_{ema_period_short}')
    #data = data.drop(columns=f'RSI_{3}')
    #data = data.drop(columns='upper_band')
    #data = data.drop(columns='middle_band')
    #data = data.drop(columns='lower_band')
    data = data.drop(columns=f'ATR({ATR_period})')
    #data = data.drop(columns='time')
    data = data.drop(columns='tick_volume')
    #data = data.drop(columns='spread')
    data = data.drop(columns='real_volume')
    #data = data.drop(columns='candle_cross_ema')
    #data = data.drop(columns='rsi_overbought')
    #data = data.drop(columns='BBand')
    #data = data.drop(columns='is_reversal_candle')

    #return data
    return data




    
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
        comment_string = f'Mean_Reversion_Strategy_{symbol}' #as to be consistent with other definitions through out project

        #cancel orders related to symbol and strategy 
        """ mt5_lib.cancel_filtered_orders(
            symbol=symbol,
            comment=comment_string
        ) """
        #Trade strategy 
        data = trend_following_strategy(
            symbol=symbol,
            timeframe=timeframe,
            balance=2000,
            ) 
        if data:
            print(f'Trade signal detected. Mean reversion strategy 1 trade placed successfully on {symbol}:{timeframe} ')      
        else:
            print(f'No trade signal detected for {symbol}')


    


