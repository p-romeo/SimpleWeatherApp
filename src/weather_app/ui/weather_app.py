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
from kivy.utils import platform
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from dotenv import load_dotenv

from weather_app.api.weather_client import WeatherStackClient, WeatherData
from weather_app.storage.location_storage import LocationStorage
from weather_app.ui.weather_card import WeatherCard

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('WEATHERSTACK_API_KEY', '').strip()
if not API_KEY:
    logger.error("WEATHERSTACK_API_KEY environment variable is not set")
    raise ValueError("API key not found. Please check your environment variables.")

class FocusTextInput(TextInput):
    """A TextInput that properly handles focus and touch events."""
    
    def on_touch_down(self, touch):
        """Handle touch down events."""
        if self.collide_point(*touch.pos):
            self.focus = True
            return super().on_touch_down(touch)
        return False

class WeatherAppLayout(MDBoxLayout):
    """
    Main layout class for the Weather App interface.
    Manages the weather display, search functionality, and location storage.
    """
    
    def __init__(self, **kwargs):
        """Initialize the WeatherAppLayout with search box and weather display area."""
        super().__init__(**kwargs)
        
        # Initialize components
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Initialize weather client and storage
        self.weather_client = WeatherStackClient(API_KEY)
        self.location_storage = LocationStorage()
        
        # Create layout for weather cards
        self.weather_cards_layout = MDGridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(10),
            adaptive_height=True
        )
        
        # Dictionary to keep track of weather cards
        self.weather_cards = {}
        self._weather_lock = Lock()  # Add lock for thread safety
        self._fetch_queue = Queue()  # Add queue for weather fetching
        
        # Start weather fetching thread
        self._fetch_thread = Thread(target=self._weather_fetch_worker, daemon=True)
        self._fetch_thread.start()
        
        # Set up the UI components
        self._setup_search_box()
        self._setup_scroll_view()
        
        # Load saved locations
        self._load_saved_locations()
    
    def _weather_fetch_worker(self):
        """Worker thread for fetching weather data."""
        while True:
            try:
                zip_code = self._fetch_queue.get()
                if zip_code is None:  # Shutdown signal
                    break
                    
                try:
                    weather_data = self.weather_client.get_weather(zip_code)
                    if weather_data:
                        # Schedule UI update on the main thread
                        Clock.schedule_once(
                            lambda dt: self._update_weather_display(weather_data, zip_code)
                        )
                    else:
                        Clock.schedule_once(
                            lambda dt: self._show_error(f"No weather data found for ZIP code {zip_code}")
                        )
                except Exception as e:
                    logger.error(f"Error fetching weather: {str(e)}")
                    Clock.schedule_once(
                        lambda dt: self._show_error(f"Failed to fetch weather: {str(e)}")
                    )
                finally:
                    if zip_code in self.weather_cards:
                        Clock.schedule_once(
                            lambda dt: self.weather_cards[zip_code].set_loading(False)
                        )
            except Exception as e:
                logger.error(f"Error in weather fetch worker: {str(e)}")
            finally:
                self._fetch_queue.task_done()
    
    def _fetch_weather(self, zip_code: str):
        """
        Queue a weather data fetch operation.
        
        Args:
            zip_code: The ZIP code to fetch weather for
        """
        with self._weather_lock:
            if zip_code in self.weather_cards:
                self.weather_cards[zip_code].set_loading(True)
        self._fetch_queue.put(zip_code)
    
    def on_stop(self):
        """Clean up resources when stopping."""
        try:
            # Signal worker thread to stop
            self._fetch_queue.put(None)
            self._fetch_thread.join(timeout=1.0)
            
            # Clean up other resources
            self.weather_client.cleanup()
            self.location_storage.save()
        except Exception as e:
            logger.error(f"Error during weather app cleanup: {e}")
    
    def _remove_location(self, zip_code: str):
        """
        Remove a location from display and storage.
        
        Args:
            zip_code: The ZIP code to remove
        """
        with self._weather_lock:
            if zip_code not in self.weather_cards:
                return
                
            try:
                # Remove from storage first
                self.location_storage.remove_location(zip_code)
                
                # Remove from UI
                card = self.weather_cards[zip_code]
                self.weather_cards_layout.remove_widget(card)
                del self.weather_cards[zip_code]
                
            except Exception as e:
                logger.error(f"Error removing location {zip_code}: {str(e)}")
                self._show_error(f"Failed to remove location: {str(e)}")
    
    def _update_weather_display(self, weather_data: WeatherData, zip_code: str):
        """
        Update the weather display with new weather data.
        
        Args:
            weather_data: The weather data to display
            zip_code: The ZIP code for the location
        """
        with self._weather_lock:
            try:
                if zip_code in self.weather_cards:
                    # Update existing card
                    card = self.weather_cards[zip_code]
                    card.update({
                        'location_name': weather_data.location_name,
                        'zip_code': zip_code,
                        'temperature': str(weather_data.temperature),
                        'description': weather_data.description,
                        'wind_speed': str(weather_data.wind_speed),
                        'humidity': str(weather_data.humidity),
                        'icon_url': weather_data.icon_url,
                        'last_update': datetime.now().strftime("Updated: %I:%M %p")
                    })
                    card.set_loading(False)
                else:
                    # Create new card
                    is_favorite = self.location_storage.is_favorite(zip_code)
                    card = WeatherCard(
                        location_name=weather_data.location_name,
                        zip_code=zip_code,
                        on_refresh=lambda: self._fetch_weather(zip_code),
                        on_remove=lambda: self._remove_location(zip_code),
                        on_favorite_toggle=lambda fav: self._on_favorite_toggle(zip_code, fav)
                    )
                    card.is_favorite = is_favorite
                    card.update({
                        'location_name': weather_data.location_name,
                        'zip_code': zip_code,
                        'temperature': str(weather_data.temperature),
                        'description': weather_data.description,
                        'wind_speed': str(weather_data.wind_speed),
                        'humidity': str(weather_data.humidity),
                        'icon_url': weather_data.icon_url,
                        'last_update': datetime.now().strftime("Updated: %I:%M %p")
                    })
                    self.weather_cards[zip_code] = card
                    
                    # Save new location
                    try:
                        self.location_storage.add_location(zip_code, weather_data.location_name)
                    except Exception as e:
                        logger.error(f"Failed to save location: {str(e)}")
                    
                    # Add card and reorder
                    self._reorder_weather_cards()
                    
            except Exception as e:
                self._show_error(f"Failed to update weather display: {str(e)}")
                if zip_code in self.weather_cards:
                    self.weather_cards[zip_code].set_loading(False)
    
    def _on_favorite_toggle(self, zip_code: str, is_favorite: bool):
        """
        Handle toggling favorite status for a location.
        
        Args:
            zip_code: The ZIP code of the location
            is_favorite: The new favorite status
        """
        try:
            self.location_storage.set_favorite(zip_code, is_favorite)
            
            # Reorder cards based on favorite status
            self._reorder_weather_cards()
            
        except Exception as e:
            self._show_error(f"Failed to update favorite status: {str(e)}")
    
    def _reorder_weather_cards(self):
        """
        Reorder weather cards to show favorites first.
        """
        # Remove all cards from layout
        self.weather_cards_layout.clear_widgets()
        
        # Sort cards: favorites first, then by name
        sorted_cards = sorted(
            self.weather_cards.items(),
            key=lambda x: (not self.location_storage.is_favorite(x[0]), x[1].location_name)
        )
        
        # Re-add cards in sorted order
        for zip_code, card in sorted_cards:
            self.weather_cards_layout.add_widget(card)
    
    def _show_error(self, message: str):
        """
        Show an error dialog with the given message.
        
        Args:
            message: The error message to display
        """
        dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def _setup_search_box(self):
        """Set up the search box for entering ZIP codes."""
        search_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8),
            padding=dp(8)
        )
        
        self.search_input = FocusTextInput(
            hint_text='Enter ZIP code',
            multiline=False,
            size_hint_x=0.8,
            on_text_validate=self._on_search
        )
        search_layout.add_widget(self.search_input)
        
        search_button = MDRaisedButton(
            text='Search',
            size_hint_x=0.2,
            on_release=lambda x: self._on_search(self.search_input)
        )
        search_layout.add_widget(search_button)
        
        self.add_widget(search_layout)
    
    def _setup_scroll_view(self):
        """Set up the scrollable view for weather cards."""
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint=(1, 1)
        )
        
        scroll.add_widget(self.weather_cards_layout)
        self.add_widget(scroll)
    
    def _on_search(self, instance):
        """
        Handle search input submission.
        
        Args:
            instance: The input field instance
        """
        zip_code = instance.text.strip()
        if not zip_code:
            self._show_error("Please enter a ZIP code")
            return
            
        if not self.location_storage._validate_zip_code(zip_code):
            self._show_error("Please enter a valid 5-digit ZIP code")
            return
            
        # Show loading indicator if card exists
        if zip_code in self.weather_cards:
            self.weather_cards[zip_code].set_loading(True)
            
        try:
            weather_data = self.weather_client.get_weather(zip_code)
            if weather_data:
                self._update_weather_display(weather_data, zip_code)
                self.search_input.text = ""  # Clear input on success
            else:
                self._show_error(f"No weather data found for ZIP code {zip_code}")
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            self._show_error(f"Failed to fetch weather: {str(e)}")
            if zip_code in self.weather_cards:
                self.weather_cards[zip_code].set_loading(False)
    
    def _load_saved_locations(self):
        """Load and display saved locations."""
        try:
            locations = self.location_storage.get_locations()
            for zip_code in locations:
                try:
                    weather_data = self.weather_client.get_weather(zip_code)
                    if weather_data:
                        self._update_weather_display(weather_data, zip_code)
                except Exception as e:
                    logger.error(f"Error loading weather for {zip_code}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading saved locations: {str(e)}")
            self._show_error("Failed to load saved locations")

