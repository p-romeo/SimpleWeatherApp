"""
A simple weather app, enter a zip code and get a forecast!
"""

import os
import logging
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug environment setup
logger.debug("Starting application...")
logger.debug(f"Current working directory: {os.getcwd()}")
env_path = Path('.env')
logger.debug(f".env file exists: {env_path.exists()}")
if env_path.exists():
    logger.debug(f".env file permissions: {oct(env_path.stat().st_mode)[-3:]}")
    with open('.env', 'r') as f:
        logger.debug(f".env file contents (masked):")
        for line in f:
            if 'API_KEY' in line:
                key_part = line.split('=')[1].strip() if '=' in line else 'invalid_format'
                logger.debug(f"  WEATHERSTACK_API_KEY=****{key_part[-4:] if len(key_part) > 4 else ''}")
            else:
                logger.debug(f"  {line.strip()}")

# Load environment variables
load_dotenv()
api_key = os.getenv('WEATHERSTACK_API_KEY')

# Validate API key
if not api_key:
    logger.error("No API key found! Make sure WEATHERSTACK_API_KEY is set in your .env file")
else:
    # Remove any whitespace and validate
    api_key = api_key.strip()
    logger.debug(f"API key stats:")
    logger.debug(f"  Length: {len(api_key)}")
    logger.debug(f"  First 4 chars: {api_key[:4]}")
    logger.debug(f"  Last 4 chars: {api_key[-4:]}")
    logger.debug(f"  Contains whitespace: {'yes' if any(c.isspace() for c in api_key) else 'no'}")
    # Check for quotes without using backslashes in f-string
    has_quotes = any(q in api_key for q in ['"', "'"])
    logger.debug(f"  Contains quotes: {'yes' if has_quotes else 'no'}")

# API Configuration
base_url = 'http://api.weatherstack.com/current'
logger.debug(f"Using API base URL: {base_url}")

# Set window size and background color
Window.size = (400, 600)
Window.clearcolor = get_color_from_hex('#f0f0f0')
# Ensure proper window density
Window._density = 1.0 if not Window._density else Window._density

class WeatherAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Initializing WeatherAppLayout")
        self.orientation = 'vertical'
        self.padding = [20, 20]
        self.spacing = 20
        
        self.api_key = api_key
        self.base_url = base_url

        # Create UI components
        self._create_ui_components()
        logger.debug("UI components initialized")

    def _create_ui_components(self):
        """Create and initialize all UI components"""
        # Title
        self.add_widget(Label(
            text="Weather Forecast",
            font_size='24sp',
            size_hint_y=None,
            height=50,
            color=get_color_from_hex('#2196F3')
        ))

        # Input section
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=10
        )
        
        self.zip_code = TextInput(
            multiline=False,
            hint_text='Enter ZIP code',
            padding=[10, 10, 0, 0],
            size_hint_x=0.7,
            font_size='16sp',
            background_color=get_color_from_hex('#ffffff'),
            foreground_color=get_color_from_hex('#000000')
        )
        self.zip_code.bind(on_text_validate=self.get_weather)
        
        self.get_weather_button = Button(
            text='Get Weather',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#2196F3'),
            background_normal=''
        )
        self.get_weather_button.bind(on_press=self.get_weather)
        
        input_layout.add_widget(self.zip_code)
        input_layout.add_widget(self.get_weather_button)
        self.add_widget(input_layout)

        # Weather image
        self.weather_image = AsyncImage(
            size_hint=(None, None),
            size=(150, 150),
            pos_hint={'center_x': 0.5}
        )
        self.add_widget(self.weather_image)

        # Weather information display
        self.weather_display = Label(
            text='',
            markup=True,
            font_size='18sp',
            halign='center',
            valign='middle',
            color=get_color_from_hex('#333333'),
            size_hint_y=None,
            height=200
        )
        self.weather_display.bind(size=self.weather_display.setter('text_size'))
        self.add_widget(self.weather_display)

    def _validate_api_key(self):
        """Validate the API key"""
        if not self.api_key:
            logger.error("API key is missing")
            return False
        
        api_key = self.api_key.strip()
        if not api_key:
            logger.error("API key is empty after stripping whitespace")
            return False
            
        logger.debug(f"API key validation:")
        logger.debug(f"  Original length: {len(self.api_key)}")
        logger.debug(f"  Stripped length: {len(api_key)}")
        logger.debug(f"  First/last 4: {api_key[:4]}...{api_key[-4:]}")
        return True

    def get_weather(self, instance):
        """Get weather data for the specified ZIP code"""
        logger.debug("\n=== Starting weather request ===")
        
        # Validate API key
        if not self._validate_api_key():
            self.weather_display.text = "[color=ff3333]API key not found or invalid. Please check your .env file.[/color]"
            return

        # Validate ZIP code
        zip_code = self.zip_code.text
        logger.debug(f"Validating ZIP code: {zip_code}")
        if len(zip_code) != 5 or not zip_code.isnumeric():
            logger.error(f"Invalid ZIP code format: {zip_code}")
            self.weather_display.text = "[color=ff3333]Invalid Zip Code[/color]"
            self.weather_image.source = ''
            return
            
        # Prepare API request
        params = {
            'access_key': self.api_key.strip(),
            'query': zip_code,
            'units': 'f'
        }
        
        # Log request details (with masked API key)
        debug_params = params.copy()
        debug_params['access_key'] = f"****{params['access_key'][-4:]}"
        logger.debug(f"API Request:")
        logger.debug(f"  URL: {self.base_url}")
        logger.debug(f"  Parameters: {json.dumps(debug_params, indent=2)}")
        
        try:
            # Ensure using HTTP for free plan
            if self.base_url.startswith('https'):
                logger.warning("Converting HTTPS to HTTP for free plan compatibility")
                self.base_url = self.base_url.replace('https', 'http')
            
            # Make API request
            logger.debug("Sending API request...")
            response = requests.get(self.base_url, params=params)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Parse response
            data = response.json()
            logger.debug(f"API Response: {json.dumps(data, indent=2)}")

            if not response.ok or 'error' in data:
                error_info = data.get('error', {})
                error_code = error_info.get('code')
                error_type = error_info.get('type')
                error_message = error_info.get('info', 'Unknown error occurred')
                
                logger.error(f"API Error:")
                logger.error(f"  Code: {error_code}")
                logger.error(f"  Type: {error_type}")
                logger.error(f"  Message: {error_message}")
                
                if error_code == 101:
                    self.weather_display.text = ("[color=ff3333]Invalid API key. Please check:\n\n"
                                               "1. Your .env file contains:\n"
                                               "   WEATHERSTACK_API_KEY=your_key_here\n"
                                               "   (no quotes, no spaces)\n\n"
                                               "2. Your API key is active at:\n"
                                               "   weatherstack.com/dashboard\n\n"
                                               "3. You're using the free plan's HTTP URL\n"
                                               "   (not HTTPS)[/color]")
                else:
                    self.weather_display.text = f"[color=ff3333]{error_message}[/color]"
                
                self.weather_image.source = ''
                return

            # Process successful response
            logger.debug("Processing successful response")
            temperature = data['current']['temperature']
            location = f"{data['location']['name']}, {data['location']['region']}"
            local_time = data['location']['localtime']
            description = data['current']['weather_descriptions'][0]

            self.weather_display.text = (
                f"[b]{location}[/b]\n\n"
                f"[color=#666666]{local_time}[/color]\n\n"
                f"[size=24sp][color=#2196F3]{temperature}°F[/color][/size]\n\n"
                f"[i]{description}[/i]"
            )

            weather_icon_url = data['current']['weather_icons'][0]
            logger.debug(f"Setting weather icon URL: {weather_icon_url}")
            self.weather_image.source = weather_icon_url

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}", exc_info=True)
            self.weather_display.text = f"[color=ff3333]Network error: {str(e)}[/color]"
            self.weather_image.source = ''
        except KeyError as e:
            logger.error(f"Failed to parse response: {str(e)}", exc_info=True)
            self.weather_display.text = "[color=ff3333]Failed to parse weather data[/color]"
            self.weather_image.source = ''
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.weather_display.text = "[color=ff3333]An unexpected error occurred[/color]"
            self.weather_image.source = ''
        finally:
            logger.debug("=== Weather request completed ===\n")


class WeatherApp(App):
    def build(self):
        logger.debug("Building WeatherApp")
        return WeatherAppLayout()


if __name__ == '__main__':
    try:
        logger.debug("Starting WeatherApp")
        logger.debug(f"Window density before app start: {Window._density}")
        logger.debug(f"Window size before app start: {Window.size}")
        WeatherApp().run()
    except Exception as e:
        logger.error("Application crashed", exc_info=True)
        if hasattr(Window, '_density'):
            logger.error(f"Window density at crash: {Window._density}")
        if hasattr(Window, 'size'):
            logger.error(f"Window size at crash: {Window.size}")
