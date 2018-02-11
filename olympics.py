from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

def get_medal_count():
    url = "https://www.pyeongchang2018.com/en/game-time/results/OWG2018/en/general/medal-standings.htm"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    #req.headers["User-Agent"] = "windows 10 bot"
    s = urlopen(req).read().decode("utf-8")

    tabledata = s[s.find("<table class=\"ResTableFull\">"):]
    tabledata = tabledata[:tabledata.find("</table>")+8]

    table_data = [[cell.text.strip() for cell in row("td")] for row in BeautifulSoup(tabledata,"lxml")("tr")]

    table_data.pop(0)
    output = "```python\n"
    output = output + "%s %s %s %s %s %s\n" % ("Rk", "Country".ljust(18), " G", " S", " B", "Tot")
    for c in table_data:
        output = output + "%s %s %s %s %s %s\n" % (c[0].rjust(2), c[1].ljust(18), c[2].rjust(2), c[3].rjust(2), c[4].rjust(2), c[5].rjust(3))
    output = output + "```"
    #print(output)
    return output
