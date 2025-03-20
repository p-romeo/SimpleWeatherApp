"""
Test configuration and fixtures for the Weather App tests.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from kivy.clock import Clock
from kivy.base import EventLoop
from kivy.core.window import Window

from weather_app.api.weather_client import WeatherData
from weather_app.ui.weather_app import WeatherAppLayout, WeatherApp

@pytest.fixture
def mock_weather_data():
    """Create mock weather data for testing."""
    return WeatherData(
        location_name="Test City",
        zip_code="12345",
        temperature=72.5,
        description="Sunny",
        wind_speed=5.0,
        humidity=65,
        icon_url="http://example.com/icon.png"
    )

@pytest.fixture
def mock_weather_client():
    """Create a mock weather client."""
    client = MagicMock()
    client.get_weather.return_value = mock_weather_data()
    return client

@pytest.fixture
def mock_location_storage():
    """Create a mock location storage."""
    storage = MagicMock()
    storage.get_locations.return_value = ["12345"]
    storage.is_favorite.return_value = False
    storage._validate_zip_code.return_value = True
    return storage

@pytest.fixture
def app():
    """Create a test instance of the Weather App."""
    app = WeatherApp()
    return app

@pytest.fixture
def weather_app_layout(mock_weather_client, mock_location_storage):
    """Create a test instance of the WeatherAppLayout."""
    with patch('weather_app.ui.weather_app.WeatherStackClient', return_value=mock_weather_client), \
         patch('weather_app.ui.weather_app.LocationStorage', return_value=mock_location_storage):
        layout = WeatherAppLayout()
        return layout

@pytest.fixture
def kivy_clock():
    """Process Kivy clock events for testing."""
    Clock.max_iteration = 0
    
    def process_events():
        for i in range(2):
            EventLoop.idle()
            Clock.tick()
    
    return process_events

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment variables."""
    os.environ['WEATHERSTACK_API_KEY'] = 'test_api_key'
    yield
    if 'WEATHERSTACK_API_KEY' in os.environ:
        del os.environ['WEATHERSTACK_API_KEY'] 