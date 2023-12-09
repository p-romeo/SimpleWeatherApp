'''
A simple weather app, enter a zip code and get a forecast!
'''

import requests

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

    def getFiveHour(self, zip_code):
        url = f"{self.base_url}forecast?access_key={self.api_key}&query={zip_code}&hourly=1"
        response = requests.get(url)
        data = response.json()

        print(data)