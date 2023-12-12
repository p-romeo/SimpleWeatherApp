import weather_app
from weather_app import WeatherApp


def getZipCode():
    while True:
        zip_code = input("Enter the zip for a forecast: ")
        if len(zip_code) == 5 and zip_code.isnumeric():
            return zip_code
        else:
            print("Please enter a valid zip code")


api_key = '8f9676b50dfb0acf1ba1199542313e27'
base_url = "http://api.weatherstack.com/"
app = weather_app.WeatherApp(api_key, base_url)
zip_code = getZipCode()
print(f"You entered zip code: {zip_code}")
app.getCurrentWeather(zip_code)
