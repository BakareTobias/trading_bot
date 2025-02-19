import numpy as np

#define a function to create custom EMA of any size
def calc_custom_ema(dataframe, ema_size):
    """ fucntion to make acustome em of any size, does not use TA-Lib 
    recommended to keep dataframe size < 1000 rows to preserve speed
    param: dataframe object of symbol price data to apply ema to, ema period[integer]
    return: """

    #create name of column to be added 
    ema_name = 'ema'+ str(ema_size)

    #create the multiplier 
    multiplier = 2/(ema_size+1)

    #calculate initial value of EMA(SMA)
    initial_mean = dataframe['close'].head(ema_size).mean()

    #iterate through dataframe and add values 
    for i in range(len(dataframe)):
        #check if i = size of EMA. if yes, then we are on initial mean
        if i == ema_size:
            dataframe.loc[i, ema_name] = initial_mean
        #if i > ema_size, calculate EMA 
        elif i>ema_size:
            ema_value = dataframe.loc[i,'close']* multiplier + dataframe.loc[i-1, ema_name]*(1-multiplier)
            dataframe.loc[i, ema_name] = ema_value
        #if i < EMA(default condition)
        else:
            dataframe.loc[i, ema_name]= 0.00

    #at end of functiion return completed dataframe to user 
    return dataframe

#function to calculate an EMA cross 
def ema_cross_calculator(dataframe, ema_one, ema_two ):
    """ 
     function to calculate/detct an EMA cross event 
    EMA column names must be in format 'ema_<value>' eg ema_20
    param: dataframe object 
            ema_one - integer of EMA 1 size 
            ema_two - integer of EMA 2 size
    return: dataframe with cross events """

    ema_one_column = 'ema' + str(ema_one)
    ema_two_column = 'ema' + str(ema_two)

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