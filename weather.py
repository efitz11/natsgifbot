import json, html
from urllib.request import urlopen, Request

def get_current_weather(text):
	req = Request("https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20woeid%20in%20(select%20woeid%20from%20geo.places(1)%20where%20text%3D%22"+text+"%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys")
	req.headers["User-Agent"] = "windows 10 bot"
	# Load data
	data = json.loads(urlopen(req).read().decode("utf-8"))
	if data['query']['count']>0:
		data = data['query']['results']['channel']
		output = data['item']['title'] + '\n'
		output = output + data['item']['condition']['temp'] + ' ' + data['units']['temperature'] + " - "
		output = output + data['item']['condition']['text'] + "\n"
		output = output + data['item']['forecast'][0]['day'] + "'s forecast: " + data['item']['forecast'][0]['high'] + "/" + data['item']['forecast'][0]['low'] + ", " + data['item']['forecast'][0]['text']
	print(output)
	
	
#get_current_weather('%2C'.join(("fairfax,","va")))
#get_current_weather('22203')