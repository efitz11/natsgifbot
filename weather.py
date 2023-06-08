from datetime import datetime
import json
import time
from urllib.request import urlopen, Request
import requests
import utils
import os

emojimap = {'Sunny':':sunny:',
            'Mostly Cloudy':':white_sun_cloud:',
            'Partly Cloudy':':white_sun_small_cloud:',
            'Cloudy':':cloud:',
            'Snow':':cloud_snow:',
            'Snow Showers':':cloud_snow:',
            'Showers':':cloud_rain:',
            'Thunderstorms':':thunder_cloud_rain:',
            'Severe Thunderstorms':'Severe :thunder_cloud_rain:'}

def _convert_ctof(temp):
    '''convert celsius to fahrenheit'''
    return 9.0/5.0 * float(temp) + 32

def _get_ET_from_timestamp(timestamp):
    # utc = datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:00Z") #"2018-03-31T20:05:00Z",
    utc = datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:00+00:00") # 2019-01-10T18:52:00+00:00
    nowtime = time.time()
    diff = datetime.fromtimestamp(nowtime) - datetime.utcfromtimestamp(nowtime)
    utc = utc + diff
    return datetime.strftime(utc, "%I:%M ET")

def get_current_weatherbit(text):
    url = "https://api.weatherbit.io/v2.0/current"
    key = utils.get_keys("weatherbit")['key']
    lat,lon,loc = get_lat_lon(text)
    url = url + "?key=%s&units=I&lat=%f&lon=%f" % (key, lat, lon)
    resp = utils.get_json(url)
    if len(resp['data']) > 0:
        data = resp['data'][0]
        obstime = data['ob_time']
        obsdatetime = datetime.strptime(obstime, '%Y-%m-%d %H:%M')
        ret = "```python\n" \
              "Location search result: %s\n" \
              "%s in %s, %s, %s:\n" \
              "  Temp: %.1f (Feels like: %.1f)\n" \
              "  Humidity: %d%%\n" \
              "  Observed: %s at station: %s" % (loc, data['weather']['description'], data['city_name'], data['state_code'], data['country_code'],
                                     data['temp'], data['app_temp'], data['rh'],
                                     utils.prettydate(obsdatetime, utc=True), data['station'])
        if data['aqi'] > 50:
            ret += "\n  AQI: %d```" % (data['aqi'])
        else:
            ret += "```"
        return ret

def get_current_weather(text):
    '''get current weather conditions'''
    loc = get_lat_lon(text)
    url = "https://api.weather.gov/points/%.4f,%.4f" % (loc[0], loc[1])
    data = requests.get(url).json()
    stations_url = data['properties']['observationStations']
    data = requests.get(stations_url).json()
    station = data['features'][0]['properties']['stationIdentifier']
    station_name = data['features'][0]['properties']['name']
    station_url = "https://api.weather.gov/stations/%s/observations?limit=1" % station
    print(station_url)
    data = requests.get(station_url).json()
    data = data['features'][0]['properties']
    temp = _convert_ctof(data['temperature']['value'])
    text = data['textDescription']
    try:
        wind_chill = _convert_ctof(data['windChill']['value'])
    except:
        wind_chill = None

    humidity = data['relativeHumidity']['value']
    updated = _get_ET_from_timestamp(data['timestamp'])
    retval = "At %s:\n%d F, %s\nHumidity: %.0f%%\n" % (station_name, temp, text, float(humidity))
    if wind_chill is not None:
        retval = "%sWind Chill: %d F\n" % (retval, wind_chill)
    retval = "%sUpdated: %s" % (retval, updated)
    return "```python\n%s```" % retval

def get_forecast(text):
    '''get a 10 day weather forecast'''
    loc = get_lat_lon(text)
    url = "https://api.weather.gov/points/%.4f,%.4f" % (loc[0], loc[1])
    print(url)
    req = requests.get(url)
    data = req.json()

    stations_url = data['properties']['observationStations']
    forecast_url = data['properties']['forecast']

    data = requests.get(stations_url).json()
    station_name = data['features'][0]['properties']['name']

    print(forecast_url)
    req = requests.get(forecast_url)
    data = req.json()
    periods = data['properties']['periods']
    out = "Forecast for %s:\n\n" % station_name
    if len(periods) > 0:
        for period in periods[:10]:
            out = out + "%s: %d%s\n%s\n\n" % (period['name'], period['temperature'], period['temperatureUnit'], period['detailedForecast'])
    return "```python\n%s```" % out

def get_readable_location(geocode_result):
    loc_str = ""
    for component in geocode_result['address_components']:
        if len(loc_str) == 0:
            loc_str += component['short_name']
        else:
            if component['types'][0] in ['locality', 'administrative_area_level_1', 'country']:
                loc_str += ", %s" % component['short_name']
    return loc_str

def get_lat_lon(search):
    cache = "cache/locations.json"
    cachedir = "cache"
    if not os.path.exists(cache):
        if not os.path.exists(cachedir):
            os.makedirs(cachedir)
        with open(cache, 'w') as f:
            f.write("{}")
    with open(cache, 'r') as f:
        s = f.read()
    queries = json.loads(s)
    if search in queries:  # if cached
        result = queries[search]['geometry']['location']
        return (result['lat'], result['lng'], get_readable_location(queries[search]))
    else:  # otherwise use API to find location
        query = search.replace(' ','+')
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + query + "&key="
        with open("keys.json",'r') as f:
            f = json.loads(f.read())
        for k in f['keys']:
            if k['name'] == 'google':
                key = k['key']
        if key is not None:
            url = url + key
            req = Request(url, headers={'User-Agent' : "ubuntu"})
            s = json.loads(urlopen(req).read().decode("utf-8"))
            print(s)
            lat = s['results'][0]['geometry']['location']['lat']
            lon = s['results'][0]['geometry']['location']['lng']

            # cache result
            queries[search] = s['results'][0]
            with open(cache, 'w') as f:
                f.write(json.dumps(queries))

            return(lat,lon, get_readable_location(s['results'][0]))

def get_current_metar(airport_code):
    # url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=3&mostRecent=true&stationString=" + airport_code
    # print(url)
    # req = Request(url, headers={'User-Agent' : "ubuntu"})
    # open = urlopen(req)
    # content = open.read().decode('utf-8')
    # tag = '<raw_text>'
    # close = '</raw_text>'
    # metar = content[content.find(tag) + len(tag):content.find(close)]
    # return metar
    url = 'https://api.weather.gov/stations/%s/observations?limit=25' % (airport_code)
    data = utils.get_json(url)
    if len(data['features']) > 0:
        for i in range(len(data['features'])):
            if len(data['features'][i]['properties']['rawMessage']) > 0:
                ts = data['features'][i]['properties']['timestamp']
                updated = _get_ET_from_timestamp(ts)
                return "```Time: %s\n%s```" % (updated, data['features'][i]['properties']['rawMessage'])
    else:
        return "Airport code not found"

if __name__ == "__main__":
    #get_current_weather('%2C'.join(("fairfax,","va")))
    # print(get_current_weatherbit('sterling, va'))
    # print(get_lat_lon("potomac, md"))
    print(get_current_metar('kduj'))
    # print(get_forecast("arlington,va"))

