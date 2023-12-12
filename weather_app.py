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

        self.get_weather_button = Button(text='Get Weather')
        self.get_weather_button.bind(on_press=self.get_weather)
        self.add_widget(self.get_weather_button)

    def get_weather(self, instance):
        zip_code = self.zip_code.text
        url = f"{self.base_url}forecast/current?access_key={self.api_key}&query={zip_code}"
        try:
            response = requests.get(url)
            response.raise_for_status()

        except Exception as err:
            self.weather_display.text = f'An error occured: {err}'
            return

        data = response.json()
        self.weather_display.text = (f"Weather at {data['location']['name']}, {data['location']['localtime']}: "
                                     f"{data['current']['temperature']} degrees,"
                                     f" {data['current']['weather_descriptions']}")


class WeatherApp(App):
    def build(self):
        return WeatherAppLayout()

if __name__ == '__main__':
    WeatherApp().run()