import datetime
import MetaTrader5
import pandas






#function to start mt5
def start_mt5(project_settings):
    """ function to start mt5
    param: project settings: json object with username, password,server, file locations
    return: true if started, else false """

    #ensure all pramateres are in correct format 
    username =  project_settings['mt5']['username']
    username = int(username)
    password = project_settings['mt5']['password']
    server = project_settings['mt5']['Server']
    mt5pathway = project_settings['mt5']['mt5_pathway']

    #attempt to initialize(start) mt5
    mt5_init = False
    try:
        mt5_init = MetaTrader5.initialize(
            login = username,
            password = password,
            server = server,
            path = mt5pathway
            
        )
        
    #error handling
    except Exception as e:
        print(f'Error initializing MetaTrader for account: {e}')
        mt5_init = False

    #if MT5 initialized, attempt to login
    mt5_login = False
    if mt5_init: #checking if it has been initialized
        #attempt login
        try:
            mt5_login = MetaTrader5.login(
                login = username,
                password = password,
                server = server,
            )
        except Exception as e:
            print(f'Error logging into MetaTrader for account: {e}')
            mt5_login = False
    else:
        print(f'account has not been initialized')

    #return output
    if mt5_login:
        return True
    return False
        
def initialize_symbol(symbol):
    """ function to initalize a symbol on MT5(assumes accountis already initialized)
     param: raw string of symbol. [note: most brokers denote symbols differently]
      return: true if initialized, else false """
    
    #check is symbol is on broker
    #fetch all symbols, these are objects with more info than just the name
    all_symbols = MetaTrader5.symbols_get()

    #create list to store all names
    symbol_names = []

    #add all symbol names to list
    for sym in all_symbols:
        symbol_names.append(sym.name)

    #check if symbol exists
    if symbol in symbol_names:
        #try to initialize
        try:
            MetaTrader5.symbol_select(symbol, True) #arguments cannot be passed at this oints, or error will come up 
            return True
        except Exception as e:
            print(f'Error initiaalizing/enabling {symbol}. Error {e}')
            #custom error handling at some later date goes here
            return False
    else: 
        print(f'symbol {symbol} does not appear on this version of MT5 ')


#FUNCTION TO RETRIEVE CANDLE STICKS DATA FROM MT5
def get_candlesticks(symbol, timeframe,number_of_candles):
    """ function to get 50,000 candles from mt5 to bcktest. we could technically get millions of candles
     but we would need to change mt5 default settings
      param: symbol: string; timeframe:string; number of candles:integer
       return: database of candlesticks """
    
    #check that no of candles is not more than 50k
    if number_of_candles > 50000:
        raise ValueError('No more than 50k candles')
    #convert timefram to mt5 friendly format 
    mt5_timeframe = set_query_timeframe(timeframe=timeframe)

    #candles = copy rates from position
    candles = MetaTrader5.copy_rates_from_pos(symbol, mt5_timeframe, 0, number_of_candles   )#the zero candle is current candle still being formed, 

    #convert to a dataframe 
    dataframe = pandas.DataFrame(candles)

    #get copy of time column 
    time = dataframe['time'].copy()

    #convert from unix epoch to standard time
    time = pandas.to_datetime(time, unit='s', utc=True)



    #shorten from 2025-02-07 00:00:00 +00:00 to 25-02-07 00:00
    time = time.dt.strftime("%y-%m-%d %H:%M")


    #add new time column next to epoch time column
    dataframe.insert(1, 'std_time', time)

    return dataframe 


