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
    """WeatherGetter class."""
    def __init__(self):
        self.location = self.load_city_location('Berlin')
        print(os.environ)

    def load_city_location(self, city):
        """Return city lat, long dict if city listed in team_locations.csv file"""
        return pd.read_csv('team_locations.csv').query(f"city == '{city}'")[['lat', 'long']].to_dict(orient='records')[0]
