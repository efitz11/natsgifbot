from urllib.request import urlopen, Request
import json
import utils
from bs4 import BeautifulSoup
from datetime import datetime

def simpleMarketCap(mcap):
    if mcap is not None:
        if mcap >= 1e12:
            cap = round(mcap/1e12, 1)
            cap = str(cap) + "T"
        elif mcap >= 1e9:
            cap = round(mcap/1e9, 1)
            cap = str(cap) + "B"
        elif mcap >= 1e6:
            cap = round(mcap/1e6, 1)
            cap = str(cap) + "M"
        elif mcap >= 1e3:
            cap = str(round(mcap/1e3,1))+ "k"
        else:
            cap = str(mcap)
    else:
        cap = ""
    return cap

def get_quote(symbol):
    if symbol.lower() == 'futures':
        return get_index_futures()
    # url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
    token = utils.get_keys("iex")['public']
    url = "https://cloud.iexapis.com/stable/stock/%s/quote?displayPercent=true&token=%s" % (symbol, token)
    print(url)
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    quote = json.loads(urlopen(req).read().decode("utf-8"))
    try:
        change = float(quote['change'])
        quote['ch'] = "%0.2f" %(change)
        quote['chper'] = "%0.2f" %(quote['changePercent'])
        quote['chytd'] = "%0.2f" % (quote['ytdChange'])
    except TypeError:
        change = "n/a"
        quote['ch'] = "n/a"
        quote['chper'] = "n/a"
        quote['chytd'] = "n/a"
    mcap = quote['marketCap']
    if mcap is not None:
        if mcap >= 1e12:
            cap = round(mcap/1e12, 1)
            cap = str(cap) + "T"
        elif mcap >= 1e9:
            cap = round(mcap/1e9, 1)
            cap = str(cap) + "B"
        elif mcap >= 1e6:
            cap = round(mcap/1e6, 1)
            cap = str(cap) + "M"
        elif mcap >= 1e3:
            cap = str(round(mcap/1e3,1))+ "k"
        else:
            cap = str(mcap)
    else:
        cap = ""
    if change != "n/a" and change > 0:
        quote['ch'] = "+" + quote['ch']
        quote['chper'] = "+" + quote['chper']
    output = "%s - %s:\n" % (symbol.upper(), quote['companyName'])
    output += "```python\n"
    if quote['latestSource'] != "IEX real time price":
        output += "Realtime price: {iexRealtimePrice}\n".format_map(quote)
    output += "{latestSource} - {latestTime}:\n" \
              "Last price: {latestPrice} ({ch}, {chper}%, {chytd}% YTD)".format_map(quote)
    output = output + " %s mkt cap\n" % cap
    if quote['week52High'] is not None:
        output = output + "52w high: %.02f\t52w low:%.02f" % (quote.get('week52High'), quote.get('week52Low'))
    output = output + "```"
    return output

