# Simple Weather App

A Python-based weather application that displays current weather information for any ZIP code using the WeatherStack API.

## Features
- Clean, modern UI built with Kivy
- Real-time weather data from WeatherStack
- Displays temperature, location, time, and weather conditions
- Weather condition icons

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd SimpleWeatherApp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Get your API key from [WeatherStack](https://weatherstack.com/)
   - Edit `.env` and replace `your_api_key_here` with your actual WeatherStack API key

4. Run the application:
```bash
python main.py
```

## Environment Variables

The application uses the following environment variables:

- `WEATHERSTACK_API_KEY`: Your WeatherStack API key

These should be placed in a `.env` file in the root directory. A template is provided in `.env.example`.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 