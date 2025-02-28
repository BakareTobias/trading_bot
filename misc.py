import sys
import time
import http.client as httplib
import os
import json 
import mt5_lib


import os
import sys
import json

def get_project_settings():
    """ 
    Function to import settings from settings.json
    Returns: settings as a dict object
    """
    # Determine the correct base path
    if getattr(sys, 'frozen', False):  # Running as .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    import_filepath = os.path.join(base_path, "settings.json")

    # Check if path exists
    if os.path.exists(import_filepath):
        # Open and read the JSON file
        with open(import_filepath, "r") as f:
            project_settings = json.load(f)
        return project_settings
    else:
        raise ImportError(f"settings.json does not exist at: {import_filepath}")



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
    


# function to check internet connectivity
def checkInternetHttplib(url="www.google.com",timeout=3):
    """ function that checks internet connection
     param: url - string of rl to use as test site. google by default
            timeout - int of how long to wait before timeout default =3 """
    connection = httplib.HTTPConnection(url,timeout=timeout)
    try:
        # only header requested for fast operation
        connection.request("HEAD", "/")
        connection.close()  # connection closed
        
        return True
    except Exception as e:
        raise Exception(f'Internet connection failed:{e}')


def print_sleeping(sleep=1):
    """ function that  handles the print sleeping
     only shows tha last 5 lines """
    last_messages = []

    while True:
        last_messages.append("No new candle. Sleeping...")
        if len(last_messages) >3:
            last_messages.pop(0)
        
        # Move the cursor up as many lines as the current number of messages,
        # then clear each line and reprint the messages.
        sys.stdout.write("\033[{}F".format(len(last_messages)))
        for message in last_messages:
            # Clear the current line and print the message.
            sys.stdout.write("\033[K" + message + "\n")
        sys.stdout.flush()
        
        time.sleep(sleep)