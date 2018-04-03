import json
from urllib.request import urlopen, Request
import urllib.parse
from bs4 import BeautifulSoup

def get_wiki_page(query):
    url = "https://en.wikipedia.org/w/api.php?action=opensearch&search="+urllib.parse.quote_plus(query)+"&limit=1&namespace=0&redirects=resolve&format=json"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = json.loads(urlopen(req).read().decode('utf-8'))
    return data[-1][0]
    
def search_untappd(beer_name):
    """search untappd for a beer"""
    url = "https://untappd.com/search?q="+ urllib.parse.quote_plus(beer_name)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    #data = data[data.find("<div class=\"results-container\">"):]
    soup = BeautifulSoup(data, 'html.parser')
    divs = soup.findAll(class_= 'beer-item')    
    div = divs[0]
    soup1 = BeautifulSoup(str(div), 'html.parser')
    href = soup1.find('a')['href']
    
    #ps = soup1.findAll('p')
    beer_name = soup1.find('p',class_='name').get_text().strip()
    brewery =   soup1.find('p',class_='brewery').get_text().strip()
    beer_type = soup1.find('p',class_='style').get_text().strip()
    beer_abv =  soup1.find('p',class_='abv').get_text().strip()
    beer_ibu =  soup1.find('p',class_='ibu').get_text().strip()
    rating =    soup1.find('p',class_='rating').get_text().strip()
    return  "**%s** - %s \t<https://untappd.com%s>\n%s\t %s\t %s\t Rating: %s" % (beer_name,brewery,href,beer_type,beer_abv,beer_ibu,rating)

def get_latest_ig_post(username):
    url = "https://www.instagram.com/" + username
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    #req.headers["User-Agent"] = "windows 10 bot"
    s = urlopen(req).read().decode("utf-8")
    srchstr = "window._sharedData = "
    s = s[s.find(srchstr)+len(srchstr):]
    s = s[:s.find("};")+1]
    s = json.loads(s)
    #print("%s" % s['entry_data']['ProfilePage'][0]['user']['media']['nodes'][0]['code'])
    return "https://www.instagram.com/p/" + s['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['shortcode']

if __name__ == "__main__":
    print(search_untappd("heineken"))