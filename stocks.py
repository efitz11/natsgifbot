from urllib.request import urlopen, Request
import json
import utils
from bs4 import BeautifulSoup

def get_quote(symbol):
    url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    quote = json.loads(urlopen(req).read().decode("utf-8"))
    try:
        change = float(quote['change'])
        ch = "%0.2f" %(change)
        chper = "%0.2f" %(quote['changePercent'])
        chytd = "%0.2f" % (quote['ytdChange'])
    except TypeError:
        change = "n/a"
        ch = "n/a"
        chper = "n/a"
        chytd = "n/a"
    mcap = quote['marketCap']
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
    if change != "n/a" and change > 0:
        ch = "+" + ch
        chper = "+" + chper
    output = "%s - %s:```python\n Last price: %s (%s, %s%%, %s%% YTD" % \
             (symbol.upper(),quote['companyName'],quote['latestPrice'],ch,chper,chytd)+")"
    output = output + " %s mkt cap\n" % cap
    output = output + " 52w high: %.02f\t52w low:%.02f" % (quote['week52High'], quote['week52Low'])
    output = output + "```"
    return output

def get_stocks():
    output = "Latest quotes:\n```python\n"
    stocks = []
    for symbol in ["DIA","VOO","VTI","ONEQ","VXUS"]:
        url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
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
    url = "https://www.marketwatch.com/investing/index/spx"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    table = soup.find("div", class_="markets__table").find("table")
    table_data = [[cell.text.strip() for cell in row("td")]
                             for row in table("tr")]
    rows = []
    for row in table_data:
        if row[1] in indexes:
            idx = {}
            idx[labels[0]] = row[1]
            idx[labels[1]] = row[2]
            idx[labels[2]] = row[3]
            idx[labels[3]] = row[4]
            rows.append(idx)
    return "```%s```" % utils.format_table(labels,rows, left_list=left)

if __name__ == "__main__":
    print(get_quote("msft"))
    # print(get_indexes())
