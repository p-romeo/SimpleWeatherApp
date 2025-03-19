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

from src.weather_app.api.weather_client import WeatherStackClient, WeatherData
from src.weather_app.storage.location_storage import LocationStorage

# Initialize logger
logger = logging.getLogger(__name__)

class WeatherCard(MDCard):
    """A Material Design card for displaying weather information."""
    
    temperature = StringProperty("--°F")
    location = StringProperty("--")
    description = StringProperty("--")
    humidity = StringProperty("--%")
    wind_speed = StringProperty("-- mph")
    feels_like = StringProperty("--°F")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(300), dp(200))
        self.padding = dp(16)
        self.spacing = dp(8)
        self.elevation = 4
        self._create_content()
        
    def _create_content(self):
        """Create the card content with weather information."""
        # Location and temperature header
        header = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        location_label = MDLabel(
            text=self.location,
            font_style="H6",
            theme_text_color="Primary"
        )
        temp_label = MDLabel(
            text=self.temperature,
            font_style="H4",
            theme_text_color="Primary"
        )
        header.add_widget(location_label)
        header.add_widget(Widget())
        header.add_widget(temp_label)
        
        # Weather details
        details = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(4))
        desc_label = MDLabel(
            text=self.description,
            font_style="Body1",
            theme_text_color="Secondary"
        )
        humidity_label = MDLabel(
            text=f"Humidity: {self.humidity}",
            font_style="Body2",
            theme_text_color="Secondary"
        )
        wind_label = MDLabel(
            text=f"Wind: {self.wind_speed}",
            font_style="Body2",
            theme_text_color="Secondary"
        )
        feels_like_label = MDLabel(
            text=f"Feels like: {self.feels_like}",
            font_style="Body2",
            theme_text_color="Secondary"
        )
        
        details.add_widget(desc_label)
        details.add_widget(humidity_label)
        details.add_widget(wind_label)
        details.add_widget(feels_like_label)
        
        self.add_widget(header)
        self.add_widget(details)

