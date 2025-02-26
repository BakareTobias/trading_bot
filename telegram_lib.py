import requests
import misc
#variable to store settings.json filepath
settings_filepath = "settings.json"

project_settings = misc.get_project_settings(import_filepath=settings_filepath)

# Replace with your bot token and chat ID
BOT_TOKEN = project_settings['telegram_bot']['bot_token']
CHAT_ID = project_settings['telegram_bot']['chat_id']

def send_telegram_message(stop_price, stop_loss, take_profit, lot_size,  comment):
    """
    Sends a message to the configured Telegram chat.
    param:   stop_price - float of stop price
            stop_loss - float of stop loss
            take_pprofit - float of take profit 
            lot_size - float of lot size
            comment - string of strategy and pair being traded
    """
    #determine if buy or sell
    if stop_price > stop_loss:
        order_type = 'BUY'
    elif stop_price < stop_loss:
        order_type = 'SELL'

    #calculate RR
    RR = (take_profit-stop_price)/(stop_loss-stop_price)
    RR = abs(RR)
    message =(f'''
    {comment}
    Order Type  : {order_type}
    Entry       : {stop_price}
    Lot Size    : {lot_size}
    Stop Loss   : {stop_loss}
    Take Profit : {take_profit}
    RR          : {RR}
            ''')
    

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.text}")

# Example usage
