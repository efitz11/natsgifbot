import json, time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
import urllib.parse
from bs4 import BeautifulSoup
import tweepy
import utils

def get_keys(name):
    with open("keys.json",'r') as f:
        s = f.read()
    keys = json.loads(s)['keys']
    for key in keys:
        if key['name'] == name:
            return key

def get_wiki_page(query):
    url = "https://en.wikipedia.org/w/api.php?action=opensearch&search="+urllib.parse.quote_plus(query)+"&limit=1&namespace=0&redirects=resolve&format=json"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = json.loads(urlopen(req).read().decode('utf-8'))
    return data[-1][0]
    
def search_untappd(beer_name):
    """search untappd for a beer"""
    keys = get_keys("untappd")
    url = "https://api.untappd.com/v4/search/beer?q="
    lim = "limit=5"
    clid = "client_id=%s" % keys['id']
    secr = "client_secret=%s" % keys['secret']
    url = url + '&'.join([urllib.parse.quote_plus(beer_name), clid, secr, lim])
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    page = urlopen(req)
    data = page.read().decode('utf-8')
    rate = page.getheader('X-Ratelimit-Remaining')
    print(rate)
    data = json.loads(data)['response']['beers']['items']
    if len(data) > 0:
        beer = data[0]['beer']
        brew = data[0]['brewery']
        beer_page = "https://untappd.com/beer/%d" % beer['bid']
        brewery = brew['brewery_name']
        location = brew['location']['brewery_city'] + "," + brew['location']['brewery_state']
        name = beer['beer_name']
        abv = beer['beer_abv']
        ibu = beer['beer_ibu']
        desc = beer['beer_description']
        return "**%s** - %s (%s)\nABV: %.1f\tIBU: %d\n\n%s\n\n%s" % (name, brewery, location, abv, ibu, desc, beer_page)
    return "No beer found"


def get_latest_ig_post(username):
    url = "https://www.instagram.com/" + username
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    #req.headers["User-Agent"] = "windows 10 bot"
    s = urlopen(req).read().decode("utf-8")
    srchstr = "window._sharedData = "
    s = s[s.find(srchstr)+len(srchstr):]
    s = s[:s.find("};")+1]
    s = json.loads(s)
    print(s)
    #print("%s" % s['entry_data']['ProfilePage'][0]['user']['media']['nodes'][0]['code'])
    post = s['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']
    caption = post['edge_media_to_caption']['edges'][0]['node']['text']
    timestamp = utils.prettydate(post['taken_at_timestamp'])
    location = ""
    if 'location' in post:
        location = " *(%s)* " % post['location']['name']
    url = "https://www.instagram.com/p/" + post['shortcode']
    return "%s**%s**: %s (%s)\n\n%s" % (location, username, caption, timestamp, url)

def get_cryptocurrency_data(text):
    if len(text) == 0:
        text = "?limit=10"
    url = "https://api.coinmarketcap.com/v1/ticker/" + text
    data = utils.get_json(url)
    if "error" in data:
        return
    for coin in data:
        coin["price_usd"] = "%.02f" % float(coin["price_usd"])
        coin["percent_change_24h"] = "%.02f" % float(coin["percent_change_24h"])
        coin["percent_change_7d"] = "%.02f" % float(coin["percent_change_7d"])
    repl = {"price_usd":"price","percent_change_24h":"% 24h", "percent_change_7d":"% 7d"}
    labels = ['name','price_usd', 'percent_change_24h','percent_change_7d']
    left = ['name']
    output = utils.format_table(labels, data, repl_map=repl, left_list=left)
    return "```python\n" + output + "```"

