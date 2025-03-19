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
from kivy.graphics import Color, Rectangle

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

class WeatherAppLayout(BoxLayout):
    """Main layout for the Weather App"""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage, **kwargs):
        """
        Initialize the Weather App layout
        
        Args:
            api_client: The WeatherStack API client
            location_storage: The location storage manager
        """
        super().__init__(**kwargs)
        
        self.api_client = api_client
        self.location_storage = location_storage
        
        # Configure layout
        self.orientation = 'vertical'
        self.padding = [40, 40]
        self.spacing = 30
        
        # Initialize thread-safe components
        self._weather_queue = Queue()
        self._current_weather_thread = None
        self._thread_lock = Lock()
        self._current_zip_code = None
        
        # Create UI components
        self._create_ui_components()
        self._update_saved_locations()
        
        # Schedule periodic UI updates
        Clock.schedule_interval(self._check_weather_queue, 0.1)
        logger.debug("UI components initialized")

    def _create_ui_components(self):
        """Create and initialize all UI components"""
        self._create_title_section()
        self._create_input_section()
        self._create_save_button()
        self._create_weather_section()
        self._create_saved_locations_section()
        self._create_error_popup()

    def _create_title_section(self):
        """Create the title section"""
        title_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=80,
            padding=[0, 10]
        )
        title_layout.add_widget(Label(
            text="Weather Forecast",
            font_size='32sp',
            size_hint_y=None,
            height=60,
            color=get_color_from_hex('#2196F3')
        ))
        self.add_widget(title_layout)

    def _create_input_section(self):
        """Create the input section"""
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=20
        )
        
        self.zip_code = TextInput(
            multiline=False,
            hint_text='Enter ZIP code',
            padding=[20, 15, 0, 15],
            size_hint_x=0.7,
            font_size='18sp',
            background_color=get_color_from_hex('#ffffff'),
            foreground_color=get_color_from_hex('#000000')
        )
        self.zip_code.bind(on_text_validate=self.get_weather)
        
        self.get_weather_button = Button(
            text='Get Weather',
            size_hint_x=0.3,
            font_size='18sp',
            background_color=get_color_from_hex('#2196F3'),
            background_normal=''
        )
        self.get_weather_button.bind(on_press=self.get_weather)
        
        input_layout.add_widget(self.zip_code)
        input_layout.add_widget(self.get_weather_button)
        self.add_widget(input_layout)

    def _create_save_button(self):
        """Create the save location button"""
        self.save_button = Button(
            text='Save Location',
            size_hint_y=None,
            height=50,
            font_size='18sp',
            background_color=get_color_from_hex('#4CAF50'),
            background_normal='',
            disabled=True
        )
        self.save_button.bind(on_press=self.save_current_location)
        self.add_widget(self.save_button)

    def _create_weather_section(self):
        """Create the weather display section"""
        weather_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=400,
            spacing=20
        )

        # Create loading spinner
        self.loading_spinner = Spinner(
            text='Loading weather data...',
            values=('Loading weather data...',),
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5},
            background_color=get_color_from_hex('#2196F3'),
            background_normal='',
        )
        self.loading_spinner.opacity = 0
        weather_section.add_widget(self.loading_spinner)

        # Create progress bar container
        progress_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(200, 4),
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
        weather_section.add_widget(progress_container)

        self.weather_image = AsyncImage(
            size_hint=(None, None),
            size=(200, 200),
            pos_hint={'center_x': 0.5}
        )
        weather_section.add_widget(self.weather_image)

        self.weather_display = Label(
            text='',
            markup=True,
            font_size='24sp',
            halign='center',
            valign='middle',
            color=get_color_from_hex('#333333'),
            size_hint_y=None,
            height=200
        )
        self.weather_display.bind(size=self.weather_display.setter('text_size'))
        weather_section.add_widget(self.weather_display)
        
        self.add_widget(weather_section)

    def _create_saved_locations_section(self):
        """Create the saved locations section"""
        locations_section = BoxLayout(
            orientation='vertical',
            size_hint_y=1,
            spacing=10
        )

        saved_locations_label = Label(
            text="Saved Locations",
            font_size='24sp',
            size_hint_y=None,
            height=40,
            color=get_color_from_hex('#2196F3')
        )
        locations_section.add_widget(saved_locations_label)

        scroll_view = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        self.saved_locations_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10
        )
        self.saved_locations_container.bind(
            minimum_height=self.saved_locations_container.setter('height')
        )
        
        scroll_view.add_widget(self.saved_locations_container)
        locations_section.add_widget(scroll_view)
        self.add_widget(locations_section)

    def _create_error_popup(self):
        """Create the error popup"""
        self.error_popup = None

    def _show_error(self, title: str, message: str) -> None:
        """
        Show an error popup
        
        Args:
            title: The popup title
            message: The error message
        """
        if self.error_popup:
            self.error_popup.dismiss()
        self.error_popup = ErrorPopup(title=title, message=message)
        self.error_popup.open()

    def _update_saved_locations(self):
        """Update the saved locations display"""
        self.saved_locations_container.clear_widgets()
        
        for zip_code, location_name in self.location_storage.get_locations().items():
            entry_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=60,
                spacing=10
            )
            
            location_button = Button(
                text=f"{location_name} ({zip_code})",
                size_hint_x=1,
                height=60,
                font_size='18sp',
                background_color=get_color_from_hex('#E3F2FD'),
                background_normal='',
                color=get_color_from_hex('#333333')
            )
            location_button.bind(on_press=lambda btn, zip=zip_code: self.load_saved_location(zip))
            
            entry_layout.add_widget(location_button)
            
            delete_button = Button(
                text='×',
                size_hint_x=None,
                width=60,
                font_size='24sp',
                background_color=get_color_from_hex('#FF5252'),
                background_normal=''
            )
            delete_button.bind(on_press=lambda btn, zip=zip_code: self.delete_location(zip))
            entry_layout.add_widget(delete_button)
            
            self.saved_locations_container.add_widget(entry_layout)

    def _fetch_weather_async(self, zip_code: str) -> None:
        """
        Fetch weather data in a separate thread
        
        Args:
            zip_code: The ZIP code to fetch weather for
        """
        try:
            with self._thread_lock:
                if self._current_weather_thread and self._current_weather_thread.is_alive():
                    logger.warning("Weather fetch already in progress")
                    return
                    
                self._current_weather_thread = Thread(
                    target=self._weather_worker,
                    args=(zip_code,),
                    daemon=True
                )
                self._current_weather_thread.start()
                
        except Exception as e:
            logger.error(f"Error starting weather fetch thread: {str(e)}")
            self._weather_queue.put(('error', str(e)))

    def _weather_worker(self, zip_code: str) -> None:
        """
        Worker thread for fetching weather data
        
        Args:
            zip_code: The ZIP code to fetch weather for
        """
        try:
            # Update progress bar
            for i in range(0, 101, 10):
                self._weather_queue.put(('progress', i))
                time.sleep(0.1)
            
            # Fetch weather data
            data = self.api_client.get_weather(zip_code)
            self._weather_queue.put(('success', data))
            
        except Exception as e:
            logger.error(f"Error in weather worker: {str(e)}")
            self._weather_queue.put(('error', str(e)))
        finally:
            # Reset progress bar
            self._weather_queue.put(('progress', 0))

    def _check_weather_queue(self, dt: float) -> None:
        """
        Check the weather queue for updates
        
        Args:
            dt: Delta time from Clock
        """
        try:
            while not self._weather_queue.empty():
                msg_type, data = self._weather_queue.get_nowait()
                
                if msg_type == 'success':
                    self._update_weather_display(data)
                elif msg_type == 'error':
                    self._show_error('Error', str(data))
                elif msg_type == 'progress':
                    self._update_progress_bar(data)
                    
        except Exception as e:
            logger.error(f"Error processing weather queue: {str(e)}")

    def _update_weather_display(self, weather_data: WeatherData) -> None:
        """
        Update the weather display with new data
        
        Args:
            weather_data: The weather data to display
        """
        try:
            # Update weather image
            self.weather_image.source = weather_data.icon_url
            
            # Update weather text
            self.weather_display.text = (
                f"[b]{weather_data.location}[/b]\n"
                f"Temperature: {weather_data.temperature}°F\n"
                f"Conditions: {weather_data.description}\n"
                f"Humidity: {weather_data.humidity}%\n"
                f"Wind Speed: {weather_data.wind_speed} mph\n"
                f"Last Updated: {weather_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Enable save button
            self.save_button.disabled = False
            self._current_zip_code = weather_data.location
            
            # Hide loading indicators
            self._hide_loading_indicators()
            
        except Exception as e:
            logger.error(f"Error updating weather display: {str(e)}")
            self._show_error('Error', 'Failed to update weather display')

    def _update_progress_bar(self, value: int) -> None:
        """
        Update the progress bar value
        
        Args:
            value: The progress value (0-100)
        """
        if value == 0:
            self.progress_bar.opacity = 0
        else:
            self.progress_bar.opacity = 1
            self.progress_bar.value = value

    def _show_loading_indicators(self) -> None:
        """Show loading indicators"""
        self.loading_spinner.opacity = 1
        self.progress_bar.opacity = 1
        self.progress_bar.value = 0

    def _hide_loading_indicators(self) -> None:
        """Hide loading indicators"""
        self.loading_spinner.opacity = 0
        self.progress_bar.opacity = 0

    def get_weather(self, instance: Any) -> None:
        """
        Get weather for the entered ZIP code
        
        Args:
            instance: The widget that triggered this method
        """
        zip_code = self.zip_code.text.strip()
        
        if not zip_code:
            self._show_error('Error', 'Please enter a ZIP code')
            return
            
        self._show_loading_indicators()
        self._fetch_weather_async(zip_code)

    def save_current_location(self, instance: Any) -> None:
        """
        Save the current location
        
        Args:
            instance: The widget that triggered this method
        """
        if not self._current_zip_code:
            self._show_error('Error', 'No location to save')
            return
            
        try:
            self.location_storage.add_location(
                self.zip_code.text.strip(),
                self._current_zip_code
            )
            self._update_saved_locations()
            self._show_error('Success', 'Location saved successfully')
        except Exception as e:
            logger.error(f"Error saving location: {str(e)}")
            self._show_error('Error', 'Failed to save location')

    def load_saved_location(self, zip_code: str) -> None:
        """
        Load a saved location
        
        Args:
            zip_code: The ZIP code to load
        """
        self.zip_code.text = zip_code
        self.get_weather(None)

    def delete_location(self, zip_code: str) -> None:
        """
        Delete a saved location
        
        Args:
            zip_code: The ZIP code to delete
        """
        try:
            self.location_storage.remove_location(zip_code)
            self._update_saved_locations()
            self._show_error('Success', 'Location deleted successfully')
        except Exception as e:
            logger.error(f"Error deleting location: {str(e)}")
            self._show_error('Error', 'Failed to delete location')

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Cancel any ongoing weather fetch
            with self._thread_lock:
                if self._current_weather_thread and self._current_weather_thread.is_alive():
                    self._current_weather_thread.join(timeout=1.0)
            
            # Clear weather queue
            while not self._weather_queue.empty():
                try:
                    self._weather_queue.get_nowait()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class WeatherApp(App):
    """Main application class"""
    
    def __init__(self, api_client: WeatherStackClient, location_storage: LocationStorage):
        """
        Initialize the Weather App
        
        Args:
            api_client: The WeatherStack API client
            location_storage: The location storage manager
        """
        super().__init__()
        self.api_client = api_client
        self.location_storage = location_storage
        
    def build(self) -> WeatherAppLayout:
        """
        Build the application UI
        
        Returns:
            WeatherAppLayout: The main application layout
        """
        return WeatherAppLayout(
            api_client=self.api_client,
            location_storage=self.location_storage
        )
        
    def cleanup(self) -> None:
        """Handle application shutdown"""
        try:
            if hasattr(self.root, 'cleanup'):
                self.root.cleanup()
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            
    def on_stop(self) -> None:
        """Handle application shutdown"""
        self.cleanup() 