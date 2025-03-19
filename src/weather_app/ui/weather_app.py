"""
Weather App UI Implementation

This module implements the user interface for the Weather App using KivyMD.
It provides:
1. A modern Material Design interface
2. Real-time weather updates
3. Location management
4. Error handling
5. Asynchronous data fetching
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from threading import Thread, Lock
from queue import Queue
from datetime import datetime
import time
import os

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.icon_definitions import md_icons
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout

from weather_app.api.weather_client import WeatherStackClient, WeatherData
from weather_app.storage.location_storage import LocationStorage
from weather_app.ui.weather_card import WeatherCard

# Initialize logger
logger = logging.getLogger(__name__)

class FocusTextInput(TextInput):
    """A TextInput that properly handles focus and touch events."""
    
    def on_touch_down(self, touch):
        """Handle touch down events."""
        if self.collide_point(*touch.pos):
            self.focus = True
            return super().on_touch_down(touch)
        return False

class WeatherAppLayout(MDScreen):
    """Main layout for the weather application."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize components
        api_key = os.getenv('WEATHERSTACK_API_KEY', '').strip()
        if not api_key:
            self._show_error("API key not found. Please check your environment variables.")
            return
            
        self.weather_client = WeatherStackClient(
            api_key=api_key,
            cache_timeout=300,  # 5 minutes
            request_timeout=10   # 10 seconds
        )
        
        # Ensure data directory exists
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        storage_file = os.path.join(data_dir, 'locations.json')
        self.location_storage = LocationStorage(storage_file=storage_file)
        
        self.orientation = 'vertical'
        self.weather_cards = {}  # Dictionary to store cards by zip code
        self._setup_ui()
        self._load_saved_locations()
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main layout
        main_layout = BoxLayout(
            orientation='vertical',
            spacing="16dp",
            padding="16dp"
        )
        
        # Top app bar
        self.top_bar = MDTopAppBar(
            title="Weather App",
            elevation=4,
            pos_hint={"top": 1}
        )
        main_layout.add_widget(self.top_bar)
        
        # Search section with card
        search_card = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height="56dp",
            padding="8dp",
            spacing="8dp",
            pos_hint={"top": 0.95}
        )
        
        # Input field
        self.search_input = TextInput(
            text='',
            hint_text='Enter ZIP code',
            multiline=False,
            size_hint_x=0.7,
            height="40dp",
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            padding=(15, 10),
            font_size='16sp'
        )
        self.search_input.bind(
            on_text_validate=self._on_search,
            focus=self._on_focus
        )
        search_card.add_widget(self.search_input)
        
        # Save button
        self.save_button = MDRaisedButton(
            text="Save",
            size_hint_x=0.3,
            height="40dp",
            on_release=lambda x: self._on_search(self.search_input)
        )
        search_card.add_widget(self.save_button)
        main_layout.add_widget(search_card)
        
        # Location list with scroll view
        scroll_view = ScrollView(
            do_scroll_x=False,
            size_hint=(1, 1)
        )
        self.location_list = MDList()
        scroll_view.add_widget(self.location_list)
        main_layout.add_widget(scroll_view)
        
        # Add main layout to screen
        self.add_widget(main_layout)
        
        # Set initial focus to search input
        Clock.schedule_once(lambda dt: setattr(self.search_input, 'focus', True), 0.1)
    
    def _load_saved_locations(self):
        """Load and display saved locations."""
        try:
            locations = self.location_storage.get_locations()
            for zip_code in locations:
                Clock.schedule_once(
                    lambda dt, code=zip_code: self._fetch_weather(code),
                    0.1
                )
        except Exception as e:
            logger.error(f"Error loading saved locations: {e}")
            self._show_error("Failed to load saved locations")
    
    def _validate_zip_code(self, zip_code: str) -> bool:
        """Validate ZIP code format."""
        if not zip_code.isdigit():
            self._show_error("ZIP code must contain only numbers")
            return False
        
        if len(zip_code) != 5:
            self._show_error("ZIP code must be 5 digits")
            return False
        
        return True
    
    def _on_search(self, instance):
        """Handle search input submission."""
        zip_code = instance.text.strip()
        if zip_code and self._validate_zip_code(zip_code):
            self._fetch_weather(zip_code)
            self.search_input.text = ""  # Clear the input field
            self.search_input.focus = True  # Keep focus on input field
    
    def _fetch_weather(self, zip_code: str):
        """Fetch weather data for a given ZIP code."""
        try:
            weather_data = self.weather_client.get_weather(zip_code)
            if weather_data:
                self._update_weather_display(weather_data)
            else:
                self._show_error(f"No weather data found for ZIP code {zip_code}")
        except ValueError as e:
            logger.error(f"Invalid weather data for {zip_code}: {e}")
            self._show_error(f"Invalid weather data for {zip_code}")
        except ConnectionError as e:
            logger.error(f"Connection error for {zip_code}: {e}")
            self._show_error("Connection error. Please check your internet connection.")
        except Exception as e:
            logger.error(f"Error fetching weather for {zip_code}: {e}")
            self._show_error(f"Failed to fetch weather for {zip_code}")
    
    def _update_weather_display(self, weather_data: WeatherData):
        """Update the weather display with new data."""
        zip_code = weather_data.zip_code
        
        # Create or update card
        if zip_code not in self.weather_cards:
            card = WeatherCard()
            self.weather_cards[zip_code] = card
            self.location_list.add_widget(card)
            
            # Save new location
            try:
                self.location_storage.add_location(zip_code, weather_data.location)
            except Exception as e:
                logger.error(f"Failed to save location: {e}")
                self._show_error("Failed to save location")
            
            # Animate card appearance
            card.opacity = 0
            anim = Animation(opacity=1, duration=0.3)
            anim.start(card)
        
        # Update card data
        card = self.weather_cards[zip_code]
        card.location_name = weather_data.location
        card.zip_code = weather_data.zip_code
        card.temperature = str(weather_data.temperature)
        card.description = weather_data.description
        card.wind_speed = str(weather_data.wind_speed)
        card.humidity = str(weather_data.humidity)
    
    def _show_error(self, message: str):
        """Show an error message to the user."""
        logger.error(message)
        # Create and show error popup
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()
    
    def _on_focus(self, instance, value):
        """Handle input field focus changes."""
        if value:  # If focused
            instance.background_color = (1, 1, 1, 1)
        else:
            instance.background_color = (0.95, 0.95, 0.95, 1)

