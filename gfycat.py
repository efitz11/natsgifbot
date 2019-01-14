import utils
import requests
import urllib.parse
import json

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
                return "https://gfycat.com/%s" % s['gfycats'][0]['gfyName']
            else:
                out = ""
                for i in range(min(num, len(s['gfycats']))):
                    gfy = s['gfycats'][i]
                    url = "https://gfycat.com/%s" % gfy['gfyName']
                    title = gfy['title']
                    desc = gfy['description']
                    if 'tags' in gfy and gfy['tags'] is not None:
                        tags = ', '.join(gfy['tags'])
                    else:
                        tags = ""
                    out = out + "%s - %s (%s), <%s>\n" % (title, desc, tags, url)
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
