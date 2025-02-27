import requests
import misc
#variable to store settings.json filepath
settings_filepath = "settings.json"

project_settings = misc.get_project_settings(import_filepath=settings_filepath)



def send_telegram_message(stop_price, stop_loss, take_profit, lot_size,  comment,symbol):
    """
    Sends a message to the configured Telegram chat.
    param:   stop_price - float of stop price
            stop_loss - float of stop loss
            take_pprofit - float of take profit 
            lot_size - float of lot size
            comment - string of strategy and pair being traded
            symbol - string of symbol to trade
    """
    #determine if buy or sell
    if stop_price > stop_loss:
        order_type = 'BUY'
    elif stop_price < stop_loss:
        order_type = 'SELL'

    #calculate RR
    RR = (take_profit-stop_price)/(stop_loss-stop_price)
    RR = round(abs(RR),2)
    message =(f'''
                Trade Signal: {comment}
                Order Type  : {order_type}
                Entry       : {stop_price}
                Lot Size    : {lot_size}
                Stop Loss   : {stop_loss}
                Take Profit : {take_profit}
                RR          : {RR}
            ''')
    

    if ('JPY' in symbol) or ('USD' in symbol): #forex pairs
        #TobiasBot details
        BOT_TOKEN = project_settings['telegram_bot_forex']['bot_token']
        CHAT_ID = project_settings['telegram_bot_forex']['chat_id']
    else: #DERIV PAIRS
        #TobiasDeriv details
        BOT_TOKEN = project_settings['telegram_bot_deriv']['bot_token']
        CHAT_ID = project_settings['telegram_bot_deriv']['chat_id']

    
    for chat in CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat,
            "text": message
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message: {response.text}")

# Example usage
