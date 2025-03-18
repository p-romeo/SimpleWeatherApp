"""
A simple weather app, enter a zip code and get a forecast!
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict

import requests
from dotenv import load_dotenv
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

class LocationStorage:
    def __init__(self, filename: str = "saved_locations.json"):
        self.filename = filename
        self.locations: Dict[str, str] = {}  # zip_code -> location_name
        self.load_locations()
    
    def load_locations(self) -> None:
        """Load saved locations from JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.locations = json.load(f)
                logger.debug(f"Loaded {len(self.locations)} locations from {self.filename}")
        except Exception as e:
            logger.error(f"Failed to load locations: {e}")
            self.locations = {}
    
    def save_locations(self) -> None:
        """Save locations to JSON file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.locations, f, indent=2)
            logger.debug(f"Saved {len(self.locations)} locations to {self.filename}")
        except Exception as e:
            logger.error(f"Failed to save locations: {e}")
    
    def add_location(self, zip_code: str, location_name: str) -> None:
        """Add a new location"""
        self.locations[zip_code] = location_name
        self.save_locations()
    
    def remove_location(self, zip_code: str) -> None:
        """Remove a location"""
        if zip_code in self.locations:
            del self.locations[zip_code]
            self.save_locations()
    
    def get_locations(self) -> Dict[str, str]:
        """Get all saved locations"""
        return self.locations

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
Window.size = (800, 900)
Window.minimum_width = 400
Window.minimum_height = 600
Window.clearcolor = get_color_from_hex('#f0f0f0')
# Ensure proper window density
Window._density = 1.0 if not Window._density else Window._density

class WeatherAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Initializing WeatherAppLayout")
        self.orientation = 'vertical'
        self.padding = [40, 40]  # Increased padding for larger window
        self.spacing = 30  # Increased spacing for better visual hierarchy
        
        self.api_key = api_key
        self.base_url = base_url
        self.location_storage = LocationStorage()

        # Create UI components
        self._create_ui_components()
        self._update_saved_locations()
        logger.debug("UI components initialized")

    def _create_ui_components(self):
        """Create and initialize all UI components"""
        # Title
        title_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=80,
            padding=[0, 10]
        )
        title_layout.add_widget(Label(
            text="Weather Forecast",
            font_size='32sp',  # Increased font size
            size_hint_y=None,
            height=60,
            color=get_color_from_hex('#2196F3')
        ))
        self.add_widget(title_layout)

        # Input section
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,  # Increased height
            spacing=20  # Increased spacing
        )
        
        self.zip_code = TextInput(
            multiline=False,
            hint_text='Enter ZIP code',
            padding=[20, 15, 0, 15],  # Increased padding
            size_hint_x=0.7,
            font_size='18sp',  # Increased font size
            background_color=get_color_from_hex('#ffffff'),
            foreground_color=get_color_from_hex('#000000')
        )
        self.zip_code.bind(on_text_validate=self.get_weather)
        
        self.get_weather_button = Button(
            text='Get Weather',
            size_hint_x=0.3,
            font_size='18sp',  # Increased font size
            background_color=get_color_from_hex('#2196F3'),
            background_normal=''
        )
        self.get_weather_button.bind(on_press=self.get_weather)
        
        input_layout.add_widget(self.zip_code)
        input_layout.add_widget(self.get_weather_button)
        self.add_widget(input_layout)

        # Save location button
        self.save_button = Button(
            text='Save Location',
            size_hint_y=None,
            height=50,  # Increased height
            font_size='18sp',  # Increased font size
            background_color=get_color_from_hex('#4CAF50'),
            background_normal='',
            disabled=True
        )
        self.save_button.bind(on_press=self.save_current_location)
        self.add_widget(self.save_button)

        # Weather display section
        weather_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=400,  # Fixed height for weather section
            spacing=20
        )

        # Weather image
        self.weather_image = AsyncImage(
            size_hint=(None, None),
            size=(200, 200),  # Larger image
            pos_hint={'center_x': 0.5}
        )
        weather_section.add_widget(self.weather_image)

        # Weather information display
        self.weather_display = Label(
            text='',
            markup=True,
            font_size='24sp',  # Increased font size
            halign='center',
            valign='middle',
            color=get_color_from_hex('#333333'),
            size_hint_y=None,
            height=200
        )
        self.weather_display.bind(size=self.weather_display.setter('text_size'))
        weather_section.add_widget(self.weather_display)
        
        self.add_widget(weather_section)

        # Saved locations section with flexible height
        locations_section = BoxLayout(
            orientation='vertical',
            size_hint_y=1,  # Take remaining space
            spacing=10
        )

        saved_locations_label = Label(
            text="Saved Locations",
            font_size='24sp',  # Increased font size
            size_hint_y=None,
            height=40,
            color=get_color_from_hex('#2196F3')
        )
        locations_section.add_widget(saved_locations_label)

        # Create a ScrollView that takes remaining space
        scroll_view = ScrollView(
            size_hint_y=1,  # Take remaining space
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # Container for saved location buttons
        self.saved_locations_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10  # Increased spacing
        )
        self.saved_locations_container.bind(
            minimum_height=self.saved_locations_container.setter('height')
        )
        
        scroll_view.add_widget(self.saved_locations_container)
        locations_section.add_widget(scroll_view)
        self.add_widget(locations_section)

    def _update_saved_locations(self):
        """Update the saved locations display"""
        self.saved_locations_container.clear_widgets()
        
        for zip_code, location_name in self.location_storage.get_locations().items():
            # Create a layout for the location entry
            entry_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=60,  # Increased height
                spacing=10
            )
            
            location_button = Button(
                text=f"{location_name} ({zip_code})",
                size_hint_x=1,
                height=60,  # Increased height
                font_size='18sp',  # Increased font size
                background_color=get_color_from_hex('#E3F2FD'),
                background_normal='',
                color=get_color_from_hex('#333333')
            )
            location_button.bind(on_press=lambda btn, zip=zip_code: self.load_saved_location(zip))
            
            # Add the location button
            entry_layout.add_widget(location_button)
            
            delete_button = Button(
                text='×',
                size_hint_x=None,
                width=60,  # Square button
                font_size='24sp',  # Increased font size
                background_color=get_color_from_hex('#FF5252'),
                background_normal=''
            )
            delete_button.bind(on_press=lambda btn, zip=zip_code: self.delete_location(zip))
            entry_layout.add_widget(delete_button)
            
            self.saved_locations_container.add_widget(entry_layout)

    def save_current_location(self, instance):
        """Save the current location"""
        current_zip = self.zip_code.text
        if current_zip and len(current_zip) == 5 and current_zip.isnumeric():
            location_name = self.weather_display.text.split('\n')[0].replace('[b]', '').replace('[/b]', '')
            self.location_storage.add_location(current_zip, location_name)
            self._update_saved_locations()
            logger.debug(f"Saved location: {location_name} ({current_zip})")

    def load_saved_location(self, zip_code: str):
        """Load weather for a saved location"""
        self.zip_code.text = zip_code
        self.get_weather(None)

    def delete_location(self, zip_code: str):
        """Delete a saved location"""
        self.location_storage.remove_location(zip_code)
        self._update_saved_locations()
        logger.debug(f"Deleted location: {zip_code}")

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
        
        # Disable save button initially
        self.save_button.disabled = True
        
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
            
            # Enable save button on successful weather fetch
            self.save_button.disabled = False

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
