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

load_dotenv()
API_KEY = os.getenv("API_KEY")
encoded_private_key = os.getenv("API_SECRET")

# The total value of the USDC and symbol assets
def total_value_of_USDC_and_symbol(symbol):
    client = BpxClient(API_KEY, encoded_private_key)
    balances = client.balances()

    real_symbol = symbol.split('_')[0]
    symbol_balances = float(balances[real_symbol]['available']) + float(balances[real_symbol]['locked'])  
    USDC_balances = float(balances['USDC']['available']) + float(balances['USDC']['locked'])
    
    print(f'{real_symbol}: {symbol_balances}')
    print(f'USDC: {USDC_balances}')

    symbol_price = float(client.Ticker(symbol)['lastPrice'])
    print(f'{real_symbol} price: {symbol_price}')
    # The total value of the USDC and RENDER assets
    total_value = USDC_balances + symbol_balances * symbol_price
    print(f'Total value: {total_value}')


def place_order(symbol, side, quantity, size):
    client = BpxClient(API_KEY, encoded_private_key)

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

def market_maker_cycle():
    mid_price = get_market_price()
    bid_price = mid_price * (1 - BID_SPREAD)
    ask_price = mid_price * (1 + ASK_SPREAD)



if __name__ == '__main__':
    total_value_of_USDC_and_symbol(SYMBOL)