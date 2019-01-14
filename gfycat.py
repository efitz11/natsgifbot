import utils
import requests
import urllib.parse

def search_gfys(query):
    api_url = "https://api.gfycat.com/v1/"
    oauth_url = api_url+"oauth/token"
    search_url = api_url+"me/gfycats/search"
    keys = utils.get_keys('gfycat')
    params = {'client_id':keys['client_id'], 'client_secret':keys['client_secret'],
              'username':keys['username'], 'password':keys['password'], "grant_type":'password'}
    # print(params)
    r = requests.post(oauth_url, data=str(params))
    # print(r.json())
    access_token = r.json()['access_token']
    headers = {'Authorization':'Bearer {}'.format(access_token)}
    url = search_url+"?search_text=%s&count=10&start=0" % urllib.parse.quote_plus(query)
    s = requests.get(url,headers=headers).json()
    if len(s['gfycats']) > 0:
        return "https://gfycat.com/%s" % s['gfycats'][0]['gfyName']
    else:
        print("query: %s\n%s\n\n" % (query, s))
        return "No gfycats found"

if __name__ == "__main__":
    search_gfys("max booing")
