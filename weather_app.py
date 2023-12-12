'''
A simple weather app, enter a zip code and get a forecast!
'''

import requests
from kivy.app import App

class WeatherApp:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.weatherstack.com/"

    def getZipCode(self):
        while True:
            zip_code = input("Enter the zip for a forecast: ")
            if len(zip_code) == 5:
                return zip_code
            else:
                print("Please enter a valid zip code")

    def getCurrentWeather(self, zip_code):
        url = f"{self.base_url}forecast?access_key={self.api_key}&query={zip_code}"
        response = requests.get(url)
        data = response.json()
        print(data)
        print(data['location']['name'])
        print(data['location']['localtime'])
        print(data['current']['temperature'])
        print(data['current']['weather_descriptions'])
        #print(data['localtime'])
        #print(data['forecast'])
        #print(data['current'])