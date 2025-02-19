import json 
import os
import pandas
#Import self made custom libraries
import  misc
import  mt5_lib
import  mean_reversion_strategy_1
import  trend_following_1
import  ema_cross_strategy
import  backtest_library

#variable to store settings.json filepath
settings_filepath = "settings.json"

#Import json
def get_project_settings(import_filepath):
    """ 
    #Functon to import settings from settings.json
    param: path to settings.json
    return: settings as a dict object
    """
    #check if path exists
    if os.path.exists(import_filepath):
        #if yes, import file path
        f = open(import_filepath, "r")
        
        #read the file 
        project_settings = json.load(f)
        
        #close file
        f.close()

        #return project settings 
        return project_settings

    else: #if it does not exist
        raise ImportError('settings.json does not exist at provided location')


def start_up(project_settings):
    """ function to manage startup rpocedures for app
     start/test symbols. ensure app working properly
      param: project settings(json file)
      return: true if start is successful, else false
        """
    #start mt5
    start_up =mt5_lib.start_mt5(project_settings=project_settings)
    if start_up:
        print('Mt5 startup successful!')
        #extract symbols from project settings
        symbols = project_settings['mt5']['symbols']

        #iterate through symbols to enable them
        for symbol in symbols:
            outcome = mt5_lib.initialize_symbol(symbol)
            if outcome is True:
                print(f'Symbol {symbol} initiated')
            else: 
                raise Exception(f'{symbol} could not be enabled')

        return True
    else:
        print('Mt5 unable to start')
        return False
    



#Main Function
if __name__ == '__main__':
    print("Lets build!")

    misc.checkInternetHttplib()

    #format how columns apear using pandas
    pandas.set_option('display.max_columns', None)
    #pandas.set_option('display.max_rows', None)  # or a large number like 5000
    #pandas.set_option('display.width', None)

    #get  import filepath
    project_settings = get_project_settings(import_filepath=settings_filepath)

    # startup procedure
    startup = start_up(project_settings=project_settings)
    
    symbol=project_settings['mt5']['symbols'][2]
    ema_one = 20
    ema_two = 50
    rsi = ema_cross_strategy.ema_cross_strategy(
        symbol=symbol,
        timeframe=project_settings['mt5']['timeframe'],
        ema_one= ema_one,
        ema_two= ema_two,
        balance=2000,
        amount_to_risk=20)
 


    rsi.to_csv(f"{symbol}_{ema_one}_{ema_two}")

    backtest_results = backtest_library.backtest_data(
        symbol=symbol,
        balance=2000,
        amount_to_risk=20,
        test_period=9000,
        ema_one=ema_one,
        ema_two=ema_two
    )

    print(f"BACKTESTING RESULTS:{symbol}")
    for key in backtest_results:
        print(f"{key}: {backtest_results[key]}")

""" 
#Main Function
if __name__ == '__main__':
    print("Lets build!")
    
    misc.checkInternetHttplib()

    # Format how columns appear using pandas
    pandas.set_option('display.max_columns', None)
    #pandas.set_option('display.max_rows', None)
    #pandas.set_option('display.width', None)

    # Get import filepath settings
    project_settings = get_project_settings(import_filepath=settings_filepath)

    # Startup procedure
    startup = start_up(project_settings=project_settings)
    
    symbol = project_settings['mt5']['symbols'][4]
    
    # Variables to track the best EMA combination and highest final balance.
    best_balance = -float("inf")
    best_ema_one = None
    best_ema_two = None

    # Loop through desired EMA values.
    # (Modify these ranges as needed for your testing.)
    for ema_one in range(40, 80, 5):  #short EMA
        for ema_two in range(160, 230, 5):  # long EMA
            # Optionally, skip if ema_two isn't greater than ema_one.
            if ema_two <= ema_one:
                continue

            print(f"Testing EMA combination: EMA1 = {ema_one}, EMA2 = {ema_two}")

            # Generate the strategy signals using the current EMA combination.
            rsi = ema_cross_strategy.ema_cross_strategy(
                symbol=symbol,
                timeframe=project_settings['mt5']['timeframe'],
                ema_one=ema_one,
                ema_two=ema_two,
                balance=2000,
                amount_to_risk=20
            )
            
            # Save the signals file (optional).
            rsi.to_csv(f"{symbol}_{ema_one}_{ema_two}")

            # Run the backtest using the current settings.
            backtest_results = backtest_library.backtest_data(
                symbol=symbol,
                balance=2000,
                amount_to_risk=20,
                test_period=10000,
                ema_one=ema_one,
                ema_two=ema_two
            )

            final_balance = backtest_results.get("Final Balance", 0)
            print(f"Backtesting results for EMA1 = {ema_one}, EMA2 = {ema_two}: Final Balance = {final_balance}")

            # Check if this combination gives a new high final balance.
            if final_balance > best_balance:
                best_balance = final_balance
                best_ema_one = ema_one
                best_ema_two = ema_two

    print("Best EMA combination:")
    print(f"EMA1 = {best_ema_one}, EMA2 = {best_ema_two}, Final Balance = {best_balance}")
 """