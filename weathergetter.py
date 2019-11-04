"""WeatherGetter gets weather from DarkSky API

https://api.darksky.net/forecast/[key]/[latitude],[longitude],[time]

key - required
Your Dark Sky secret key.
latitude - required
The latitude of a location (in decimal degrees). Positive is north, negative is south.
longitude - required
The longitude of a location (in decimal degrees). Positive is east, negative is west.
"""
import requests
import os
import pandas as pd

# I've scraped all the cities.

# however for first try: the teams in this database are largely german,
# so go ahead and just use the weather in Berlin, Germany as a proxy
# for this information. If it was raining in Berlin on the day the game
# was played, count that as rain game

class WeatherGetter:
    """WeatherGetter class. Default city is Berlin."""
    def __init__(self, city='Berlin', api_call_limit=10, test=False):
        self.city = city
        self.location = self.load_city_location(city)
        self._api_key = os.environ['DARKSKY_API_KEY']
        self._darksky_api_url = 'https://api.darksky.net/forecast'
        self.api_call_count = 0
        self.api_call_limit = api_call_limit
        self.test = test

    def load_weather(self, unixtime):
        return self.darksky_call(self.location['lat'], self.location['lon'], unixtime)

    def darksky_call(self, lat, lon, date):
        date = str(int(date))
        lat = str(lat)
        lon = str(lon)
        url = '/'.join([self._darksky_api_url, self._api_key, ','.join([lat, lon, date])])
        if self.test:
            return url
        response = requests.get(url)
        self.api_call_count += 1
        return response.json()

    def load_city_location(self, city):
        """Return city lat, long dict if city listed in team_locations.csv file"""
        return pd.read_csv('team_locations.csv').query(f"city == '{city}'")[['lat', 'lon']].to_dict(orient='records')[0]