def get_latest_tweet(user):
    with open("keys.json",'r') as f:
        s = f.read()
    keys = json.loads(s)['keys']
    for key in keys:
        if key['name'] == "twitter":
            api_key = key['api_key']
            secret = key['api_secret']
            token = key['token']
            token_secret = key['token_secret']
    if 'accounts' in json.loads(s):
        map = json.loads(s)['accounts']
    else:
        map = dict()
    user = user.lower()
    if user == "list":
        output = ""
        for u in map:
            output = output + "%s - %s\n" % (u, map[u])
        return output[:-1]
    if user in map:
        user = map[user]
    auth = tweepy.OAuthHandler(api_key, secret)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    tweet = api.user_timeline(screen_name=user,count=1)[0]
    tid = tweet.id
    t = tweet.created_at
    nowtime = time.time()
    diff = datetime.fromtimestamp(nowtime) - datetime.utcfromtimestamp(nowtime)
    local = t + diff
    local = utils.prettydate(local)
    # local = local.strftime("%Y-%m-%d %I:%M:%S")
    # print(json.dumps(tweet._json))

    prefix = "Tweet posted "
    if "retweeted_status" in tweet._json:
        prefix = "Retweeted "
    return "%s %s: https://twitter.com/%s/status/%s" % (prefix, local, user, tid)

def search_imdb(query):
    url = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + urllib.parse.quote_plus(query) + "&s=all"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    divs = soup.findAll(class_="findSection")
    div = divs[0]
    soup1 = BeautifulSoup(str(div),'html.parser')
    href = soup1.find('tr').find('a')['href']
    out = "https://imdb.com%s" % href
    return out

def ud_def(query):
    url = "http://api.urbandictionary.com/v0/define?term=" + urllib.parse.quote_plus(query)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = json.loads(urlopen(req).read().decode('utf-8'))
    count = 0
    out = []
    for l in data['list']:
        count += 1
        out.append("**%s**: %s\n\n*%s*" % (l['word'], l['definition'], l['example']))
        if count == 2:
            break
    return out

def _print_table(lines):
    # lengths = [0 for i in range(len(lines[0]))]
    outlines = ['' for i in range(len(lines))]
    for col in range(len(lines[0])):
        length = 0
        for i in range(len(lines)):
            length = max(length,len(lines[i][col]))
        for i in range(len(lines)):
            outlines[i] = "%s %s" % (outlines[i], lines[i][col].ljust(length))
    return '\n'.join(outlines)

def cocktail(query):
    url = "https://www.thecocktaildb.com/api/json/v1/1/search.php?s=" + urllib.parse.quote_plus(query)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = json.loads(urlopen(req).read().decode('utf-8'))
    if data['drinks'] is None:
        return "No cocktails found."
    if len(data['drinks']) == 0:
        return "No cocktails found."
    for drink in data['drinks']:
        output = "**%s**:\n\n" % drink['strDrink']
        lines = []
        for i in range(1,15):
            ingredient = drink['strIngredient%d' % i]
            if ingredient == "":
                break
            measure = drink['strMeasure%d' % i]
            lines.append([measure, ingredient])
        output = "%s```%s```" % (output, _print_table(lines))
        output = "%s\n%s\n\n" % (output, drink['strInstructions'].strip())
        output = "%s%s" % (output, drink['strDrinkThumb'])
        return output

def kym(query):
    url = "https://knowyourmeme.com/search?q=" + urllib.parse.quote_plus(query)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    table = soup.find_all("table",class_="entry_list")[0]
    entries = table.find_all("td")
    link = entries[0].find("h2").find("a")
    title = link.contents[0]
    url = "https://knowyourmeme.com" + link['href']
    print(title, url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    content = soup.find('div', {"id":"content"})
    article = content.find('article', class_="entry")
    # body = article.find('div',{'id':'entry_body'}).find('p').get_text()
    body = article.find('section',class_="bodycopy")
    paras = body.find_all('p')
    for p in paras:
        if len(p.get_text()) > 1:
            body = p.get_text()
            break
    img = article.find("header").find("img")['data-src']

    body = img + "\n\n" + body
    body = body + "\n\nMore info at <%s>" % (url)
    return(body)

if __name__ == "__main__":
    # print(search_untappd("heineken"))
    # print(get_latest_tweet("nationalsump"))
    # print(get_latest_tweet("chelsea_janes"))
    # print(ud_def("word"))
    # search_imdb("ryan reynolds")
    # print(cocktail("margarita"))
    print(kym("wednesday my dudes"))
    # print(kym("iphone"))
