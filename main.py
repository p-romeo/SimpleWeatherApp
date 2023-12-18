import weather_app

def getZipCode():
    while True:
        zip_code = input("Enter the zip for a forecast: ")
        if len(zip_code) == 5 and zip_code.isnumeric():
            return zip_code
        else:
            print("Please enter a valid zip code")


api_key = '3fd394fd91eb46557abe94f7fefb5e3e'
base_url = "http://api.weatherstack.com/"
zip_code = getZipCode()
print(f"You entered zip code: {zip_code}")
