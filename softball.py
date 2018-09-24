from urllib.request import urlopen, Request
from html.parser import HTMLParser
from utils import format_table
from datetime import datetime

class TableParser(HTMLParser):
    def __init__(self, table_id):
        HTMLParser.__init__(self)
        self.table_state = False
        self.header_state = False
        self.i = 0
        self.table_id = table_id
        self.cur_data = ""
        self.colspan = 1
    
    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "table" and attr_dict["id"] == self.table_id:
            self.table_state = True
            self.header_state = True
            self.labels = list()
            self.dicts = list()
        elif self.table_state:
            if not self.header_state and tag == "tr":
                self.dicts.append(dict())
                self.i = 0
            elif tag == "td" or tag == "th":
                self.cur_data = ""
                if "colspan" in attr_dict:
                    self.colspan = int(attr_dict["colspan"])
                else:
                    self.colspan = 1
      
    def handle_endtag(self, tag):
        if tag == "table":
            self.table_state = False
        elif tag == "tr":
            self.header_state = False
        elif tag == "td" or tag == "th":
            if self.header_state:
                for i in range(self.colspan):
                    while self.cur_data in self.labels:
                        self.cur_data += "_"
                    self.labels.append(self.cur_data)
            elif self.table_state:
                try:
                  self.dicts[-1][self.labels[self.i]] = self.cur_data
                except IndexError as e:
                  print(self.dicts)
                  print(self.labels)
                  print(self.cur_data)
                  print(self.i)
                  raise e
                self.i += 1
            self.cur_data = ""
  
    def handle_data(self, data):
        self.cur_data += data.strip()
        
def fas_standings():
    url = "http://www.fairfaxadultsoftball.com/c.php?p=365&Season=F&League=FMC&Division=T1&SelectedTeam=All+Teams"
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    parser = TableParser("StandingsTable")
    parser.feed(urlopen(url).read().decode("utf-8"))
    return "```python\n%s\n```" % format_table(parser.labels, parser.dicts)
    
month_lookup = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    
def fas_schedule(week=""):
    url = "http://www.fairfaxadultsoftball.com/c.php?p=365&Season=F&League=FMC&Division=T1&SelectedTeam=All+Teams"
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    parser = TableParser("stand-sched")
    parser.feed(urlopen(url).read().decode("utf-8"))
    
    try:
        week = int(week)
    except ValueError:
        # comb through to find the current week
        week = 1
        now = datetime.now().date()
        for row in parser.dicts:
            if "Date" in row:
                # whenever we see a date that hasn't happened yet, or is today, break out
                if len(row["Date"]) > 6 and month_lookup[row["Date"][-6:-3].lower()] >= now.month and int(row["Date"][-2:]) >= now.day:
                    break
            # update the week as we go
            elif "Visitor" in row:
                if len(row["Visitor"]) > 5 and row["Visitor"][:5] == "Week ":
                    week = int(row["Visitor"][5:])
                    
            
         
    start = len(parser.dicts)
    end = len(parser.dicts)
    for i, row in enumerate(parser.dicts):
        if row["Visitor"] == "Week "+str(week):
            start = i+1
        elif row["Visitor"] == "Week "+str(week+1):
            end = i
    parser.dicts = parser.dicts[start:end]
    
    return "```python\n%s\n```" % format_table(parser.labels[:-3], parser.dicts)