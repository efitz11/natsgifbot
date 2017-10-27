from urllib.request import urlopen
import xmltodict
import json

class XmlReader:
    def __init__(self):
        self.mlbtrurl = 'https://www.mlbtraderumors.com/washington-nationals/feed'
        self.mlbtrlog = 'mlbtr.log'
        
    def mlbtr(self):
        file = urlopen(self.mlbtrurl)

        data = xmltodict.parse(file)
        
        #f = open('xmlout.txt','w')
        #f.write(json.dumps(data,indent=4))
        #f.close()
        
        leaditem = data['rss']['channel']['item'][0]
        #date = leaditem['pubDate']
        #title = leaditem['title']
        link = leaditem['link']
        try:
            f = open(self.mlbtrlog,'r')
            last = f.readline()
            f.close()
        except FileNotFoundError:
            print ("creating log")
            last = ""
            
        if last != link:
            f = open(self.mlbtrlog,'w')
            f.write(link)
            f.close()
            return "New MLBTR post: %s" % link