from random import randint
import numpy as np
from collections import Counter


class InvestStrategies(object):
    def __init__(self, market, options):
        self.market = market
        self.options = options
        self.dates = self.market.dates()

        self.min_week_duration = self.options.get('min_week_duration') or 1
        self.max_week_duration = self.options.get('max_week_duration') or 52
        self.min_start_date = self.options.get('min_start_date', self.dates[0])
        self.max_end_date = self.options.get('max_end_date', self.dates[-1])

        self.min_week_index = min([index for index, date in enumerate(self.dates) if self.min_start_date <= date])
        self.max_week_index = max([index for index, date in enumerate(self.dates) if self.max_end_date >= date])

    def buy(self, amount, date):
        raise Exception("Implementation needed")

    def get_random_start_end_date(self):
        week_duration = randint(self.min_week_duration, self.max_week_duration)

        random_start_index = randint(self.min_week_index, self.max_week_index - week_duration)
        random_end_index = random_start_index + week_duration
        duration = random_end_index - random_start_index
        return duration, random_start_index, random_end_index

    def buy_top_x(self, date, amount, top_x_first_pos, top_x_last_pos, strategy, exclude=None):
        if exclude is None:
            exclude = []
        symbols_to_buy = self.market.get_positions_range(date, top_x_first_pos, top_x_last_pos)
        symbols_to_buy = [symbol for symbol in symbols_to_buy if symbol not in exclude]
        return self.market.buy_coins(date, list(symbols_to_buy), amount, strategy=strategy)

    def add_coins_list(self, coins_group):
        coins_keys = set([
            coin_key
            for coins_data in coins_group
            for coin_key in coins_data.keys()
        ])
        coins = {}
        for coins_data in coins_group:
            for coin_key in coins_keys:
                if coins_data.get(coin_key):
                    if coins.get(coin_key) is None:
                        coins[coin_key] = 0
                    coins[coin_key] += coins_data[coin_key]
        return coins

    def run_strategy(self, initial_amount, balance_x_weeks=0):
        results = {
            "min_date": "",
            "max_date": "",
            "min_duration": "",
            "max_duration": "",
            "values": [],
            "bought_coins": [],
            "raw_values": []
        }
        iterations = 0
        bought_coins = []
        for weeks_duration, start_date_index, end_date_index in self.get_all_iterations():
            if not results['max_duration'] or results['max_duration'] < weeks_duration:
                results['max_duration'] = weeks_duration
            if not results['min_duration'] or results['min_duration'] > weeks_duration:
                results['min_duration'] = weeks_duration

            if not results['min_date'] or results['min_date'] > self.dates[start_date_index]:
                results['min_date'] = self.dates[start_date_index]
            if not results['max_date'] or results['max_date'] < self.dates[end_date_index]:
                results['max_date'] = self.dates[end_date_index]

            amount = initial_amount
            if balance_x_weeks > 0:
                first_date = True
                coins = {}
                for date in self.dates[start_date_index:end_date_index:balance_x_weeks]:
                    if not first_date:
                        amount = self.market.sell_coins(date, coins)
                    else:
                        first_date = False
                    coins = self.buy(amount, date)
                    bought_coins += coins.keys()
                amount = self.market.sell_coins(date, coins)
            else:
                coins = self.buy(amount, self.dates[start_date_index])
                bought_coins += coins.keys()
                amount = self.market.sell_coins(self.dates[end_date_index], coins)

            results['raw_values'].append(
                [
                    self.dates[start_date_index],
                    self.dates[end_date_index],
                    weeks_duration,
                    round(1.0 * amount / initial_amount, 2),
                    round(100.0 * (amount / initial_amount - 1) / weeks_duration, 3)
                ]
            )
            iterations += 1

        results['iterations'] = iterations
        results['values'] = sorted([value for _, _, _, _, value in results['raw_values']])
        results['mean'] = round(np.mean(results['values']), 2)
        results['median'] = round(np.median(results['values']), 2)
        results['min_rate'] = round(np.min(results['values']), 2)
        results['max_rate'] = round(np.max(results['values']), 2)
        results['bought_coins'] = Counter(bought_coins)
        results['total_bought_coins'] = len(Counter(bought_coins))
        results['raw_values'] = sorted(results['raw_values'], key=lambda x: x[4])
        results['median_values'] = [
            values for values in results['raw_values'] if values[4] < results['median']
        ][-1]
        return results

    def print_results(self, results):
        print("\n\n%s:\n" % self.name())
        for key in [
            'min_rate', 'max_rate', 'median_values'
            # , 'total_bought_coins', 'bought_coins'
        ]:
            # TODO: refactor this
            if key == "min_rate":
                print(
                    "Min return(%s to %s) %s weeks: %sx." % (
                        results['raw_values'][0][0], results['raw_values'][0][1],
                        results['raw_values'][0][2], results['raw_values'][0][3],
                        # round(52*results['raw_values'][0][3]/results['raw_values'][0][2], 2)
                    )
                )
            elif key == "max_rate":
                print(
                    "Max return(%s to %s) %s weeks: %sx." % (
                        results['raw_values'][-1][0], results['raw_values'][-1][1],
                        results['raw_values'][-1][2], results['raw_values'][-1][3],
                        # round(52*results['raw_values'][-1][3]/results['raw_values'][-1][2], 2)
                    )
                )
            elif key == "median_values":
                print(
                    "Mean return(%s to %s) %s weeks: %sx." % (
                        results[key][0], results[key][1],
                        results[key][2], results[key][3],
                        # round(52*results[key][3]/results[key][2], 2)
                    )
                )
            elif key == "bought_coins":
                print("%s: %s" % (key, str(list(results[key].keys()))))
            else:
                print("%s: %s" % (key, results[key]))

    def get_all_iterations(self):
        for weeks_duration in range(self.min_week_duration, self.max_week_duration + 1):
            for week_start_index in range(self.min_week_index, self.max_week_index + 1):
                week_end_index = week_start_index + weeks_duration
                if week_end_index > self.max_week_index:
                    break
                yield(weeks_duration, week_start_index, week_end_index)