def get_quote_yahoo(symbol):
    if symbol.lower() == 'futures':
        return get_index_futures()

    # url = "https://query1.finance.yahoo.com/v7/finance/options/%s" % symbol
    # quote = utils.get_json(url)['optionChain']['result'][0]['quote']
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%s" % symbol
    quote = utils.get_json(url)['quoteResponse']['result'][0]

    output = "{shortName} ({symbol})\n".format_map(quote)
    output += "```python\n"
    if quote['marketState'] in ["POST", "POSTPOST"]:
        if "postMarketChange" in quote:
            if quote['postMarketPrice'] > 0.1:
                output += "After Hours:  %.02f (%.02f, %.02f%%) (%s)\n" % (quote.get("postMarketPrice"), quote.get("postMarketChange"), quote.get("postMarketChangePercent"), datetime.fromtimestamp(quote.get("postMarketTime")))
            else:
                output += "After Hours:  %s (%s, %.02f%%) (%s)\n" % ("{:.2e}".format(quote["postMarketPrice"]), "{:.2e}".format(quote["postMarketChange"]), quote.get("postMarketChangePercent"), datetime.fromtimestamp(quote.get("postMarketTime")))
        output += "Market Close: %.02f (%.02f, %.02f%%) (%s)\n" % (quote.get("regularMarketPrice"), quote.get("regularMarketChange"), quote.get("regularMarketChangePercent"), datetime.fromtimestamp(quote.get("regularMarketTime")))
    elif quote['marketState'] in ["PRE"]:
        if "preMarketPrice" in quote:
            if quote['preMarketPrice'] > 0.1:
                output += "PreMarket:    %.02f (%.02f, %.02f%%) (%s)\n" % (
                    quote.get("preMarketPrice"), quote.get("preMarketChange"), quote.get("preMarketChangePercent"), datetime.fromtimestamp(quote.get("preMarketTime")))
            else:
                output += "PreMarket:    %s (%s, %.02f%%) (%s)\n" % ("{:.2e}".format(quote["preMarketPrice"]), "{:.2e}".format(quote["preMarketChange"]), quote.get("preMarketChangePercent"), datetime.fromtimestamp(quote.get("preMarketTime")))
        output += "Market Close: %.02f (%.02f, %.02f%%) (%s)\n" % (
            quote.get("regularMarketPrice"), quote.get("regularMarketChange"), quote.get("regularMarketChangePercent"), datetime.fromtimestamp(quote.get("regularMarketTime")))
    else:
        if quote['regularMarketPrice'] > 0.1:
            output += "Market Hours: %.02f (%.02f, %.02f%%) (%s)\n" % (quote.get("regularMarketPrice"), quote.get("regularMarketChange"), quote.get("regularMarketChangePercent"), datetime.fromtimestamp(quote.get("regularMarketTime")))
        else:
            output += "Market Hours: %s (%s, %.02f%%) (%s)\n" % ("{:.2e}".format(quote["regularMarketPrice"]), "{:.2e}".format(quote.get("regularMarketChange")), quote.get("regularMarketChangePercent"), datetime.fromtimestamp(quote.get("regularMarketTime")))
    output += "Day volume: %s (%s 10 day avg)\n" % (simpleMarketCap(quote.get("regularMarketVolume")), simpleMarketCap(quote.get("averageDailyVolume10Day")))
    output += "Day range: {regularMarketDayRange}\n".format_map(quote)
    output += "52w range: {fiftyTwoWeekRange}\n".format_map(quote)
    output += "Market Cap: %s, P/E: %s\n" % (simpleMarketCap(quote.get("marketCap")), "%.02f" % quote.get("trailingPE") if "trailingPE" in quote else "N/A")
    output += "```\n<https://finance.yahoo.com/quote/%s>" % (quote.get("symbol"))

    return output

def get_crypto_yahoo():
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=btc-usd,eth-usd,ltc-usd,xlm-usd,doge-usd,bnb-usd"
    results = utils.get_json(url)['quoteResponse']['result']

    if len(results) > 0:
        for res in results:
            price = res['regularMarketPrice']
            if price < 1.0:
                if price > 0.1:
                    res['regularMarketPrice'] = str(round(price, 3))
                    res['regularMarketDayLow'] = str(round(res['regularMarketDayLow'], 3))
                    res['regularMarketDayHigh'] = str(round(res['regularMarketDayHigh'], 3))
                else:
                    res['regularMarketPrice'] = "{:.2e}".format(price)
                    res['regularMarketDayLow'] = "{:.2e}".format(res['regularMarketDayLow'], 3)
                    res['regularMarketDayHigh'] = "{:.2e}".format(res['regularMarketDayHigh'], 3)
            else:
                res['regularMarketPrice'] = int(price)
                res['regularMarketDayLow'] = int(res['regularMarketDayLow'])
                res['regularMarketDayHigh'] = int(res['regularMarketDayHigh'])
            res['marketCap'] = simpleMarketCap(res['marketCap'])

        labels = ["fromCurrency", "regularMarketPrice", "regularMarketDayHigh", "regularMarketDayLow", "marketCap"]
        left_labels = ["fromCurrency"]
        replace = {"fromCurrency":"coin", "regularMarketPrice":"Price", "regularMarketDayHigh":"24h high",
                   "regularMarketDayLow":"24h low", "marketCap":"market cap"}
        out = "```python\n"

        out += utils.format_table(labels, results, left_list=left_labels, repl_map=replace)
        out += "```"
        return out
    else:
        return "error"

