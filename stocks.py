from urllib.request import urlopen, Request
import json

def get_quote(symbol):
    url = "https://api.iextrading.com/1.0/stock/"+symbol+"/quote?displayPercent=true"
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    quote = json.loads(urlopen(req).read().decode("utf-8"))
    output = "```python\n Last price: %s (%s,%s" % (quote['latestPrice'],quote['change'],quote['changePercent'])+"%)"
    output = output + "```"
    return output
