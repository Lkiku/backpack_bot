import os
import base64
import json
import time
import requests
from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlencode
from dotenv import load_dotenv

class BpxClient:
    def __init__(self, api_key, api_secret):
        self.debug = False
        self.proxies = {
            'http': '',
            'https': ''
        }
        self.window = 5000
        self.url = 'https://api.backpack.exchange/'

        self.api_key = api_key
        self.api_secret = api_secret
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(api_secret)
        )

    # capital
    def balances(self):
        return requests.get(url=f'{self.url}api/v1/capital', proxies=self.proxies,
                            headers=self.sign('balanceQuery', {})).json()

    def deposits(self):
        return requests.get(url=f'{self.url}wapi/v1/capital/deposits', proxies=self.proxies,
                            headers=self.sign('depositQueryAll', {})).json()

    def depositAddress(self, chain: str):
        params = {'blockchain': chain}
        return requests.get(url=f'{self.url}wapi/v1/capital/deposit/address', proxies=self.proxies, params=params,
                            headers=self.sign('depositAddressQuery', params)).json()

    def withdrawals(self, limit: int, offset: int):
        params = {'limit': limit, 'offset': offset}
        return requests.get(url=f'{self.url}wapi/v1/capital/withdrawals', proxies=self.proxies, params=params,
                            headers=self.sign('withdrawalQueryAll', params)).json()

    # history
    def orderHistoryQuery(self, symbol: str, limit: int, offset: int):
        params = {'symbol': symbol, 'limit': limit, 'offset': offset}
        return requests.get(url=f'{self.url}wapi/v1/history/orders', proxies=self.proxies, params=params,
                            headers=self.sign('orderHistoryQueryAll', params)).json()

    def fillHistoryQuery(self, symbol: str, limit: int, offset: int):
        params = {'limit': limit, 'offset': offset}
        if len(symbol) > 0:
            params['symbol'] = symbol
        return requests.get(url=f'{self.url}wapi/v1/history/fills', proxies=self.proxies, params=params,
                            headers=self.sign('fillHistoryQueryAll', params)).json()

    # sign
    def sign(self, instruction: str, params: dict):
        timestamp = int(time.time() * 1000)
        params_with_instruction = {'instruction': instruction, **params}
        ordered_params = urlencode(sorted(params_with_instruction.items()))
        signing_string = f"{ordered_params}&timestamp={timestamp}&window={self.window}"
        signature_bytes = self.private_key.sign(signing_string.encode())
        encoded_signature = base64.b64encode(signature_bytes).decode()

        if self.debug:
            print(f'Waiting Sign Str: {signing_string}')
            print(f"Signature: {encoded_signature}")

        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": encoded_signature,
            "X-Timestamp": str(timestamp),
            "X-Window": str(self.window),
            "Content-Type": "application/json; charset=utf-8",
        }
        return headers

    # exexute order
    def ExeOrder(self, symbol, side, orderType, quantity, price):
        params = {
            'symbol': symbol,
            'side': side,
            'orderType': orderType,
            'quantity': quantity,
            'price': price
        }
        response = requests.post(url=f'{self.url}api/v1/order', proxies=self.proxies, data=json.dumps(params),
                             headers=self.sign('orderExecute', params))

        if response.status_code not in [200, 201, 202]:
            print(f"Error placing order, status code: {response.status_code}, response: {response.text}")
            return None

        try:
            return response.json()
        except ValueError:  # Includes JSONDecodeError
            print(f"No JSON content returned in response to place_order, status code: {response.status_code}")
            return None

    # cancel all oders 
    def cancelAllOrders(self, symbol):
        params = {'symbol': symbol}
        response = requests.delete(url=f'{self.url}api/v1/orders', proxies=self.proxies, data=json.dumps(params),
                             headers=self.sign('orderCancelAll', params))
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:  # Includes JSONDecodeError
                print(f"No JSON content returned in response to cancel_all_orders, status code: {response.status_code}")
                return None
        else:
            print(f"Error cancelling orders, status code: {response.status_code}, response: {response.text}")
            return None
    
    # public 
    def Assets():
        return requests.get(url=f'{self.url}api/v1/assets').json()


    def Markets():
        return requests.get(url=f'{self.url}api/v1/markets').json()


    def Ticker(self, symbol: str):
        return requests.get(url=f'{self.url}api/v1/ticker?symbol={symbol}').json()


    def Depth(self, symbol: str):
        return requests.get(url=f'{self.url}api/v1/depth?symbol={symbol}').json()


    # System
    def Status():
        return requests.get(url=f'{self.url}api/v1/status').json()


    def Ping():
        return requests.get(url=f'{self.url}api/v1/ping').text


    def Time():
        return requests.get(url=f'{self.url}api/v1/time').text



if __name__ == '__main__':
    SYMBOL = 'RENDER_USDC'
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    encoded_private_key = os.getenv("API_SECRET")
    client = BpxClient(API_KEY, encoded_private_key)
    balances = client.balances()
    RENDER_balances = float(balances['RENDER']['available']) + float(balances['RENDER']['locked'])
    USDC_balances = float(balances['USDC']['available']) + float(balances['USDC']['locked'])
    print(f'RENDER: {RENDER_balances}')
    print(f'USDC: {USDC_balances}')
    RENDER_price = float(client.Ticker(SYMBOL)['lastPrice'])
    print(f'RENDER price: {RENDER_price}')
    # The total value of the USDC and RENDER assets
    total_value = USDC_balances + RENDER_balances * RENDER_price
    print(f'Total value: {total_value}')
