"""Weather card widget for displaying weather information"""

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

class WeatherCard(MDCard):
    """
    A card widget for displaying weather information
    
    This widget displays:
    1. Location name and ZIP code
    2. Temperature in Celsius
    3. Weather description
    4. Wind speed in km/h
    5. Humidity percentage
    """
    
    location_name = StringProperty("")
    zip_code = StringProperty("")
    temperature = StringProperty("0")
    description = StringProperty("")
    wind_speed = StringProperty("0")
    humidity = StringProperty("0")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "8dp"
        self.spacing = "8dp"
        self.size_hint_y = None
        self.height = "200dp"
        self.elevation = 2
        
        # Create UI elements
        self.location_label = MDLabel(
            text=self.location_name,
            font_style="H6",
            theme_text_color="Primary"
        )
        self.zip_label = MDLabel(
            text=f"ZIP: {self.zip_code}",
            theme_text_color="Secondary"
        )
        self.temp_label = MDLabel(
            text=f"{self.temperature}°C",
            font_style="H5",
            theme_text_color="Primary"
        )
        self.desc_label = MDLabel(
            text=self.description,
            theme_text_color="Secondary"
        )
        self.wind_label = MDLabel(
            text=f"Wind: {self.wind_speed} km/h",
            theme_text_color="Secondary"
        )
        self.humidity_label = MDLabel(
            text=f"Humidity: {self.humidity}%",
            theme_text_color="Secondary"
        )
        
        # Set up layout
        location_layout = BoxLayout(orientation="vertical", size_hint_y=0.4)
        location_layout.add_widget(self.location_label)
        location_layout.add_widget(self.zip_label)
        self.add_widget(location_layout)
        
        weather_layout = BoxLayout(orientation="vertical", size_hint_y=0.6)
        weather_layout.add_widget(self.temp_label)
        weather_layout.add_widget(self.desc_label)
        weather_layout.add_widget(self.wind_label)
        weather_layout.add_widget(self.humidity_label)
        self.add_widget(weather_layout)
        
        # Bind properties
        self.bind(
            location_name=self._on_location_name,
            zip_code=self._on_zip_code,
            temperature=self._on_temperature,
            description=self._on_description,
            wind_speed=self._on_wind_speed,
            humidity=self._on_humidity
        )
    
    def _on_location_name(self, instance, value):
        self.location_label.text = value
    
    def _on_zip_code(self, instance, value):
        self.zip_label.text = f"ZIP: {value}"
    
    def _on_temperature(self, instance, value):
        self.temp_label.text = f"{value}°C"
    
    def _on_description(self, instance, value):
        self.desc_label.text = value
    
    def _on_wind_speed(self, instance, value):
        self.wind_label.text = f"Wind: {value} km/h"
    
    def _on_humidity(self, instance, value):
        self.humidity_label.text = f"Humidity: {value}%"
    
    def update(self, weather_data):
        """
        Update the card with new weather data
        
        Args:
            weather_data: Dictionary containing weather information
        """
        self.location_name = weather_data.get('location_name', '')
        self.zip_code = weather_data.get('zip_code', '')
        self.temperature = weather_data.get('temperature', '0')
        self.description = weather_data.get('description', '')
        self.wind_speed = weather_data.get('wind_speed', '0')
        self.humidity = weather_data.get('humidity', '0') 