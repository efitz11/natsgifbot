import json
from urllib.request import urlopen, Request
import urllib.parse

def get_cryptocurrency_data(text):
    if len(text) == 0:
        text = "?limit=10"
    req = Request("https://api.coinmarketcap.com/v1/ticker/" +text)
    req.headers["User-Agent"] = "windows 10 bot"
    data = json.loads(urlopen(req).read().decode("utf-8"))
    if "error" in data:
        return
    output = "```python\n"
    for coin in data:
        name = coin["name"]
        price = coin["price_usd"]
        change = coin["percent_change_24h"]
        change7 = coin["percent_change_7d"]
        output = output + name.ljust(12) + " $" + price.ljust(10) + change.rjust(6) + "% last 24h\t" + change7.rjust(6) + "% last 7d\n"
    return output+"```"