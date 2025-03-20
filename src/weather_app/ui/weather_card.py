"""Weather card widget for displaying weather information"""

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.image import AsyncImage
from kivymd.uix.spinner import MDSpinner

class WeatherCard(MDCard):
    """
    Material Design card component for displaying weather information.
    
    This card displays:
    1. Location name and ZIP code
    2. Current temperature
    3. Weather description
    4. Wind speed
    5. Humidity level
    6. Last update time
    7. Weather icon
    8. Loading indicator
    
    The card updates automatically when new weather data is received
    and provides interactive elements for refreshing data or removing
    the location.
    """
    
    location_name = StringProperty("")
    zip_code = StringProperty("")
    temperature = StringProperty("0")
    description = StringProperty("")
    wind_speed = StringProperty("0")
    humidity = StringProperty("0")
    icon_url = StringProperty("")
    last_update = StringProperty("")
    is_loading = False
    is_favorite = False
    
    def __init__(self, on_refresh=None, on_remove=None, on_favorite=None, **kwargs):
        """
        Initialize the weather card component.
        
        Sets up:
        1. Card layout and styling
        2. Weather data properties
        3. Interactive elements
        4. Update handlers
        
        Args:
            on_refresh: Callback function for refreshing weather data
            on_remove: Callback function for removing the location
            on_favorite: Callback function for toggling favorite status
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "8dp"
        self.spacing = "8dp"
        self.size_hint_y = None
        self.height = "250dp"
        self.elevation = 2
        
        self.on_refresh = on_refresh
        self.on_remove = on_remove
        self.on_favorite = on_favorite
        
        # Create UI elements
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=0.2,
            spacing="8dp"
        )
        
        location_info = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.7
        )
        
        self.location_label = MDLabel(
            text=self.location_name,
            font_style="H6",
            theme_text_color="Primary"
        )
        self.zip_label = MDLabel(
            text=f"ZIP: {self.zip_code}",
            theme_text_color="Secondary"
        )
        location_info.add_widget(self.location_label)
        location_info.add_widget(self.zip_label)
        
        button_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=0.3,
            spacing="4dp"
        )
        
        self.favorite_button = MDIconButton(
            icon="star-outline",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color,
            on_release=self._on_favorite_press
        )
        refresh_button = MDIconButton(
            icon="refresh",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color,
            on_release=self._on_refresh_press
        )
        remove_button = MDIconButton(
            icon="close",
            theme_text_color="Custom",
            text_color=self.theme_cls.error_color,
            on_release=self._on_remove_press
        )
        button_layout.add_widget(self.favorite_button)
        button_layout.add_widget(refresh_button)
        button_layout.add_widget(remove_button)
        
        header_layout.add_widget(location_info)
        header_layout.add_widget(button_layout)
        self.add_widget(header_layout)
        
        # Weather info layout with loading indicator
        self.weather_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=0.5,
            padding=("8dp", "8dp")
        )
        
        # Loading indicator
        self.loading_layout = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=("16dp", "16dp")
        )
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={'center_x': .5, 'center_y': .5}
        )
        self.loading_layout.add_widget(self.spinner)
        
        # Left side - Temperature and description
        temp_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.6
        )
        self.temp_label = MDLabel(
            text=f"{self.temperature}°F",
            font_style="H4",
            theme_text_color="Primary",
            halign="center"
        )
        self.desc_label = MDLabel(
            text=self.description,
            theme_text_color="Secondary",
            halign="center"
        )
        temp_layout.add_widget(self.temp_label)
        temp_layout.add_widget(self.desc_label)
        
        # Right side - Weather icon
        self.icon_image = AsyncImage(
            source=self.icon_url,
            size_hint_x=0.4,
            allow_stretch=True,
            keep_ratio=True
        )
        
        self.weather_layout.add_widget(temp_layout)
        self.weather_layout.add_widget(self.icon_image)
        self.add_widget(self.weather_layout)
        
        # Details layout
        details_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_y=0.3,
            spacing="4dp"
        )
        
        self.wind_label = MDLabel(
            text=f"Wind: {self.wind_speed} mph",
            theme_text_color="Secondary",
            font_style="Body2"
        )
        self.humidity_label = MDLabel(
            text=f"Humidity: {self.humidity}%",
            theme_text_color="Secondary",
            font_style="Body2"
        )
        self.update_label = MDLabel(
            text=self.last_update,
            theme_text_color="Hint",
            font_style="Caption"
        )
        
        details_layout.add_widget(self.wind_label)
        details_layout.add_widget(self.humidity_label)
        details_layout.add_widget(self.update_label)
        self.add_widget(details_layout)
        
        # Bind properties
        self.bind(
            location_name=self._on_location_name,
            zip_code=self._on_zip_code,
            temperature=self._on_temperature,
            description=self._on_description,
            wind_speed=self._on_wind_speed,
            humidity=self._on_humidity,
            icon_url=self._on_icon_url,
            last_update=self._on_last_update
        )
    
    def set_loading(self, loading: bool):
        """
        Show or hide the loading indicator.
        
        Args:
            loading: True to show loading indicator, False to hide
        """
        if loading != self.is_loading:
            self.is_loading = loading
            if loading:
                self.weather_layout.clear_widgets()
                self.weather_layout.add_widget(self.loading_layout)
                self.spinner.active = True
            else:
                self.spinner.active = False
                self.weather_layout.clear_widgets()
                temp_layout = MDBoxLayout(
                    orientation="vertical",
                    size_hint_x=0.6
                )
                temp_layout.add_widget(self.temp_label)
                temp_layout.add_widget(self.desc_label)
                self.weather_layout.add_widget(temp_layout)
                self.weather_layout.add_widget(self.icon_image)
    
    def set_favorite(self, is_favorite: bool):
        """
        Set the favorite status of the location.
        
        Args:
            is_favorite: True if location is favorite, False otherwise
        """
        self.is_favorite = is_favorite
        self.favorite_button.icon = "star" if is_favorite else "star-outline"
    
    def _on_location_name(self, instance, value):
        """Update the location name label."""
        self.location_label.text = value
    
    def _on_zip_code(self, instance, value):
        """Update the ZIP code label."""
        self.zip_label.text = f"ZIP: {value}"
    
    def _on_temperature(self, instance, value):
        """Update the temperature label."""
        self.temp_label.text = f"{value}°F"
    
    def _on_description(self, instance, value):
        """Update the weather description label."""
        self.desc_label.text = value
    
    def _on_wind_speed(self, instance, value):
        """Update the wind speed label."""
        self.wind_label.text = f"Wind: {value} mph"
    
    def _on_humidity(self, instance, value):
        """Update the humidity label."""
        self.humidity_label.text = f"Humidity: {value}%"
    
    def _on_icon_url(self, instance, value):
        """Update the weather icon."""
        self.icon_image.source = value
    
    def _on_last_update(self, instance, value):
        """Update the last update time label."""
        self.update_label.text = value
    
    def _on_refresh_press(self, instance):
        """Handle refresh button press."""
        if self.on_refresh:
            self.on_refresh(self.zip_code)
    
    def _on_remove_press(self, instance):
        """Handle remove button press."""
        if self.on_remove:
            self.on_remove(self.zip_code)
    
    def _on_favorite_press(self, instance):
        """Handle favorite button press."""
        if self.on_favorite:
            self.on_favorite(self.zip_code)
    
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
        self.icon_url = weather_data.get('icon_url', '')
        self.last_update = weather_data.get('last_update', '')