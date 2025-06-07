"""
WeatherStack API client implementation

This module provides a client for interacting with the WeatherStack API.
It includes features like:
- Rate limiting
- Response caching
- Error handling
- Input validation
"""

import logging
import requests
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

@dataclass
class WeatherData:
    """
    Data class for weather information.
    
    Attributes:
        temperature: Current temperature in Fahrenheit
        location_name: Location name
        description: Weather description
        humidity: Humidity percentage
        wind_speed: Wind speed in mph
        icon_url: URL to the weather icon
        timestamp: Time when the data was fetched
        zip_code: ZIP code for the location
    """
    temperature: float
    location_name: str
    description: str
    humidity: int
    wind_speed: float
    icon_url: str
    timestamp: datetime
    zip_code: str

class WeatherStackClient:
    """
    Client for interacting with the WeatherStack API.
    
    This client handles:
    1. API authentication
    2. Rate limiting
    3. Response caching
    4. Error handling
    5. Data validation
    """
    
    def __init__(self, api_key: str, base_url: str = 'http://api.weatherstack.com/current',
                 cache_timeout: int = 300, request_timeout: int = 10):
        """
        Initialize the WeatherStack API client
        
        Args:
            api_key: The API key for WeatherStack
            base_url: The base URL for the API
            cache_timeout: How long to cache results in seconds (default 5 minutes)
            request_timeout: How long to wait for API response in seconds (default 10 seconds)
            
        Raises:
            ValueError: If the API key is invalid
        """
        self.api_key = api_key.strip()
        if not self._validate_api_key():
            raise ValueError("Invalid API key format")
            
        self.base_url = base_url
        self.cache_timeout = cache_timeout
        self.request_timeout = request_timeout
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum time between requests in seconds
        
        # Initialize cache
        self._weather_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        self.session = requests.Session()
        
    def cleanup(self) -> None:
        """Clean up resources when shutting down"""
        try:
            self.session.close()
            self._weather_cache.clear()
            self._cache_timestamps.clear()
            logger.info("WeatherStack client cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during WeatherStack client cleanup: {str(e)}")
        
    def get_weather(self, zip_code: str) -> WeatherData:
        """
        Get weather data for a specific ZIP code
        
        Args:
            zip_code: The ZIP code to get weather for
            
        Returns:
            WeatherData: Structured weather information
            
        Raises:
            ValueError: If the ZIP code is invalid
            requests.RequestException: If the API request fails
            TimeoutError: If the API request times out
            KeyError: If the API response is missing required data
        """
        if not self._validate_zip_code(zip_code):
            raise ValueError(f"Invalid ZIP code format: {zip_code}")

        # Apply rate limiting
        self._apply_rate_limit()
            
        # Try to get cached data first
        cached_data = self._get_cached_weather(zip_code)
        if cached_data:
            logger.debug(f"Returning cached weather data for {zip_code}")
            return self._parse_weather_data(zip_code, cached_data)
            
        # Prepare API request
        params = {
            'access_key': self.api_key,
            'query': zip_code,
            'units': 'f'
        }
        
        # Log request details (with masked API key)
        debug_params = params.copy()
        debug_params['access_key'] = f"****{params['access_key'][-4:]}"
        logger.debug("API Request:")
        logger.debug(f"  URL: {self.base_url}")
        logger.debug(f"  Parameters: {debug_params}")
        
        try:
            # Ensure using HTTP for free plan
            if self.base_url.startswith('https'):
                logger.warning("Converting HTTPS to HTTP for free plan compatibility")
                self.base_url = self.base_url.replace('https', 'http')
            
            # Make request with timeout
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                error_info = data['error']
                error_message = error_info.get('info', 'Unknown error occurred')
                raise ValueError(f"API Error: {error_message}")

            # Cache the successful response
            self._cache_weather(zip_code, data)
            
            # Update last request time for rate limiting
            self._last_request_time = time.time()
                
            return self._parse_weather_data(zip_code, data)
            
        except requests.Timeout:
            logger.error("API request timed out")
            raise TimeoutError("Weather API request timed out")
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
            
    def _validate_api_key(self) -> bool:
        """
        Validate the API key format
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        return bool(self.api_key and len(self.api_key) >= 32)
        
    @staticmethod
    def _validate_zip_code(zip_code: str) -> bool:
        """
        Validate ZIP code format
        
        Args:
            zip_code: The ZIP code to validate
            
        Returns:
            bool: True if the ZIP code is valid, False otherwise
        """
        return bool(zip_code and len(zip_code) == 5 and zip_code.isnumeric())

    def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting to API requests.
        Ensures a minimum time between requests to avoid hitting API limits.
        """
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                sleep_time = self._min_request_interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

    def _get_cached_weather(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Get cached weather data if available and not expired
        
        Args:
            zip_code: The ZIP code to get cached data for
            
        Returns:
            Optional[Dict[str, Any]]: Cached weather data if available and not expired
        """
        if zip_code in self._weather_cache:
            timestamp = self._cache_timestamps.get(zip_code, 0)
            if time.time() - timestamp < self.cache_timeout:
                return self._weather_cache[zip_code]
            else:
                # Clean up expired cache entry
                del self._weather_cache[zip_code]
                del self._cache_timestamps[zip_code]
        return None

    def _cache_weather(self, zip_code: str, data: Dict[str, Any]) -> None:
        """
        Cache weather data for a ZIP code
        
        Args:
            zip_code: The ZIP code to cache data for
            data: The weather data to cache
        """
        self._weather_cache[zip_code] = data
        self._cache_timestamps[zip_code] = time.time()
        
    def _parse_weather_data(self, zip_code: str, data: Dict[str, Any]) -> WeatherData:
        """
        Parse raw API response into structured WeatherData
        
        Args:
            zip_code: The ZIP code for this weather data
            data: Raw API response data
            
        Returns:
            WeatherData: Structured weather information
            
        Raises:
            KeyError: If required data is missing from the API response
        """
        try:
            current = data['current']
            location = data['location']
            
            return WeatherData(
                temperature=float(current['temperature']),
                location_name=location['name'],
                description=current['weather_descriptions'][0],
                humidity=int(current['humidity']),
                wind_speed=float(current['wind_speed']),
                icon_url=current['weather_icons'][0],
                timestamp=datetime.fromtimestamp(location['localtime_epoch']),
                zip_code=zip_code
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse weather data: {str(e)}")
            raise KeyError(f"Missing required data in API response: {str(e)}") 