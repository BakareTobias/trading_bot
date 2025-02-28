#LIBRARY FOR IDENTIFYING CANDLESTICK TYPES AND CANDLESTICK PATTERNS

#function to spot reversal candles
#reversal candles at support also apply at resistance
def is_reversal(data):
    """Function to identify a reversal candle
        conditions for a reversal candle 
        candle wick range is at least 1.5x of body i.e abs[high - low] >= abs[open - close] * 1.5
        
        param: data object of price info
        
        returns: data object of price info with a row"""
    
    #extract open,close,high,low columns from data object
    open = data['open']
    close = data['close']
    high = data['high']
    low = data['low']

    #create reversal_candle column, default to 0
    data['is_reversal_candle'] = None

    #loop through data object
    for i in range(len(data)):
        #if wick range is at least 1.5x of body
        if abs(high[i] - low[i]) >= (abs(open[i] - close[i]) * 1.5):
            #and candle body is <= 0.4 of candle range
            if abs(open[i]-close[i]) <= (abs(high[i] - low[i]) * 0.4):
                #assign true if reversal candle
                data.loc[i, "is_reversal_candle"]  = True
            else:
                data.loc[i, "is_reversal_candle"]  = False
        else:
                data.loc[i, "is_reversal_candle"]  = False
    return data