import time
import pandas
#Import self made custom libraries
import misc
import mt5_lib
import mean_reversion_strategy_1
import trend_following_1
import ema_cross_strategy
import telegram_lib





#Main Function
if __name__ == '__main__':
    print("Lets build!")
    #check internet connection
    misc.checkInternetHttplib()

    #format how columns apear using pandas
    pandas.set_option('display.max_columns', None)
    #pandas.set_option('display.max_rows', None)  # or a large number like 5000
    #pandas.set_option('display.width', None)

    #variable to store settings.json filepath
    settings_filepath = "settings.json"    

    #get  import filepath
    project_settings = misc.get_project_settings(import_filepath=settings_filepath)

    # startup procedure
    startup = misc.start_up(project_settings=project_settings)
    
    ###CHECK FOR NU CANDLE CODE
    #if startup successful, start trading while loop
    if startup:
        #set a variable for the current time 
        current_time = 0
        #set a variable for previous time 
        previous_time = 0
        ##by comparing the current and previous time we cand etermine when a new candle is formed 

        #start while loop; #exit loop if Ctrl+C is pressed
        try:
            while 1:
                #get a value for current time. [using BTCUSD as it trads 24/7]
                time_candle = mt5_lib.get_candlesticks(
                    symbol='BTCUSD.cfd',
                    timeframe=project_settings['mt5']['timeframe'][0],
                    number_of_candles=1
                )
                #extract time value from time_candle and assign to current time
                current_time = time_candle['time'][0]
                #compare current_time to previous_time
                if current_time != previous_time:#new candle has occured; proceed with strategy
                    print('New candle! Lets trade')

                    #update previous_time with current_time value
                    previous_time = current_time

                    strategy = ema_cross_strategy.run_strategy(project_settings)
                    
                    
                else: #no new candle has been formed
                    misc.print_sleeping()


                    time.sleep(30)#makes system more stable, reduces cpu overhead from constant querying
        except KeyboardInterrupt: #exit loop if Ctrl+C is pressed
            pass    