#function to place an order on MT5
def place_order(order_type, symbol, volume, stop_loss, take_profit, comment, stop_price, direct=False):
    """ function to place an order on MT5. function checks order first(best practice), then places it 
        if order check returns true 
        param:  order_type - string [buy_stop/sell_stop]
                symbol     - string of symbol to trade
                volume     - float of lot size
                stop_loss  - string/float of SL
                take_profit- string/float of TP
                stop_price - string/float of stop_price
                comment    - string of comment to indicate strategy being used to place trade  
                direct     - Boolean. defualts to false. when True, will bypassorder check
            
        return: Trade Outcome  """
   
    #make sure volume, stop_loss, stop_price, take_profit are in correct format(float)
    volume = float(volume)
    #volume can only be 2 decimal places
    ###this can mess up volume calculations for small accounts 
    volume = round(volume , 2)

    #stop loss
    stop_loss = float(stop_loss)
    #stop_loss cannot be more than 4 decimal places 
    stop_loss = round(stop_loss, 4)

    #set up order request. will be a dictionary object sent to MT5 to confirm trade 
    request = {
        'symbol' : symbol,
        'volume' : volume,
        'sl'     : stop_loss,
        'tp'     : take_profit,
        'type_time': MetaTrader5.ORDER_TIME_GTC,
        'comment': comment,

    }

    #create order type based on values 
    if order_type == 'SELL_STOP':
        #update request 
        request['type'] = MetaTrader5.ORDER_TYPE_SELL_STOP
        request['action'] = MetaTrader5.TRADE_ACTION_PENDING
        request['type_filling'] = MetaTrader5.ORDER_FILLING_RETURN
        if stop_price <= 0:
            raise ValueError('Stop price cannot be zero')
        else:
            request['price'] = stop_price
    elif order_type == 'BUY_STOP':
        #update request 
        request['type'] = MetaTrader5.ORDER_TYPE_BUY_STOP
        request['action'] = MetaTrader5.TRADE_ACTION_PENDING
        request['type_filling'] = MetaTrader5.ORDER_FILLING_RETURN
        if stop_price <= 0:
            raise ValueError('Stop price cannot be zero')
        else:
            request['price'] = stop_price
    else:
        #order type beyond program functionality is being passed
        raise ValueError(f'this function cannot handle {order_type} requests')
    
    #if direct is true, go straight to adding the error without checking 
    if direct:
        order_result = MetaTrader5.order_send(request)
        #notify based on return outcomes 
        if order_result[0] == 10009:
            print(f'Order for {symbol} successful ')
            return order_result[2]
        #notify user if Autotrading has been left on in MT5
        elif order_result[0] == 10027:
            raise Exception('turn off Algotrading on MT5 terminal ')
        else:
            print(f'Error logging order for {symbol}. Error code {order_result[0]}. Error details {order_result} /n Troubleshoot at https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes')
    else: 
        #check the order
        result = MetaTrader5.order_check(request)
        #if check passes, place the order
        if result[0] == 0:
            print(f'order check for {symbol} successful. Placing order...')
            #place the order using recursion
            place_order(
                order_type=order_type,
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment,
                stop_price=stop_price,
                direct=True
            )
        #an invalide price has been passed
        elif result[0] == 10015:
            print(f'Invalid price {stop_price} for symbol {symbol}')
        #any other error code
        else:
            print(f'Order check failed. details: {result[0]}. /n Troubleshoot at https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes')


#function to cancel an order on MT5
def cancel_order(order_number):
    """ function to cancle an order identified by an order number 
    param: integer of order nuber to be canceled
    
    return: Boolean. True = canceled False = not canceled """ 

    #create request 
    request = {
        "action": MetaTrader5.TRADE_ACTION_REMOVE,
        "order" : order_number,
        "comment": "order removed"
    }
    
    try:
        order_result = MetaTrader5.order_send(request)
        if order_result[0] == 10009:
            print(f'Order {order_number} canceled successfully')
            return True 
        else:#any other error code
            print(f'Order cancel for {order_number} failed. Error code: {order_result[0]}. /nTrouble shoot at https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes ')
            return False
    except Exception as e:
        #this reresents an issue with the MT5 Terminal. pause program till error resolved 
        print(f'Error cancelling order {order_number}. Error {e}')
        raise Exception
    
#function to retrieve all currently open/pending orders fom mt5
def get_all_open_orders():
    """ function to retrieve all open orders on MT5
     return: list of open orders  """
    
    return MetaTrader5.orders_get()

