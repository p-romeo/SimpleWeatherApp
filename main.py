"""
A simple weather app, enter a zip code and get a forecast!
"""

import os

import requests
from dotenv import load_dotenv
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

load_dotenv()

api_key = os.getenv('WEATHERSTACK_API_KEY')
# noinspection HttpUrlsUsage
base_url = 'http://api.weatherstack.com/'


class WeatherAppLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.api_key = api_key
        self.base_url = base_url

        self.zip_code = TextInput(multiline=False)
        self.zip_code.bind(on_text_validate=self.get_weather)
        self.add_widget(Label(text="Enter Zip Code:"))
        self.add_widget(self.zip_code)

        self.weather_display = Label(text='')
        self.add_widget(self.weather_display)

        self.weather_image = AsyncImage()
        self.add_widget(self.weather_image)

        self.get_weather_button = Button(text='Get Weather')
        self.get_weather_button.bind(on_press=self.get_weather)
        self.add_widget(self.get_weather_button)

    # noinspection PyUnusedLocal
    def get_weather(self, instance):
        zip_code = self.zip_code.text
        if len(zip_code) != 5 or not zip_code.isnumeric():
            self.weather_display.text = "Invalid Zip Code"
            return
        url = f"{self.base_url}current?access_key={self.api_key}&query={zip_code}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as err:
            self.weather_display.text = f'An error occurred: {err}'
            return

        data = response.json()

        try:
            temperature = data['current']['temperature']
            fahrenheit = (temperature * 9 / 5) + 32

            self.weather_display.text = (f"Weather at {data['location']['name']}, {data['location']['region']} \n"
                                         f"{data['location']['localtime']} \n"
                                         f"{fahrenheit} degrees \n"
                                         f"{data['current']['weather_descriptions'][0]}")

            weather_icon_url = data['current']['weather_icons'][0]
            self.weather_image.source = weather_icon_url

        except KeyError:
            error_message = data.get('error', {}).get('info', 'Unknown Error occurred')
            self.weather_display.text = error_message


class WeatherApp(App):
    def build(self):
        return WeatherAppLayout()


if __name__ == '__main__':
    WeatherApp().run()
