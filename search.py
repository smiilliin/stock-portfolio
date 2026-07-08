from pykrx import stock

for ticker in stock.get_etf_ticker_list():
    name = stock.get_etf_ticker_name(ticker)

    if "금현물" in name:
        print(ticker, name)

    if "미국30년국채" in name:
        print(ticker, name)