class WeatherApp(MDApp):
    """Main application class."""
    
    def build(self):
        """Build the application."""
        # Configure window
        Window.size = (400, 600)
        Window.minimum_width = 400
        Window.minimum_height = 600
        Window.softinput_mode = 'below_target'  # Keep input field visible when keyboard appears
        Window.keyboard_anim_args = {'d': .2, 't': 'in_out_expo'}
        Window.keyboard_padding = 0
        
        # Set up theme
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.2
        
        # Create and return the main layout
        return WeatherAppLayout()
    
    def on_start(self):
        """Called when the application starts."""
        # Bind keyboard events
        Window.bind(
            on_key_down=self._on_keyboard_down,
            on_keyboard=self._on_keyboard
        )
        
        # Set window focus
        Window.request_keyboard(
            self._keyboard_closed, self.root
        )
    
    def on_stop(self):
        """Clean up when the application stops."""
        try:
            self.root.weather_client.cleanup()
            self.root.location_storage.save()
        except Exception as e:
            logger.error(f"Error during weather app cleanup: {e}")
    
    def _keyboard_closed(self):
        """Handle keyboard close."""
        Window.unbind(on_keyboard=self._on_keyboard)
    
    def _on_keyboard(self, window, key, *args):
        """Handle keyboard events."""
        if key == 27:  # ESC key
            return True  # Prevent app from closing
        return False
    
    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        """Handle keyboard down events."""
        if keycode == 40:  # Enter key
            self.root.search_input.focus = True
            return True
        return False 