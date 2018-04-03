from urllib.request import urlopen, Request
import json

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
    else:
        cap = str(round(mcap/1e3,1))+ "k"
    if change != "n/a" and change > 0:
        ch = "+" + ch
        chper = "+" + chper
    output = "%s - %s:```python\n Last price: %s (%s, %s%%, %s%% YTD" % (symbol.upper(),quote['companyName'],quote['latestPrice'],ch,chper,chytd)+")"
    output = output + " %s mkt cap" % cap
    output = output + "```"
    return output

def get_stocks():
    output = "Latest quotes:\n```python\n"
    for symbol in ["DIA","VOO","VTI","ONEQ","VXUS"]:
        url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
        req = Request(url)
        req.headers["User-Agent"] = "windows 10 bot"
        # Load data
        quote = json.loads(urlopen(req).read().decode("utf-8"))
        change = float(quote['change'])
        ch = "%0.2f" %(change)
        chper = "%0.2f" %(quote['changePercent'])
        chytd = "%0.2f" % (quote['ytdChange'])
        if change > 0:
            ch = "+" + ch
            chper = "+" + chper
        output = output + "%s - %s (%s, %s%%, %s%% YTD) - %s\n" % (symbol.upper(),quote['latestPrice'],ch,chper,chytd,quote['companyName'])
#    output = "%s - %s:```python\n Last price: %s (%s, %s%%, %s%% YTD" % (symbol.upper(),quote['companyName'],quote['latestPrice'],ch,chper,chytd)+")"
    output = output + "```"
    return output

if __name__ == "__main__":
    print(get_quote("msft"))
