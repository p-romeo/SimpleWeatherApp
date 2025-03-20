"""
Unit tests for the WeatherStackClient class.
"""

import pytest
from unittest.mock import patch, MagicMock
from weather_app.api.weather_client import WeatherStackClient, WeatherData

@pytest.fixture
def weather_client():
    """Create a WeatherStackClient instance for testing."""
    return WeatherStackClient("test_api_key")

@pytest.fixture
def mock_response():
    """Create a mock API response."""
    return {
        "location": {
            "name": "Test City",
            "region": "Test Region",
            "country": "Test Country",
        },
        "current": {
            "temperature": 72.5,
            "weather_descriptions": ["Sunny"],
            "wind_speed": 5.0,
            "humidity": 65,
            "weather_icons": ["http://example.com/icon.png"]
        }
    }

def test_validate_api_key():
    """Test API key validation."""
    # Test valid key
    client = WeatherStackClient("a" * 32)
    assert client._validate_api_key() is True
    
    # Test invalid keys
    with pytest.raises(ValueError):
        WeatherStackClient("")
    
    with pytest.raises(ValueError):
        WeatherStackClient("short_key")

def test_get_weather_success(weather_client, mock_response):
    """Test successful weather data retrieval."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        weather_data = weather_client.get_weather("12345")
        
        assert isinstance(weather_data, WeatherData)
        assert weather_data.location_name == "Test City"
        assert weather_data.temperature == 72.5
        assert weather_data.description == "Sunny"
        assert weather_data.wind_speed == 5.0
        assert weather_data.humidity == 65
        assert weather_data.icon_url == "http://example.com/icon.png"

def test_get_weather_invalid_zip(weather_client):
    """Test weather retrieval with invalid ZIP code."""
    with pytest.raises(ValueError):
        weather_client.get_weather("invalid")
    
    with pytest.raises(ValueError):
        weather_client.get_weather("1234")  # Too short
    
    with pytest.raises(ValueError):
        weather_client.get_weather("123456")  # Too long

def test_get_weather_api_error(weather_client):
    """Test handling of API errors."""
    with patch('requests.get') as mock_get:
        # Test connection error
        mock_get.side_effect = ConnectionError()
        with pytest.raises(ConnectionError):
            weather_client.get_weather("12345")
        
        # Test API error response
        mock_get.side_effect = None
        mock_get.return_value.json.return_value = {"error": {"code": 101, "info": "API Error"}}
        mock_get.return_value.status_code = 400
        
        with pytest.raises(ValueError) as exc_info:
            weather_client.get_weather("12345")
        assert "API Error" in str(exc_info.value)

def test_get_weather_invalid_response(weather_client):
    """Test handling of invalid API responses."""
    with patch('requests.get') as mock_get:
        # Missing required fields
        mock_get.return_value.json.return_value = {"location": {}, "current": {}}
        mock_get.return_value.status_code = 200
        
        with pytest.raises(ValueError) as exc_info:
            weather_client.get_weather("12345")
        assert "Invalid response format" in str(exc_info.value)
        
        # Invalid JSON
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        
        with pytest.raises(ValueError) as exc_info:
            weather_client.get_weather("12345")
        assert "Invalid JSON response" in str(exc_info.value)

def test_cleanup(weather_client):
    """Test client cleanup."""
    # Mock session
    weather_client._session = MagicMock()
    
    weather_client.cleanup()
    
    weather_client._session.close.assert_called_once() 