class WeatherAppLayout(MDScreen):
    """Main layout for the Weather App using Material Design."""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage, **kwargs):
        super().__init__(**kwargs)
        self.api_client = api_client
        self.location_storage = location_storage
        self.weather_cards: List[WeatherCard] = []
        self._create_ui()
        self._load_saved_locations()
        
    def _create_ui(self):
        """Create the main UI layout."""
        # Main container
        main_layout = MDBoxLayout(orientation="vertical", spacing=dp(16), padding=dp(16))
        
        # Top app bar
        self.top_bar = MDTopAppBar(
            title="Weather App",
            elevation=4,
            pos_hint={"top": 1}
        )
        
        # Search section
        search_layout = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        self.zip_input = MDTextField(
            hint_text="Enter ZIP code",
            helper_text="Enter a valid US ZIP code",
            helper_text_mode="on_error",
            max_text_length=5,
            size_hint_x=0.7
        )
        self.search_button = MDRaisedButton(
            text="Search",
            on_release=self._on_search,
            size_hint_x=0.3
        )
        search_layout.add_widget(self.zip_input)
        search_layout.add_widget(self.search_button)
        
        # Progress bar container
        self.progress_container = MDBoxLayout(adaptive_height=True)
        with self.progress_container.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.progress_rect = Rectangle(pos=self.progress_container.pos, size=self.progress_container.size)
        self.progress_container.bind(pos=self._update_rect, size=self._update_rect)
        
        self.progress_bar = ProgressBar(max=100, value=0)
        self.progress_container.add_widget(self.progress_bar)
        self.progress_container.opacity = 0
        
        # Location list
        self.location_list = MDList()
        scroll_view = ScrollView()
        scroll_view.add_widget(self.location_list)
        
        # Add all widgets to main layout
        main_layout.add_widget(self.top_bar)
        main_layout.add_widget(search_layout)
        main_layout.add_widget(self.progress_container)
        main_layout.add_widget(scroll_view)
        
        self.add_widget(main_layout)
        
    def _update_rect(self, instance, value):
        """Update the progress bar background rectangle."""
        self.progress_rect.pos = instance.pos
        self.progress_rect.size = instance.size
        
    def _load_saved_locations(self):
        """Load and display saved locations."""
        try:
            locations = self.location_storage.get_locations()
            for zip_code in locations:
                asyncio.create_task(self._fetch_weather(zip_code))
        except Exception as e:
            logger.error(f"Error loading saved locations: {e}")
            self._show_error("Failed to load saved locations")
            
    async def _fetch_weather(self, zip_code: str) -> None:
        """Fetch weather data for a ZIP code."""
        try:
            logger.debug(f"[Fetching weather data for ZIP code] {zip_code}")
            weather_data = await self.api_client.get_weather(zip_code)
            logger.debug(f"[Received weather data] {weather_data}")
            
            Clock.schedule_once(lambda dt: self._update_weather_display(zip_code, weather_data))
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            Clock.schedule_once(lambda dt: self._show_error(f"Failed to fetch weather data: {str(e)}"))
            
    def _update_weather_display(self, zip_code: str, weather_data: WeatherData) -> None:
        """Update the weather display with new data."""
        try:
            logger.debug("Creating weather card")
            card = WeatherCard()
            card.temperature = f"{weather_data.temperature}°F"
            card.location = weather_data.location
            card.description = weather_data.description
            card.humidity = f"{weather_data.humidity}%"
            card.wind_speed = f"{weather_data.wind_speed} mph"
            card.feels_like = f"{weather_data.feels_like}°F"
            
            logger.debug("[Setting card properties]")
            logger.debug(f"  [  Temperature] {card.temperature}")
            logger.debug(f"  [  Location  ] {card.location}")
            logger.debug(f"  [  Description] {card.description}")
            logger.debug(f"  [  Humidity  ] {card.humidity}")
            logger.debug(f"  [  Wind Speed] {card.wind_speed}")
            
            # Clear existing cards if this is a new search
            if zip_code not in self.location_storage.get_locations():
                logger.debug("Clearing existing cards for new search")
                self.location_list.clear_widgets()
                self.weather_cards.clear()
            
            logger.debug("Adding card to location list")
            self.location_list.add_widget(card)
            self.weather_cards.append(card)
            
            # Animate card appearance
            card.opacity = 0
            anim = Animation(opacity=1, duration=0.3)
            anim.start(card)
            
            # Save new location if not already stored
            if zip_code not in self.location_storage.get_locations():
                logger.debug(f"[Saving new location] {zip_code}")
                self.location_storage.add_location(zip_code, weather_data.location)
                
            # Bind the location list size to its children
            self.location_list.bind(minimum_height=self.location_list.setter('height'))
            
        except Exception as e:
            logger.error(f"[Error updating weather display] {e}")
            self._show_error(f"Failed to update weather display: {str(e)}")
            
    def _on_search(self, instance) -> None:
        """Handle search button click."""
        zip_code = self.zip_input.text.strip()
        if not zip_code:
            self.zip_input.error = True
            return
            
        self.zip_input.error = False
        asyncio.create_task(self._fetch_weather(zip_code))
        
    def _show_error(self, message: str) -> None:
        """Show an error popup."""
        error_popup = Popup(
            title='Error',
            content=MDLabel(text=message),
            size_hint=(None, None),
            size=(dp(300), dp(200)),
            auto_dismiss=True
        )
        error_popup.open()

class WeatherApp(MDApp):
    """Main application class using Material Design."""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage, **kwargs):
        super().__init__(**kwargs)
        self.api_client = api_client
        self.location_storage = location_storage
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
    def build(self):
        """Build the application UI."""
        return WeatherAppLayout(
            api_client=self.api_client,
            location_storage=self.location_storage
        )
        
    def cleanup(self):
        """Clean up application resources."""
        try:
            self.location_storage.save()
            logger.info("Weather app cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during weather app cleanup: {e}") 