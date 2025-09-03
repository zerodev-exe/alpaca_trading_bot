import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

STOCKS_URL = "https://data.alpaca.markets/v1beta1/screener/stocks/movers?top=15"

CRYPTO_URL = "https://data.alpaca.markets/v1beta1/screener/crypto/movers?top=15"

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

def get_top_stocks_gainers():
    response = requests.get(STOCKS_URL, headers=HEADERS)
    data = response.json()

    gainers = data['gainers']
    losers = data['losers']

    print("\nTop Gainers:")
    print("-----------")
    for gainer in gainers:
        print(f"Symbol: {gainer['symbol']:<10} Change: {gainer['percent_change']:>.2f}%  Price: ${gainer['price']:.2f}")

    # print("\nTop Losers:")
    # print("----------")
    # for loser in losers:
    #     print(f"Symbol: {loser['symbol']:<10} Change: {loser['percent_change']:>6.2f}%  Price: ${loser['price']:.2f}")

    return gainers

def get_top_crypto_gainers():
    response = requests.get(CRYPTO_URL, headers=HEADERS)
    data = response.json()

    gainers = data['gainers']
    losers = data['losers']

    print("\nTop Gainers:")
    print("-----------")
    for gainer in gainers:
        print(f"Symbol: {gainer['symbol']:<10} Change: {gainer['percent_change']:>.2f}%  Price: ${gainer['price']:.2f}")

    # print("\nTop Losers:")
    # print("----------")
    # for loser in losers:
    #     print(f"Symbol: {loser['symbol']:<10} Change: {loser['percent_change']:>6.2f}%  Price: ${loser['price']:.2f}")

    return gainers

if __name__ == "__main__":
    get_top_crypto_gainers()
    get_top_stocks_gainers()