class WeatherApp(MDApp):
    """
    Main application class for the Weather App.
    
    This class:
    1. Initializes the application
    2. Sets up the theme and styling
    3. Creates the main layout
    4. Handles application lifecycle
    """
    
    def build(self):
        """
        Build and return the application's root widget.
        
        This method:
        1. Sets up the application theme
        2. Creates the main layout
        3. Initializes UI components
        
        Returns:
            WeatherAppLayout: The root widget of the application
        """
        # Configure window
        if platform != 'android':
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
        # Request necessary Android permissions
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        
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
            # Unbind keyboard events
            Window.unbind(
                on_key_down=self._on_keyboard_down,
                on_keyboard=self._on_keyboard
            )
            
            # Clean up resources
            self.root.weather_client.cleanup()
            self.root.location_storage.save()
        except Exception as e:
            logger.error(f"Error during weather app cleanup: {e}")
    
    def _keyboard_closed(self):
        """
        Handle keyboard close event.
        
        Unbinds the keyboard event handler when the keyboard is closed.
        """
        try:
            Window.unbind(on_keyboard=self._on_keyboard)
        except Exception as e:
            logger.error(f"Error unbinding keyboard: {e}")
    
    def _on_keyboard(self, window, key, *args):
        """
        Handle keyboard events.
        
        Args:
            window: The window instance
            key: The key code
            *args: Additional arguments
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        try:
            if key == 27:  # ESC key
                return True  # Prevent app from closing
            elif key == 13:  # Enter key
                if hasattr(self.root, 'search_input') and self.root.search_input:
                    self.root.search_input.focus = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Error handling keyboard event: {e}")
            return False
    
    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        """
        Handle keyboard down events.
        
        Args:
            instance: The widget instance
            keyboard: The keyboard instance
            keycode: The key code
            text: The text input
            modifiers: List of active modifiers
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        try:
            if keycode == 40:  # Enter key
                if hasattr(self.root, 'search_input') and self.root.search_input:
                    self.root.search_input.focus = True
                    if self.root.search_input.text.strip():
                        self.root._on_search(self.root.search_input)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error handling keyboard down event: {e}")
            return False 