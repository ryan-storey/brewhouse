"""
This module is used to generate a prediction of sales for
given months in the future
"""
import csv
from datetime import datetime
from typing import Tuple


def calculate_ratio(totals: dict) -> list:
    """
    Calculates the ratio of sales between each beer

    This function takes the total sales of each beer as an argument
    and calculates the ratio of sales between each beer, returning them
    as a list of values.

    Arguments:
    totals - the total sales of each beer over the last 12 months
    """
    ratio = []
    ratio.append(totals['Organic Red Helles']) #total sales appended
    ratio.append(totals['Organic Pilsner'])
    ratio.append(totals['Organic Dunkel'])
    ratio_exc_zero = []
    for item in ratio:
        if item != 0:  # filters out zeros to avoid crashes
            ratio_exc_zero.append(item)
    lowest_sale = min(ratio_exc_zero)  # calculates ratios excluding zeros
    for i in range(len(ratio)):
        ratio[i] = float("%.3f" % (ratio[i] / lowest_sale))
        # calculates ratio to 3dp
    return ratio


def growth_rate(timeframe: int = 1) -> Tuple:
    """
    Calculates the average growth rate and returns the predicted sales

    This function calculates the average growth rate per month in the
    last 12 months and uses this value to produce a prediction for the
    sales in a given month. The function returns the predictions and
    the ratio of sales between each beer.

    Arguments:
    timeframe - the number of months in the future to predict for
    """
    sales = {}
    # sales read in from file
    sales['Organic Red Helles'] = read_in_sales("Organic Red Helles")
    sales['Organic Pilsner'] = read_in_sales("Organic Pilsner")
    sales['Organic Dunkel'] = read_in_sales("Organic Dunkel")
    predictions = {}
    for key, value in sales.items():
        total_growth = 0
        for i in range(2, 13):  # calculates growth rate between months
            growth = float(value[str(i)] - value[str(i - 1)]) / float(value[str(i - 1)])
            total_growth += growth
            # average growth rate calculated
        average_growth = float(total_growth / 11)
        predictions[key] = sales_predictions(value, average_growth, timeframe)
        predictions[key]['growth'] = float("%.3f" % average_growth)
    ratio = get_sales_ratio(sales)  # ratio of sales calculated
    return ratio, predictions


def get_sales_ratio(sales: dict) -> list:
    """
    Adds up the total yearly sale per beer and returns the ratio of sales

    Arguments:
    sales - dictionary containing the sales data for each beer for 1 year.
    """
    total_sold = {
        'Organic Red Helles': 0,
        'Organic Pilsner': 0,
        'Organic Dunkel': 0}
    for key, value in sales.items():
        for month, sale in value.items():
            total_sold[key] += int(sale)  # all of the sales are added up
    return calculate_ratio(total_sold)  # ratio calculated


def sales_predictions(
        monthly_sales: dict,
        average_growth: float,
        timeframe: int) -> dict:
    """
    Calculates the predicted sale for one month for a beer

    The function takes a dictionary of sales for one year and
    calculates the average monthly sale, and uses this as well
    as the average growth rate to make a prediction for a month
    in the future. The prediction data is returned in a dictionary.
    Prediction formula = average_sale * (growth_rate ^ months)

    Arguments:
    monthly_sales - Dictionary containing the monthly sales for a beer
    average_growth - the average growth rate for one beer per month
    timeframe - the number of months in the future to predict for.
    """

    data = {}
    total = 0
    for i in range(1, 13):
        total = total + monthly_sales[str(i)]
    average = float(total) / 12  # average monthly sale calculated
    growth = float(1 + average_growth)  # growth multiplier calculated
    data['average'] = int(average)
    data['prediction'] = int(average * growth**int(timeframe))
    # prediction calculated
    return data


def read_in_sales(beer: str) -> dict:
    """
    Finds the number of sales per month for a type of beer

    Arguments:
    beer - the name of the beer
    """
    sales = {}
    previous = 0
    month_number = 0
    data = csv_read()
    for order in data:
        if order['Recipe'] == beer:  # beers are read in individually
            month = datetime.strptime(order['Date Required'], '%d-%b-%y').month
            if month != previous:
            # if this record is from a different month to the last one
                previous = month
                month_number += 1  # increase months by 1
            if str(month_number) in sales:
                pass
            else:
                sales[str(month_number)] = 0  # month added to the file
                # sale for that month added to total
            sales[str(month_number)] += int(order["Quantity ordered"])
    return sales


def csv_read() -> list:
    """Reads in all previous sales data from the file"""
    data = []
    with open('test_data.csv') as f:
        # open file
        for row in csv.DictReader(f):
            data.append({key: data for key, data in row.items()})
        # read rows in as a sorted list of dictionaries
        data = sorted(
            data, key=lambda k: datetime.strptime(
                k['Date Required'], '%d-%b-%y'))
    return data