#function to retrive a filtered list of orders
def get_filtered_list_of_orders(symbol, comment):
    """ function to retrieve a filtered list of all open orders on MT5 
    params: symbol - string of symbol to filter for
            comment - string of strategy to filter for 
    
    return: filtered list of orders"""
    #retrieve list of open orders by symbol 
    open_orders_by_symbol = MetaTrader5.orders_get(symbol)
    #check if any orders were retrieved 
    if open_orders_by_symbol is None or len(open_orders_by_symbol) == 0:
        return[]
    #convert open orders into a dataframe 
    open_orders_dataframe = pandas.DataFrame(
        list(open_orders_by_symbol), 
        columns=open_orders_by_symbol[0].asdict().keys()
    )

    #from open orders dataframe, filter orders by comment 
    open_orders_dataframe = open_orders_dataframe[open_orders_dataframe['comment'] == comment]

    #create a list to store open order numbers 
    open_orders =[]

    #iterate through dataframe and add order numbers to the list 
    for order in open_orders_dataframe['ticket']:
        open_orders.append(order)

    return open_orders

#function to cancel orders based on filters
def cancel_filtered_orders(symbol,comment):
    """ function to cancel a list of filtered orders. Based on two filters: symbols and comment 
    param:  symbol - string of symbol to fliter for 
            comment- string of strategy to filter for 
    
    return: Boolean. True = successfully canceled. False = cancel failed"""
    
    #retrive list of open orders for filter 
    orders = get_filtered_list_of_orders(symbol=symbol, comment=comment)

    if len(orders) > 0:
        #iterate through and cancel 
        for order in orders:
            cancel_outcome = cancel_order(order_number=order)
            if cancel_outcome is not True: #if cancel_order fails for any reason 
                return False 
        #if for loop iterates with no errors
        return True
    else:
        return True

#function to convert a timeframe string to mt5 friendly format 
def set_query_timeframe(timeframe):
    """
    Function to implement a conversion from a user-friendly timeframe string into a MT5 friendly object. Note that the
    function implements a Pseudo switch as Python version < 3.10 do not contain 'switch' functionality.
    :param timeframe: string of the timeframe
    :return: MT5 Timeframe Object
    """
    if timeframe == "M1":
        return MetaTrader5.TIMEFRAME_M1
    elif timeframe == "M2":
        return MetaTrader5.TIMEFRAME_M2
    elif timeframe == "M3":
        return MetaTrader5.TIMEFRAME_M3
    elif timeframe == "M4":
        return MetaTrader5.TIMEFRAME_M4
    elif timeframe == "M5":
        return MetaTrader5.TIMEFRAME_M5
    elif timeframe == "M6":
        return MetaTrader5.TIMEFRAME_M6
    elif timeframe == "M10":
        return MetaTrader5.TIMEFRAME_M10
    elif timeframe == "M12":
        return MetaTrader5.TIMEFRAME_M12
    elif timeframe == "M15":
        return MetaTrader5.TIMEFRAME_M15
    elif timeframe == "M20":
        return MetaTrader5.TIMEFRAME_M20
    elif timeframe == "M30":
        return MetaTrader5.TIMEFRAME_M30
    elif timeframe == "H1":
        return MetaTrader5.TIMEFRAME_H1
    elif timeframe == "H2":
        return MetaTrader5.TIMEFRAME_H2
    elif timeframe == "H3":
        return MetaTrader5.TIMEFRAME_H3
    elif timeframe == "H4":
        return MetaTrader5.TIMEFRAME_H4
    elif timeframe == "H6":
        return MetaTrader5.TIMEFRAME_H6
    elif timeframe == "H8":
        return MetaTrader5.TIMEFRAME_H8
    elif timeframe == "H12":
        return MetaTrader5.TIMEFRAME_H12
    elif timeframe == "D1":
        return MetaTrader5.TIMEFRAME_D1
    elif timeframe == "W1":
        return MetaTrader5.TIMEFRAME_W1
    elif timeframe == "MN1":
        return MetaTrader5.TIMEFRAME_MN1
    else:
        print(f"Incorrect timeframe provided. {timeframe}")
        raise ValueError("Input the correct timeframe")



