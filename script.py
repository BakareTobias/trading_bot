import datetime
import time
import pandas
#Import self made custom libraries
import misc
import mt5_lib
import ema_cross_strategy





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
    project_settings = misc.get_project_settings()

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
                #check internet connection
                misc.checkInternetHttplib()
                #get a value for current time. [using BTCUSD as it trads 24/7]
                time_candle = mt5_lib.get_candlesticks(
                    symbol='BTCUSD.0',
                    timeframe=project_settings['mt5']['timeframe'][0],
                    number_of_candles=1
                )
                #extract time value from time_candle and assign to current time
                current_time = time_candle['time'][0]
                
                #convert from unix epoch to standard time
                current_time =  pandas.to_datetime(current_time, unit='s', utc=True)
                
                current_time = current_time.tz_convert("Etc/GMT-1")  # Convert to UTC-1


                #shorten from 2025-02-07 00:00:00 +00:00 to 25-02-07 00:00
                current_time = current_time.strftime("%y-%m-%d %H:%M")
                
               
                #compare current_time to previous_time
                if current_time != previous_time:#new candle has occured; proceed with strategy
                   
                    print(f'New M15 candle: {current_time}')

                    #update previous_time with current_time value
                    previous_time = current_time

                    strategy = ema_cross_strategy.run_strategy(project_settings)
                    
                    
                else: #no new candle has been formed

                    #check how many minutes till next 15 minute candle, and wait that long before checking again
                    now = datetime.datetime.now()
                    minutes = now.minute
                    seconds = now.second
                    
                    #calculate time till next candle
                    wait_time = (15-(minutes % 15)) * 60 - seconds

                    if wait_time > 0:
                        time.sleep(wait_time)

                    time.sleep(3)#wait extra 3 seconds to allow candle fully form
        except KeyboardInterrupt: #exit loop if Ctrl+C is pressed
            pass    
