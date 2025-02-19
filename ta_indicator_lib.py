import pandas
import talib
import numpy as np

#define a function to create custom EMA of any size using TALIB
def calc_ema(dataframe, ema_size):
    """ fucntion to make an EMA of any size, uses TA-Lib 
    recommended to keep dataframe size < 1000 rows to preserve speed
    param:  dataframe object of symbol price data to apply ema to, 
            ema_size [integer of EMA size]
    return: dataframe object with EMA column """

    #create name of column to be added 
    ema_name = 'EMA_'+ str(ema_size)

    #make copy of dataframe close prices(and convert to numpy array)
    price_close = dataframe['close'].values

    #generate EMA for price_close values
    ema_values = talib.EMA(price_close,ema_size)

    #convert ema_values from numpy to dataframe(pandas)
    ema_values = pandas.DataFrame(ema_values,columns=[ema_name])

    #filter through ema_values and replace any NaN with 0
    ema_values = ema_values.fillna(0)

    #add ema_values column to the dataframe 
    dataframe[ema_name] = ema_values

    #at end of functiion return completed dataframe to user 
    return dataframe

#function to calculate an EMA cross 
def ema_cross_calculator(dataframe, ema_one, ema_two ):
    """ 
     function to create 2 specified EMA
             and calculate/detect an EMA cross event 
    param: dataframe object 
            ema_one - integer of EMA 1 size 
            ema_two - integer of EMA 2 size
    return: dataframe with cross events """

    #check that EMA are not the same size
    if ema_two == ema_one:
        raise ValueError('Both EMA should not be equal')

    #calculate EMA one
    dataframe = calc_ema(dataframe,ema_one)
    #calculate EMA two 
    dataframe = calc_ema(dataframe,ema_two)

    ema_one_column = 'EMA_' + str(ema_one)
    ema_two_column = 'EMA_' + str(ema_two)

    #create a position column - True if EMA smol is above EMA big
    dataframe['position'] = dataframe[ema_one_column]> dataframe[ema_two_column]
    #create a preposition column - shifts position column down a row to compare current value to previous value
    dataframe['pre_position'] = dataframe['position'].shift(1)

    #drop and NA values 
    dataframe.dropna(inplace = True)

    #define the crossover - not comparing actual ema values. change in boolean indicates a cross of values; outputs true
    dataframe['ema_cross'] = np.where((dataframe['position'] == dataframe['pre_position']) , False,True)

    #drop the position and preposition column(not necessary beyond this point)
    dataframe = dataframe.drop(columns= 'position')
    dataframe = dataframe.drop(columns= 'pre_position')

    #return dataframe 
    return dataframe

def rsi(dataframe,period=14):
    """ function to calculate RSI and add it to the dataframe object 
        param:  dataframe object of price
                period - integer of RSI period(default value 14)
                
        return: dataframe object"""
    

    #create name of column to be added 
    rsi_name = 'RSI_'+ str(period)

    #make copy of dataframe close prices(and convert to numpy array)
    price_close = dataframe['close'].values

    #generate RSI for price_close values
    rsi_values = talib.RSI(price_close,timeperiod=period)

    #convert rsi_values from numpy to dataframe(pandas)
    rsi_values = pandas.DataFrame(rsi_values,columns=[rsi_name])

    #replace NaN values with 0
    rsi_values = rsi_values.fillna(0)

    #add ema_values column to the dataframe 
    dataframe[rsi_name] = rsi_values

    #at end of functiion return completed dataframe to user 
    return dataframe

def BBands(dataframe,period=20):
    """ function that creates BBands for a dataframe object
        param:  dataframe object
                period - integer(default value 20)

        
        return:  dataframe object with BBands"""
    
    #make copy of dataframe close prices(and convert to numpy array)
    price_close = dataframe['close'].values

    #BBands values(std devs) do not need to be adjusted much so i am declaring them in here
    upperband, middleband, lowerband = talib.BBANDS(
        real=price_close,
        timeperiod=period,
        nbdevup=2,#std dev upper
        nbdevdn=2,#std dev lower
        matype=0  #MA type. 0=SMA 1=EMA
    )

    #convert upper band, middle band, lower band back to pandas
    upperband = pandas.DataFrame(upperband,columns=['upper_BBand'])
    middleband = pandas.DataFrame(middleband,columns=['middle_BBand'])
    lowerband = pandas.DataFrame(lowerband,columns=['lower_BBand'])

    #remove null values
    upperband = upperband.fillna(0)
    middleband = middleband.fillna(0)
    lowerband = lowerband.fillna(0)

    #insert upper, middle and lower band into dataframe
    dataframe['upper_band'] = upperband
    dataframe['middle_band']= middleband
    dataframe['lower_band'] = lowerband

    return dataframe

def ATR(dataframe,period=14):
    """ function to calculate ATR for a period
    param:  dataframe object
            period - integer (default value = 14) """
    
    #make copy of dataframe high, low & close prices(and convert to numpy array)
    price_high = dataframe['high'].values
    price_low = dataframe['low'].values
    price_close = dataframe['close'].values
    

    atr = talib.ATR(
        high=price_high,
        low=price_low,
        close=price_close,
        timeperiod=period
    )

    #convert back to pandas dataframe 
    atr = pandas.DataFrame(atr,columns=[f'ATR'])

    #remove null values
    atr = atr.fillna(0)

    #add atr column to dataframe 
    dataframe[f'ATR({period})'] = atr

    return dataframe


def ADX(dataframe,period=14):
    """ function to calculate ADX for a period >25 indicate strong trend, <20 -> weak trend
    param:  dataframe object
            period - integer (default value = 14) """
    
    #make copy of dataframe high, low & close prices(and convert to numpy array)
    price_high = dataframe['high'].values
    price_low = dataframe['low'].values
    price_close = dataframe['close'].values
    

    atr = talib.ADX(
        high=price_high,
        low=price_low,
        close=price_close,
        timeperiod=period
    )

    #convert back to pandas dataframe 
    atr = pandas.DataFrame(atr,columns=[f'ADX_{period}'])

    #remove null values
    atr = atr.fillna(0)

    #add atr column to dataframe 
    dataframe[f'ADX_{period}'] = atr

    return dataframe

