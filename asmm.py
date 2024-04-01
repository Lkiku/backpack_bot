import requests
import time
import base64
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlencode
from dotenv import load_dotenv
import os
import logging
import math
from bpx import BpxClient


SYMBOL = 'RENDER_USDC'
BID_SPREAD = 0.002  # Spread for bid orders, adjust as needed
ASK_SPREAD = 0.002  # Spread for ask orders, adjust as needed
ORDER_REFRESH_TIME = 60  # Time in seconds to refresh orders
POSITION_SIZE = 1.8 #In RENDER

load_dotenv()
API_KEY = os.getenv("API_KEY")
encoded_private_key = os.getenv("API_SECRET")


# Setup logging
logging.basicConfig(filename='market_maker.log', level=logging.INFO, format='%(asctime)s %(message)s')

def log_to_console_and_file(message):
    print(message)
    logging.info(message)

# The total value of the USDC and symbol assets
def total_value_of_USDC_and_symbol(symbol):
    client = BpxClient(API_KEY, encoded_private_key)
    balances = client.balances()

    real_symbol = symbol.split('_')[0]
    symbol_balances = float(balances[real_symbol]['available']) + float(balances[real_symbol]['locked'])  
    USDC_balances = float(balances['USDC']['available']) + float(balances['USDC']['locked'])
    
    log_to_console_and_file(f'{real_symbol}: {symbol_balances}')
    log_to_console_and_file(f'USDC: {USDC_balances}')

    symbol_price = float(client.Ticker(symbol)['lastPrice'])
    log_to_console_and_file(f'{real_symbol} price: {symbol_price}')
    # The total value of the USDC and RENDER assets
    total_value = USDC_balances + symbol_balances * symbol_price
    log_to_console_and_file(f'Total value: {total_value}')


def place_order(client, symbol, side, price, size):
    # Load JSON data from the file
    with open('market.json', 'r') as f:
        market_data = json.load(f)

    # Get the market info for the current MARKET symbol
    market_info = next((market for market in market_data if market['symbol'] == symbol), None)
    if market_info is None:
        log_to_console_and_file(f"Error: {symbol} not found in the market data.")
        return None

    # Get the tick size and step size from the market info
    tick_size = market_info['filters']['price']['tickSize']
    step_size = market_info['filters']['quantity']['stepSize']

   # Round the price and quantity based on the tick size and step size
    rounded_price = round(float(price), int(-1 * math.log10(float(tick_size))))
    rounded_quantity = round(float(size), int(-1 * math.log10(float(step_size))))
    
    order_data = client.orderExecute(symbol=symbol, side=side, orderType='Limit', quantity=str(rounded_quantity), price=str(rounded_price))

    return order_data


def get_market_price(client, symbol):
    data = client.Ticker(symbol)

    # Ensure the necessary keys are present in the response
    if 'lastPrice' in data:
        # Using 'lastPrice' as the market price
        return float(data['lastPrice'])
    elif 'high' in data and 'low' in data:
        # Alternatively, calculate the mid-price as the average of 'high' and 'low'
        high_price = float(data['high'])
        low_price = float(data['low'])
        return (high_price + low_price) / 2
    else:
        print("Unexpected response structure:", data)
        return None  # Or handle as appropriate


def market_maker_cycle(client, symbol):
    mid_price = get_market_price(client, symbol)
    bid_price = mid_price * (1 - BID_SPREAD)
    ask_price = mid_price * (1 + ASK_SPREAD)

    print(f"Placing new orders. Mid price: {mid_price}, Bid price: {bid_price}, Ask price: {ask_price}")
    
    # Cancel all existing orders before placing new ones
    client.cancelAllOrders(symbol)

    # Load JSON data from the file
    with open('market.json', 'r') as f:
        market_data = json.load(f)

    # Check if the MARKET symbol exists in the JSON data
    market_info = next((market for market in market_data if market['symbol'] == symbol), None)
    if market_info is None:
        log_to_console_and_file(f"Error: {symbol} not found in the market data.")
        return
    
    # Check if the POSITION_SIZE meets the minimum quantity requirement
    min_quantity = market_info['filters']['quantity']['minQuantity']
    if POSITION_SIZE < float(min_quantity):
        log_to_console_and_file(f"Error: POSITION_SIZE {POSITION_SIZE} is less than the minimum quantity {min_quantity} for {MARKET}.")
        return

    try:
        bid_order = place_order(client, symbol, 'Bid', bid_price, POSITION_SIZE)
    except Exception as e:
        log_to_console_and_file(f"Error placing bid order: {str(e)}")

    try:
        ask_order = place_order(client, symbol, 'Ask', ask_price, POSITION_SIZE)
    except Exception as e:
        log_to_console_and_file(f"Error placing ask order: {str(e)}")

    print(f"Placed orders: {bid_order} {ask_order}")


def main():
    # client = BpxClient(API_KEY, encoded_private_key)
    # print(get_market_price(client, SYMBOL))
    while True:
        # market_maker_cycle()
        total_value_of_USDC_and_symbol(SYMBOL)
        time.sleep(ORDER_REFRESH_TIME)

if __name__ == '__main__':
    main()