"""
Weather App UI implementation using Kivy
"""

import logging
from typing import Optional, Dict, Any
from threading import Thread
from queue import Queue

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

from src.weather_app.api.weather_client import WeatherStackClient
from src.weather_app.storage.location_storage import LocationStorage

logger = logging.getLogger(__name__)

class WeatherAppLayout(BoxLayout):
    """Main layout for the Weather App"""
    
    def __init__(self, api_client: WeatherStackClient, **kwargs):
        """Initialize the Weather App layout"""
        super().__init__(**kwargs)
        
        self.api_client = api_client
        self.location_storage = LocationStorage()
        
        # Configure layout
        self.orientation = 'vertical'
        self.padding = [40, 40]
        self.spacing = 30
        
        # Initialize thread-safe queue for weather data
        self._weather_queue = Queue()
        self._current_weather_thread = None
        
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
        """Fetch weather data in a separate thread"""
        try:
            data = self.api_client.get_weather(zip_code)
            self._weather_queue.put(('success', data))
        except Exception as e:
            self._weather_queue.put(('error', str(e)))

    def get_weather(self, instance):
        """Get weather data for the specified ZIP code"""
        logger.debug("\n=== Starting weather request ===")
        
        # Disable UI elements and show loading indicator
        self.save_button.disabled = True
        self.get_weather_button.disabled = True
        self.loading_spinner.opacity = 1
        
        # Clear previous weather display
        self.weather_display.text = ''
        self.weather_image.source = ''
        
        # Cancel any existing weather request thread
        if self._current_weather_thread and self._current_weather_thread.is_alive():
            logger.debug("Canceling previous weather request")
            # We can't actually cancel the thread, but we can ignore its results
            self._weather_queue.queue.clear()
        
        # Start new weather request in a separate thread
        self._current_weather_thread = Thread(
            target=self._fetch_weather_async,
            args=(self.zip_code.text,),
            daemon=True
        )
        self._current_weather_thread.start()

    def _check_weather_queue(self, dt):
        """Check for completed weather requests"""
        try:
            while not self._weather_queue.empty():
                status, data = self._weather_queue.get_nowait()
                
                # Hide loading indicator
                self.loading_spinner.opacity = 0
                self.get_weather_button.disabled = False
                
                if status == 'success':
                    self._update_weather_display(data)
                else:  # error
                    self.weather_display.text = f"[color=ff3333]{data}[/color]"
                    self.weather_image.source = ''
                    self.save_button.disabled = True
                
        except Exception as e:
            logger.error(f"Error processing weather data: {e}", exc_info=True)

    def _update_weather_display(self, data: Dict[str, Any]):
        """Update the weather display with new data"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error updating weather display: {e}", exc_info=True)
            self.weather_display.text = "[color=ff3333]Error displaying weather data[/color]"
            self.weather_image.source = ''
            self.save_button.disabled = True

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


class WeatherApp(App):
    """Main Weather Application"""
    
    def __init__(self, api_client: WeatherStackClient, **kwargs):
        super().__init__(**kwargs)
        self.api_client = api_client

    def build(self):
        """Build and return the root widget"""
        # Configure window
        Window.size = (800, 900)
        Window.minimum_width = 400
        Window.minimum_height = 600
        Window.clearcolor = get_color_from_hex('#f0f0f0')
        
        # Ensure proper window density
        Window._density = 1.0 if not Window._density else Window._density
        
        return WeatherAppLayout(api_client=self.api_client) 