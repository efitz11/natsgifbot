from urllib.request import urlopen, Request
import json

def get_quote(symbol):
    url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    quote = json.loads(urlopen(req).read().decode("utf-8"))
    change = float(quote['change'])
    ch = "%0.2f" %(change)
    chper = "%0.2f" %(quote['changePercent'])
    if change > 0:
        ch = "+" + ch
        chper = "+" + chper
    elif change < 0:
        ch = "-" + ch
        chper = "-" + chper
    output = "%s quote:```python\n Last price: %s (%s, %s" % (symbol.upper(),quote['latestPrice'],ch,chper)+"%)"
    output = output + "```"
    return output
