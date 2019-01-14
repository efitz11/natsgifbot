import utils
import requests
import urllib.parse
import json

def gfy_str(gfy, embed=True):
    name = gfy['gfyName']
    title = gfy['title']
    desc = gfy['description']
    url = "https://gfycat.com/%s" % name
    if not embed:
        url = "<%s>" % url
    tags = None
    if 'tags' in gfy and gfy['tags'] is not None:
        tags = ', '.join(gfy['tags'])
    str = "%s" % title
    if len(desc) > 0:
        str = "%s - %s" % (str, desc)
    if tags is not None:
        str = "%s [%s]" % (str, tags)
    return "%s, %s" % (str, url)

def search_gfys(query, num=0):
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
    try:
        if len(s['gfycats']) > 0:
            if num == 0:
                return gfy_str(s['gfycats'][0])
            else:
                out = ""
                for i in range(min(num, len(s['gfycats']))):
                    out = "%s%s\n" % (out, gfy_str(s['gfycats'][i], embed=False))
                return out
        else:
            print("query: %s\n%s\n\n" % (query, s))
            return "No gfycats found"
    except:
        import traceback
        f = utils.write_to_file(json.dumps(s),"gfycat.json", 'errors', prependtimestamp=True)
        print("error: json output written to %s" % f)
        traceback.print_exc()
        return "encountered error"

if __name__ == "__main__":
    search_gfys("max booing")
