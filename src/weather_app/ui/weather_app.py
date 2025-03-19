"""
Weather App UI implementation using Kivy

This module provides the user interface for the Weather App using Kivy.
Features include:
- Real-time weather updates
- Location management
- Error handling and user feedback
- Responsive design
- Asynchronous data fetching
"""

import logging
from typing import Optional, Dict, Any, Tuple
from threading import Thread, Lock
from queue import Queue
from datetime import datetime
import time

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

from src.weather_app.api.weather_client import WeatherStackClient, WeatherData
from src.weather_app.storage.location_storage import LocationStorage

logger = logging.getLogger(__name__)

class ErrorPopup(Popup):
    """Custom popup for displaying errors"""
    
    def __init__(self, title: str, message: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.3)
        self.auto_dismiss = True
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(
            text=message,
            text_size=(self.width - 20, None),
            halign='center',
            valign='middle'
        ))
        
        ok_button = Button(
            text='OK',
            size_hint_y=None,
            height=40,
            background_color=get_color_from_hex('#2196F3'),
            background_normal=''
        )
        ok_button.bind(on_press=self.dismiss)
        content.add_widget(ok_button)
        
        self.content = content

class WeatherCard(ButtonBehavior, BoxLayout):
    """Custom card widget for displaying weather information"""
    
    temperature = StringProperty('--°F')
    location = StringProperty('')
    description = StringProperty('')
    humidity = StringProperty('--%')
    wind_speed = StringProperty('-- mph')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(15)
        self.spacing = dp(10)
        self.background_normal = ''
        self.background_color = get_color_from_hex('#FFFFFF')
        
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Light gray background
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        
        # Bind size to update the background rectangle
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Create content
        self._create_content()
        
        # Bind property changes to update content
        self.bind(
            temperature=self._update_temperature,
            location=self._update_location,
            description=self._update_description,
            humidity=self._update_humidity,
            wind_speed=self._update_wind_speed
        )
        
    def _update_rect(self, instance, value):
        """Update the background rectangle when the widget size changes"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            
    def _create_content(self):
        """Create the card content"""
        # Location and temperature
        header = BoxLayout(size_hint_y=None, height=dp(40))
        self.location_label = Label(
            text=self.location,
            font_size='18sp',
            bold=True,
            color=get_color_from_hex('#333333')
        )
        self.temp_label = Label(
            text=self.temperature,
            font_size='24sp',
            bold=True,
            color=get_color_from_hex('#2196F3')
        )
        header.add_widget(self.location_label)
        header.add_widget(self.temp_label)
        self.add_widget(header)
        
        # Weather condition
        self.condition_label = Label(
            text=self.description,
            font_size='16sp',
            color=get_color_from_hex('#666666')
        )
        self.add_widget(self.condition_label)
        
        # Details grid
        details = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(80)
        )
        
        # Humidity
        humidity_box = BoxLayout(orientation='vertical')
        humidity_box.add_widget(Label(
            text='Humidity',
            font_size='12sp',
            color=get_color_from_hex('#999999')
        ))
        self.humidity_label = Label(
            text=self.humidity,
            font_size='14sp',
            color=get_color_from_hex('#333333')
        )
        humidity_box.add_widget(self.humidity_label)
        details.add_widget(humidity_box)
        
        # Wind Speed
        wind_box = BoxLayout(orientation='vertical')
        wind_box.add_widget(Label(
            text='Wind Speed',
            font_size='12sp',
            color=get_color_from_hex('#999999')
        ))
        self.wind_speed_label = Label(
            text=self.wind_speed,
            font_size='14sp',
            color=get_color_from_hex('#333333')
        )
        wind_box.add_widget(self.wind_speed_label)
        details.add_widget(wind_box)
        
        self.add_widget(details)
        
    def _update_temperature(self, instance, value):
        """Update temperature label"""
        self.temp_label.text = value
        
    def _update_location(self, instance, value):
        """Update location label"""
        self.location_label.text = value
        
    def _update_description(self, instance, value):
        """Update description label"""
        self.condition_label.text = value
        
    def _update_humidity(self, instance, value):
        """Update humidity label"""
        self.humidity_label.text = value
        
    def _update_wind_speed(self, instance, value):
        """Update wind speed label"""
        self.wind_speed_label.text = value

class WeatherAppLayout(BoxLayout):
    """Main application layout"""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        self.api_client = api_client
        self.location_storage = location_storage
        self.weather_cards = []
        
        # Set background color
        with self.canvas.before:
            Color(0.92, 0.92, 0.92, 1)  # Light gray background
            Rectangle(pos=self.pos, size=self.size)
        
        # Bind size to update the background rectangle
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Create UI components
        self._create_ui_components()
        
        # Load saved locations
        self._load_saved_locations()
        
    def _update_rect(self, instance, value):
        """Update the background rectangle when the widget size changes"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.92, 0.92, 0.92, 1)
            Rectangle(pos=self.pos, size=self.size)
            
    def _create_ui_components(self):
        """Create all UI components"""
        # Create header
        self._create_header()
        
        # Create search section
        self._create_search_section()
        
        # Create weather section
        self._create_weather_section()
        
        # Create location list
        self._create_location_list()
        
    def _create_header(self):
        """Create the application header"""
        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )
        
        title = Label(
            text='Weather App',
            font_size='24sp',
            bold=True,
            color=get_color_from_hex('#2196F3'),
            size_hint_x=0.7
        )
        
        refresh_btn = Button(
            text='⟳',
            font_size='24sp',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#2196F3'),
            background_normal='',
            on_press=self._refresh_all_weather
        )
        
        header.add_widget(title)
        header.add_widget(refresh_btn)
        self.add_widget(header)
        
    def _create_search_section(self):
        """Create the search section"""
        search_section = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        self.zip_input = TextInput(
            hint_text='Enter ZIP code',
            multiline=False,
            size_hint_x=0.7,
            background_color=get_color_from_hex('#FFFFFF'),
            foreground_color=get_color_from_hex('#333333'),
            cursor_color=get_color_from_hex('#2196F3'),
            padding=[dp(10), dp(10)]
        )
        
        search_btn = Button(
            text='Search',
            size_hint_x=0.3,
            background_color=get_color_from_hex('#2196F3'),
            background_normal='',
            on_press=self._search_weather
        )
        
        search_section.add_widget(self.zip_input)
        search_section.add_widget(search_btn)
        self.add_widget(search_section)
        
    def _create_weather_section(self):
        """Create the weather display section"""
        self.weather_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(400),
            spacing=dp(20)
        )
        
        # Create loading spinner
        self.loading_spinner = Spinner(
            text='Loading weather data...',
            values=('Loading weather data...',),
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            pos_hint={'center_x': 0.5},
            background_color=get_color_from_hex('#2196F3'),
            background_normal='',
        )
        self.loading_spinner.opacity = 0
        self.weather_section.add_widget(self.loading_spinner)
        
        # Create progress bar container
        progress_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(200), dp(4)),
            pos_hint={'center_x': 0.5}
        )
        
        # Add background color using canvas
        with progress_container.canvas.before:
            Color(*get_color_from_hex('#E0E0E0'))
            self.progress_bg = Rectangle(pos=progress_container.pos, size=progress_container.size)
        
        # Update rectangle position and size when the container changes
        def update_rect(instance, value):
            self.progress_bg.pos = instance.pos
            self.progress_bg.size = instance.size
        progress_container.bind(pos=update_rect, size=update_rect)
        
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(1, 1)
        )
        progress_container.add_widget(self.progress_bar)
        progress_container.opacity = 0
        self.weather_section.add_widget(progress_container)
        
        self.add_widget(self.weather_section)
        
    def _create_location_list(self):
        """Create the location list section"""
        # Create a container for the scroll view
        scroll_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(400)  # Fixed height for the scroll area
        )
        
        # Create the grid layout for weather cards
        self.location_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        
        # Make the grid layout expand to fit its children
        self.location_list.bind(
            minimum_height=self.location_list.setter('height')
        )
        
        # Create the scroll view
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(10),
            scroll_type=['bars', 'content']
        )
        
        # Add the grid layout to the scroll view
        scroll.add_widget(self.location_list)
        
        # Add the scroll view to the container
        scroll_container.add_widget(scroll)
        
        # Add the container to the main layout
        self.add_widget(scroll_container)
        
    def _create_weather_card(self, weather_data: WeatherData) -> WeatherCard:
        """Create a weather card for the given weather data"""
        try:
            logger.debug("Creating WeatherCard with data:")
            logger.debug(f"  Location: {weather_data.location}")
            logger.debug(f"  Temperature: {weather_data.temperature}")
            logger.debug(f"  Description: {weather_data.description}")
            logger.debug(f"  Humidity: {weather_data.humidity}")
            logger.debug(f"  Wind Speed: {weather_data.wind_speed}")
            
            card = WeatherCard()
            card.size_hint_y = None  # Allow the card to have a fixed height
            card.height = dp(200)    # Set a fixed height for the card
            card.temperature = f"{weather_data.temperature}°F"
            card.location = weather_data.location
            card.description = weather_data.description
            card.humidity = f"{weather_data.humidity}%"
            card.wind_speed = f"{weather_data.wind_speed} mph"
            
            # Add animation for card appearance
            card.opacity = 0
            anim = Animation(opacity=1, duration=0.3)
            anim.start(card)
            
            return card
        except Exception as e:
            logger.error(f"Error creating weather card: {str(e)}", exc_info=True)
            raise
        
    def _show_loading(self, show: bool = True):
        """Show or hide loading indicators"""
        if show:
            self.loading_spinner.opacity = 1
            self.progress_bar.parent.opacity = 1
            self.progress_bar.value = 0
        else:
            self.loading_spinner.opacity = 0
            self.progress_bar.parent.opacity = 0
            
    def _update_progress(self, value: float):
        """Update the progress bar value"""
        self.progress_bar.value = value
        
    def _show_error(self, title: str, message: str):
        """Show an error popup"""
        popup = ErrorPopup(title=title, message=message)
        popup.open()
        
    def _refresh_all_weather(self, instance=None):
        """Refresh weather data for all locations"""
        self._show_loading()
        locations = self.location_storage.get_locations()
        total = len(locations)
        
        for i, location in enumerate(locations):
            self._update_progress((i + 1) / total * 100)
            self._fetch_weather(location)
            
        self._show_loading(False)
        
    def _search_weather(self, instance=None):
        """Search for weather by ZIP code"""
        zip_code = self.zip_input.text.strip()
        if not zip_code:
            self._show_error('Error', 'Please enter a ZIP code')
            return
            
        self._show_loading()
        self._fetch_weather(zip_code)
        
    def _fetch_weather(self, zip_code: str):
        """Fetch weather data for a location"""
        try:
            logger.debug(f"Fetching weather data for ZIP code: {zip_code}")
            weather_data = self.api_client.get_weather(zip_code)
            logger.debug(f"Received weather data: {weather_data.__dict__}")
            self._update_weather_display(weather_data, zip_code)
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}", exc_info=True)
            self._show_error('Error', str(e))
        finally:
            self._show_loading(False)
            
    def _update_weather_display(self, weather_data: WeatherData, zip_code: str):
        """Update the weather display with new data"""
        try:
            logger.debug("Creating weather card")
            # Create and add new weather card
            card = WeatherCard()
            card.size_hint_y = None  # Allow the card to have a fixed height
            card.height = dp(200)    # Set a fixed height for the card
            
            # Update card properties
            logger.debug("Setting card properties:")
            logger.debug(f"  Temperature: {weather_data.temperature}°F")
            logger.debug(f"  Location: {weather_data.location}")
            logger.debug(f"  Description: {weather_data.description}")
            logger.debug(f"  Humidity: {weather_data.humidity}%")
            logger.debug(f"  Wind Speed: {weather_data.wind_speed} mph")
            
            card.temperature = f"{weather_data.temperature}°F"
            card.location = str(weather_data.location)
            card.description = str(weather_data.description)
            card.humidity = f"{weather_data.humidity}%"
            card.wind_speed = f"{weather_data.wind_speed} mph"
            
            # Clear existing cards if this is a search (not a saved location)
            if zip_code not in self.location_storage.get_locations():
                logger.debug("Clearing existing cards for new search")
                self.location_list.clear_widgets()
                self.weather_cards = []
            
            logger.debug("Adding card to location list")
            self.location_list.add_widget(card)
            self.weather_cards.append(card)
            
            # Add animation for card appearance
            card.opacity = 0
            anim = Animation(opacity=1, duration=0.3)
            anim.start(card)
            
            # Save location if not already saved
            locations = self.location_storage.get_locations()
            if zip_code not in locations:
                logger.debug(f"Saving new location: {zip_code}")
                self.location_storage.add_location(zip_code)
                
            # Bind the location list size to its children
            self.location_list.bind(minimum_height=self.location_list.setter('height'))
            
        except Exception as e:
            logger.error(f"Error updating weather display: {str(e)}", exc_info=True)
            self._show_error('Error', 'Failed to display weather data')
            
    def _load_saved_locations(self):
        """Load and display saved locations"""
        locations = self.location_storage.get_locations()
        for location in locations:
            self._fetch_weather(location)
            
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.api_client.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class WeatherApp(App):
    """Main application class"""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage):
        super().__init__()
        self.api_client = api_client
        self.location_storage = location_storage
        
    def build(self) -> WeatherAppLayout:
        return WeatherAppLayout(
            api_client=self.api_client,
            location_storage=self.location_storage
        )
        
    def cleanup(self) -> None:
        try:
            if hasattr(self.root, 'cleanup'):
                self.root.cleanup()
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            
    def on_stop(self) -> None:
        self.cleanup() 