"""
UI tests for the Weather App.
"""

import pytest
from unittest.mock import patch, MagicMock
from kivy.clock import Clock
from kivy.metrics import dp

def test_app_initialization(app):
    """Test app initialization and theme setup."""
    # Build the app
    root = app.build()
    
    # Check theme configuration
    assert app.theme_cls.primary_palette == "Blue"
    assert app.theme_cls.theme_style == "Light"
    assert app.theme_cls.theme_style_switch_animation is True
    
    # Check root widget
    assert root is not None
    assert root.orientation == 'vertical'
    assert root.padding == dp(10)
    assert root.spacing == dp(10)

def test_weather_app_layout(weather_app_layout, mock_weather_client, mock_location_storage, kivy_clock):
    """Test WeatherAppLayout functionality."""
    # Check initial setup
    assert weather_app_layout.weather_client == mock_weather_client
    assert weather_app_layout.location_storage == mock_location_storage
    assert len(weather_app_layout.weather_cards) == 1  # From mock data
    
    # Test search functionality
    weather_app_layout.search_input.text = "12345"
    weather_app_layout._on_search(weather_app_layout.search_input)
    kivy_clock()
    
    # Verify weather client was called
    mock_weather_client.get_weather.assert_called_with("12345")
    
    # Check weather card was updated
    assert "12345" in weather_app_layout.weather_cards
    card = weather_app_layout.weather_cards["12345"]
    assert card.location_name == "Test City"

def test_favorite_functionality(weather_app_layout, mock_location_storage, kivy_clock):
    """Test favorite location functionality."""
    # Add a test location
    weather_app_layout._update_weather_display(
        weather_data=MagicMock(
            location_name="Test City",
            zip_code="12345",
            temperature=72.5,
            description="Sunny",
            wind_speed=5.0,
            humidity=65,
            icon_url="http://example.com/icon.png"
        ),
        zip_code="12345"
    )
    kivy_clock()
    
    # Toggle favorite
    weather_app_layout._on_favorite_toggle("12345", True)
    kivy_clock()
    
    # Verify storage was updated
    mock_location_storage.set_favorite.assert_called_with("12345", True)

def test_remove_location(weather_app_layout, mock_location_storage, kivy_clock):
    """Test location removal."""
    # Add a test location
    weather_app_layout._update_weather_display(
        weather_data=MagicMock(
            location_name="Test City",
            zip_code="12345",
            temperature=72.5,
            description="Sunny",
            wind_speed=5.0,
            humidity=65,
            icon_url="http://example.com/icon.png"
        ),
        zip_code="12345"
    )
    kivy_clock()
    
    # Remove location
    weather_app_layout._remove_location("12345")
    kivy_clock()
    
    # Verify storage was updated
    mock_location_storage.remove_location.assert_called_with("12345")
    assert "12345" not in weather_app_layout.weather_cards

def test_error_handling(weather_app_layout, mock_weather_client, kivy_clock):
    """Test error handling in UI."""
    # Test invalid ZIP code
    weather_app_layout.search_input.text = "invalid"
    weather_app_layout._on_search(weather_app_layout.search_input)
    kivy_clock()
    
    # Verify error was shown
    assert mock_weather_client.get_weather.call_count == 0
    
    # Test API error
    mock_weather_client.get_weather.side_effect = ConnectionError("API Error")
    weather_app_layout.search_input.text = "12345"
    weather_app_layout._on_search(weather_app_layout.search_input)
    kivy_clock()
    
    # Verify error handling
    assert "12345" not in weather_app_layout.weather_cards

def test_keyboard_handling(app, kivy_clock):
    """Test keyboard event handling."""
    root = app.build()
    
    # Test ESC key
    assert app._on_keyboard(None, 27, None) is True
    
    # Test Enter key
    assert app._on_keyboard(None, 13, None) is True
    
    # Test other keys
    assert app._on_keyboard(None, 65, None) is False  # 'A' key

def test_cleanup(weather_app_layout, mock_weather_client, mock_location_storage):
    """Test cleanup on app stop."""
    weather_app_layout.on_stop()
    
    # Verify resources were cleaned up
    mock_weather_client.cleanup.assert_called_once()
    mock_location_storage.save.assert_called_once() 