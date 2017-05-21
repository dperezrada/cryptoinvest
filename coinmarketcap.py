import pandas as pd
import numpy as np


class Coinmarketcap(object):
    @staticmethod
    def load_data(source_datapath):
        by_date_data = {}
        all_data = pd.read_csv(source_datapath, sep='\t', header=0, encoding="utf-8", dtype={'Market Cap': np.float64, 'Total Market Cap': np.float64})
        all_data["Market Cap Share"] = all_data["Market Cap"] / all_data["Total Market Cap"]
        for index, value in all_data['Date'].items():
            date = value
            symbol = all_data['Symbol'][index]
            price = all_data['Price'][index]
            marketcap = all_data['Market Cap'][index]
            position = all_data['Pos'][index]
            if by_date_data.get(date) is None:
                by_date_data[date] = {'symbols': {}, 'positions': []}
            by_date_data[date]['symbols'][symbol] = {
                "price": price,
                "marketcap": marketcap
            }
            by_date_data[date]['positions'].append([symbol, position])
        for date in by_date_data.keys():
            by_date_data[date]['positions'] = [el[0] for el in sorted(by_date_data[date]['positions'], key=lambda x: x[1])]
        return all_data, by_date_data

    def __init__(self, source_datapath):
        self.data, self.by_date_data = self.load_data(source_datapath)

    def get_coin_price(self, date, coin_symbol):
        try:
            return float(self.by_date_data[date]['symbols'][coin_symbol]['price'])
        except:
            # print("ERROR: price not found for coin %s (%s)" % (coin_symbol, date))
            return 0

    def coins_to_usd(self, date, coins):
        amount_usd = 0
        for coin_symbol, amount in coins.items():
            coin_usd = self.get_coin_price(date, coin_symbol)
            amount_usd += amount * coin_usd
        return amount_usd

    def buy_coin(self, date, symbol, amount_usd):
        try:
            return amount_usd / self.get_coin_price(date, symbol)
        except:
            print(date, symbol, amount_usd)
            raise Exception("")

    def buy_coins(self, date, symbols, amount_usd, strategy="even"):
        symbols_length = len(symbols)
        coins = {}
        if strategy == "market_cap":
            coins_market_cap = {}
            total_market_cap = 0
            for coin_symbol in symbols:
                coins_market_cap[coin_symbol] = self.get_coin_market_cap(date, coin_symbol)
                total_market_cap += coins_market_cap[coin_symbol]
        for coin_symbol in symbols:
            coin_amount_usd = 0
            if strategy == "even":
                coin_amount_usd = (amount_usd / symbols_length)
            elif strategy == "market_cap":
                coin_amount_usd = (amount_usd * (coins_market_cap[coin_symbol] / total_market_cap))
            coins[coin_symbol] = self.buy_coin(date, coin_symbol, coin_amount_usd)
        return coins

    def sell_coins(self, date, coins):
        amount_usd = 0
        for coin_symbol, coin_amount in coins.items():
            coin_price = self.get_coin_price(date, coin_symbol)
            amount_usd += coin_price * coin_amount
        return amount_usd

    def get_coin_market_cap(self, date, coin_symbol):
        return float(self.by_date_data[date]['symbols'][coin_symbol]['marketcap'])

    def get_positions_range(self, date, first_position, last_position):
        return self.by_date_data[date]['positions'][first_position - 1:last_position]

    def dates(self):
        return sorted(self.by_date_data.keys())

    def print_returns(self, initial_amount, initial_date, final_amount, final_date):
        print("%s: %s USD" % (initial_date, round(initial_amount, 2)))
        print("%s: %s USD" % (final_date, round(final_amount, 2)))
        print("----------")
        print("%sX" % round(final_amount / initial_amount, 1))
