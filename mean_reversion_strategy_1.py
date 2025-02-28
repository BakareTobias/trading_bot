import mt5_lib
import ta_indicator_lib
import helper_library
import candlestick_patterns_lib

#MEAN REVERSION STRATEGY 1
#INDICATORS: BOLLINGER BANDS, RSI, EMA, ATR
#RULES(Long)
#Conditions:1. Price must be above EMA(200)[trend following] 
#           2. 1H,4H,1D
#           3. Risk 0.8% per trade
#
#ENTRY: Price equal lower BB & RSI<=oversold
#TP 1  : Middle BB
#TP 2  : Upper BB
#SL    : 1.5 x ATR
#RULES(Short)
#Conditions:1. Price must be below EMA(200)[trend following] 
#           
#
#ENTRY: Price equal higher BB & RSI>=overbought
#TP 1  : Middle BB
#TP 2  : Lower BB
#SL    : 1.5 x ATR

#v1.1 2/14/25. Adding ADX indicator. same conditions AND ADX should be less than 20 

#indicator periods and oversold parameters, for easily manipulating trade parameters
rsi_period = 3
rsi_overbought = 70
rsi_oversold = 20
ema_period = 200
ATR_period = 14
atr_multiplier = 0.5
adx_period = 14
adx_level = 20

#function to run strategy
def mean_reversion_strategy(symbol,timeframe,balance,amount_to_risk=20):
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
        ema_period=ema_period,
        rsi_period=rsi_period,
        atr_period=ATR_period
    
    )    

    #Step 3
    data = det_trade(
        data=data
    )
    
    #Step 4
    trade_event = data.tail(1).copy( )#copy info for most recent formed candle 
    
    if trade_event['place_trade'].values:
        #Make trade requires balance, comment, amount_to_risk
        comment_string = f'Mean_Reversion_Strategy_1_{symbol}'
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

