import talib
import mt5_lib
import script

project_settings = script.get_project_settings('settings.json')
candles = mt5_lib.get_candlesticks(
    symbol=project_settings['mt5']['symbols'][0],
    timeframe=project_settings['mt5']['timeframe'],
    number_of_candles=1000
)

print(candles)

"""     for symbol in symbols:
        candlesticks = mt5_lib.get_candlesticks(
            symbol=symbol,
            timeframe= project_settings['mt5']['timeframe'],
            number_of_candles= 1000
        )
        print(candlesticks)

    #calculate an EMA 20, 50, 200
    ema_50 = indicator_lib.calc_custom_ema(dataframe=candlesticks, ema_size=50)#return dtafrme with new ema column

    ema_20 = indicator_lib.calc_custom_ema(dataframe=ema_50, ema_size=20)

    ema_200 = indicator_lib.calc_custom_ema(dataframe=ema_20,ema_size=200)

    print(ema_200) """
""" 
#calculate an EMA 20, 50, 200
    ema_50 = indicator_lib.calc_custom_ema(dataframe=candlesticks, ema_size=50)#return dtafrme with new ema column

    ema_20 = indicator_lib.calc_custom_ema(dataframe=ema_50, ema_size=20)

    ema_200 = indicator_lib.calc_custom_ema(dataframe=ema_20,ema_size=200)

    #ema_30 = indicator_lib.calc_custom_ema(dataframe=ema_200,ema_size=30)

    #print(ema_200)

    #detect EMA crosses between 50 and 200
    ema_cross = indicator_lib.ema_cross_calculator(
        dataframe=ema_200,
        ema_one=50,
        ema_two=200
    )
    #print(ema_cross)

    #extract only true values from EMA cross table
    ema_cross_true = ema_cross[ema_cross['ema_cross'] == True]
    print(ema_cross_true) """