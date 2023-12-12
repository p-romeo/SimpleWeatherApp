'''
A simple weather app, enter a zip code and get a forecast!
'''

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
import requests

class WeatherAppLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.api_key = '0bec28f01706819cc9e739dd721e8f12'
        self.base_url = "http://api.weatherstack.com/"

        self.zip_code = TextInput(multiline=False)
        self.add_widget(Label(text="Enter Zip Code:"))
        self.add_widget(self.zip_code)

        self.weather_display = Label(text='')
        self.add_widget(self.weather_display)

        self.get_weather_button


class WeatherApp:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

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