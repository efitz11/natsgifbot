import json, html
from urllib.request import urlopen, Request

emojimap = {'Sunny':':sunny:',
            'Mostly Cloudy':':white_sun_cloud:',
            'Partly Cloudy':':white_sun_small_cloud:',
            'Cloudy':':cloud:',
            'Snow':':cloud_snow:',
            'Snow Showers':':cloud_snow:',
            'Showers':':cloud_rain:',
            'Thunderstorms':':thunder_cloud_rain:',
            'Severe Thunderstorms':'Severe :thunder_cloud_rain:'}

def get_current_weather(text):
    req = Request("https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20woeid%20in%20(select%20woeid%20from%20geo.places(1)%20where%20text%3D%22"+text+"%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys")
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    data = json.loads(urlopen(req).read().decode("utf-8"))
    if data['query']['count']>0:
        data = data['query']['results']['channel']
        unit = data['units']['temperature']
        condition = data['item']['condition']['text']
        fcondition = data['item']['forecast'][0]['text']
        if condition in emojimap:
            condition = emojimap[condition]
        if fcondition in emojimap:
            fcondition = emojimap[fcondition]
        output = data['item']['title'] + '\n'
        output = output + data['item']['condition']['temp'] + ' ' + unit + " - "
        output = output + condition + "\tWind Chill: " + data['wind']['chill'] + ' ' + unit + "\n"
        output = output + data['item']['forecast'][0]['day'] + "'s forecast: " + data['item']['forecast'][0]['high'] + "/" + data['item']['forecast'][0]['low'] + ", " + fcondition
    return output
    
    
#get_current_weather('%2C'.join(("fairfax,","va")))
#print(get_current_weather('22203'))