def get_stocks():
    output = "Latest quotes:\n```python\n"
    stocks = []
    token = utils.get_keys("iex")['public']
    for symbol in ["DIA","VOO","VTI","ONEQ","VXUS"]:
        url = "https://cloud.iexapis.com/stable/stock/%s/quote?displayPercent=true&token=%s" % (symbol, token)
        # url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
        req = Request(url)
        req.headers["User-Agent"] = "windows 10 bot"
        # Load data
        quote = json.loads(urlopen(req).read().decode("utf-8"))
        stock = dict()
        change = float(quote['change'])
        ch = "%0.2f" %(change)
        chper = "%0.2f" %(quote['changePercent'])
        chytd = "%0.2f" % (quote['ytdChange'])
        if change > 0:
            ch = "+" + ch
            chper = "+" + chper
        stock['symbol'] = symbol.upper()
        stock['price'] = "%.2f" % float(quote['latestPrice'])
        stock['change'] = ch
        stock['%'] = chper
        stock['% YTD'] = chytd
        stock['description'] = quote['companyName']
        stock['high52w'] = quote['week52High']
        stock['low52w'] = quote['week52Low']
        stocks.append(stock)
        # output = output + "%s - %s (%s, %s%%, %s%% YTD) - %s\n" % (symbol.upper(),quote['latestPrice'],ch,chper,chytd,quote['companyName'])
#    output = "%s - %s:```python\n Last price: %s (%s, %s%%, %s%% YTD" % (symbol.upper(),quote['companyName'],quote['latestPrice'],ch,chper,chytd)+")"
    labels = ['symbol','price','change','%','% YTD','description']
    left = ['symbol','description']
    output = output + utils.format_table(labels, stocks, left_list=left)
    output = output + "```"
    return output

def get_indexes():
    indexes = {'Dow','S&P 500','Nasdaq'}
    labels = ['Index','Last','Change','%']
    left = [labels[0]]
    url = "https://cnn.com/markets"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    # with open('output.txt','w', encoding='utf-8') as f:
    #     f.write(data)
    l = soup.find("ul", class_="three-equal-columns wsod")
    # print(l)
    items = l.findAll('li')
    rows = list()
    for item in items:
        ticker = dict()
        ticker['Index'] = item.find("span", class_="ticker-name").get_text()
        ticker['Last'] = item.find("span", class_="ticker-points").get_text()
        ticker['%'] = item.find("span", class_="ticker-name-change").get_text()
        ticker['Change'] = item.find("span", class_="ticker-points-change").get_text()
        rows.append(ticker)

    u = soup.find("div", class_="disclaimer")
    t = u.find("span").get_text()
    # table_data = [[cell.text.strip() for cell in row("td")]
    #                          for row in table("tr")]
    # rows = []
    # for row in table_data:
    #     if row[1] in indexes:
    #         idx = {}
    #         idx[labels[0]] = row[1]
    #         idx[labels[1]] = row[2]
    #         idx[labels[2]] = row[3]
    #         idx[labels[3]] = row[4]
    #         rows.append(idx)
    return "```%s\n  Updated: %s```" % (utils.format_table(labels,rows, left_list=left), t)

def get_yahoo_indexes():
    indexes = {'^GSPC':'S&P 500', '^DJI':'Dow 30', '^IXIC':'Nasdaq'}
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols="
    for index in indexes.keys():
        url = url + index + ","
    url = url[:-1]  # remove trailing comma
    data = utils.get_json(url)
    idxs = list()
    for future in data['quoteResponse']['result']:
        idx = dict()
        idx['name'] = indexes[future['symbol']]
        idx['price'] = "%.2f" % future['regularMarketPrice']
        idx['change'] = "%.2f" % future['regularMarketChange']
        idx['%'] = "%.2f" % future['regularMarketChangePercent']
        idxs.append(idx)
    labels = ['name','price','change','%']
    left = ['name']
    return "```%s```" % (utils.format_table(labels,idxs,left_list=left))

def get_index_futures():
    indexes = {'ES=F':'S&P Futures', 'YM=F':'Dow Futures', 'NQ=F':'Nasdaq Futures'}
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols="
    for index in indexes.keys():
        url = url + index + ","
    url = url[:-1]  # remove trailing comma
    data = utils.get_json(url)
    idxs = list()
    for future in data['quoteResponse']['result']:
        idx = dict()
        idx['name'] = indexes[future['symbol']]
        idx['price'] = future['regularMarketPrice']
        idx['change'] = future['regularMarketChange']
        idx['%'] = round(future['regularMarketChangePercent'], 2)
        idxs.append(idx)
    labels = ['name','price','change','%']
    left = ['name']
    return "```%s```" % (utils.format_table(labels,idxs,left_list=left))

if __name__ == "__main__":
    # print(get_quote("msft"))
    print(get_yahoo_indexes())
    # print(get_index_futures())
    # print(get_quote_yahoo("btc-usd"))
    # print(get_crypto_yahoo())