#function to backtest strategy
def mean_reversion_strategy_backtest(symbol,timeframe,test_period):
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
   
    return: data with trade parameters """

    #Step 1
    data = get_data(
        symbol=symbol,
        timeframe=timeframe,
        test_period = test_period
        
    )

    #Step 2
    data = calc_indicators(
        data=data,
        ema_period=ema_period,
        rsi_period=rsi_period,
        atr_period=ATR_period
    
    )    

    #Step 3
    data = det_trade(
        data=data
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

#Step 2: calculate indicators
def calc_indicators(data,ema_period,rsi_period,atr_period):
    """ function to calculate EMA 200, RSI 14, BBands, ATR 14
     param: data-dataframe of candle info
            ema-period 
            rsi-period
            atr-period variables ttached here to make
                        manipulation of variables easy at the top
             
    return: dataframe with updated columns """

    #Calculate EMA 
    data = ta_indicator_lib.calc_ema(data,ema_period)

    #Calculate RSI
    data = ta_indicator_lib.rsi(data,rsi_period)#period set to default 14

    #calculate BBands
    data = ta_indicator_lib.BBands(data)#period set to default 20;std set to 2

    #calculat ATR
    data = ta_indicator_lib.ATR(data,atr_period)#period set to default 14

    #calculate ADX 
    data = ta_indicator_lib.ADX(data,adx_period)


    
    #return dataframe
    return data

#Step 3: Determine trade event
def det_trade(data):
    """ Function to check if all conditions have been met 
    param: data= object of price data
            EMA_period - integer of ema period default 200
            rsi_period - integer of rsi perios default 14

    return: object of price data 
     """
###PART 1 CHECK TRADE CONDITIONS/RULES
    """ CONDITIONS
    1. Determine bias.  True if price[close]> EMA
                        False if price[close]< EMA
                         default = None
                         
    2. Determine overbought/sold. True if>= 75. 
                                    False if<= 25
                                    default = None 
    
    3. Determine BBand  True if price[high]>= UB
                        False if price[low]<= LB
                        default = None
                        
    4. Check rejection candle   True if rejection candle
                                False if not rejection candle
                                default = None
    
    v 1.1
    
    5. Check ADX                >25 -> True
                                <20 -> False
                                20-25 -> None
    """
    

    #copy data to avoid panda copy warnng 
    data = data.copy()

    #extract open,close,high,low
    open = data['open']
    close = data['close']
    high = data['high']
    low = data['low']
    ema = data[f'EMA_{ema_period}']
    rsi = data[f'RSI_{rsi_period}']
    adx = data[f'ADX_{adx_period}']
    ub = data['upper_band']  
    mb =data['middle_band']
    lb=data['lower_band']


    #iterate through dataframe and check trading conditions
    for i in range(len(data)):
        #determine bias using ema
        if close[i]> ema[i]:
            data.loc[i,'ema_bias'] = True
        elif close[i]< ema[i]:
            data.loc[i,'ema_bias'] = False
        else:
            data.loc[i,'ema_bias'] = None

        #determine overbought using rsi
        if rsi[i]>= rsi_overbought:
            data.loc[i,'rsi_overbought'] = True
        elif rsi[i]<= rsi_oversold:
            data.loc[i,'rsi_overbought'] = False
        else:
            data.loc[i,'rsi_overbought'] = None

        #determine BBand status using upper and lower bands
        if high[i]>= ub[i]:
            data.loc[i,'BBand'] = True#overbought
        elif low[i]<= lb[i]:
            data.loc[i,'BBand'] = False#oversold
        else:
            data.loc[i,'BBand'] = None#ranging aka waiting

        #determine trend strenght using ADX
        
        

    #check for rejection candle 
    data = candlestick_patterns_lib.is_reversal(data)
        

###PART 2: CALCULATE TRADE PARAMS
    """ for sells
        ema_bias == False & rsi_overbought == True &  BBand == True & is_reversal_candle == True
        entry = next candle open aka current candle close
        SL = current candle ATR*multiplier + next candle open
        TP = middleband
        

        for buys
        ema_bias == True & rsi_overbought == False &  BBand == False & is_reversal_candle == True
        entry = next candle open aka current candle close
        SL = current candle ATR*multiplier - next candle open
        TP = middleband"""

    #fetch columns from data(rsi_overbought/oversold overwrites previous values(they are not needed past this point))
    ema_bias = data['ema_bias']
    rsi_overbought_data = data['rsi_overbought']
    BBand = data['BBand']
    atr = data[f'ATR({ATR_period})']

    #add TP, SL, and stop price column to dataframe 
    data['take_profit_1'] = 0.00 #trade values on mt5 must be float 
    data['take_profit_2'] = 0.00
    data['stop_price'] = 0.00
    data['stop_loss'] = 0.00
    data['place_trade']= False


    is_reversal_candle = data['is_reversal_candle']
    for i in range(len(data)):
        #BUYS
        if ((ema_bias[i] == True) & (rsi_overbought_data[i] == False) & (BBand[i] == False) & (is_reversal_candle[i] == True) & (adx[i]<adx_level)):
            data.loc[i,'stop_price'] = close[i]
            data.loc[i,'stop_loss']  = close[i]-(atr[i]*atr_multiplier)
            data.loc[i,'take_profit_1']= mb[i]
            data.loc[i,'take_profit_2']= ub[i]
            data.loc[i,'place_trade']= True
        
        #SELLS
        elif ((ema_bias[i] == False) & (rsi_overbought_data[i] == True) & (BBand[i] == True) & (is_reversal_candle[i] == True)& (adx[i]<adx_level)):
            data.loc[i,'stop_price'] = close[i]
            data.loc[i,'stop_loss']  = (atr[i]*atr_multiplier)+close[i]
            data.loc[i,'take_profit_1']= mb[i] 
            data.loc[i,'take_profit_2']= lb[i]
            data.loc[i,'place_trade']= True

    #drop rows not needed
    data = data.drop(columns=f'EMA_{ema_period}')
    #data = data.drop(columns=f'RSI_{3}')
    data = data.drop(columns='upper_band')
    data = data.drop(columns='middle_band')
    data = data.drop(columns='lower_band')
    data = data.drop(columns=f'ATR({ATR_period})')
    data = data.drop(columns='time')
    data = data.drop(columns='tick_volume')
    #data = data.drop(columns='spread')
    data = data.drop(columns='real_volume')
    #data = data.drop(columns='ema_bias')
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
        data = mean_reversion_strategy(
            symbol=symbol,
            timeframe=timeframe,
            balance=2000,
            ) 
        if data:
            print(f'Trade signal detected. Mean reversion strategy 1 trade placed successfully on {symbol}:{timeframe} ')      
        else:
            print(f'No trade signal detected for {symbol}')


    


