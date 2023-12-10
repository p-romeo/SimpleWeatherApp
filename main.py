import weather_app

api_key = '0bec28f01706819cc9e739dd721e8f12'
app = weather_app.WeatherApp(api_key)
zip_code = app.getZipCode()
print(f"You entered zip code: {zip_code}")
app.getCurrentWeather(zip_code)

