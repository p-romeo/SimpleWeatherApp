"""
WeatherStack API client implementation
"""

import logging
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

class WeatherStackClient:
    """Client for interacting with the WeatherStack API"""
    
    def __init__(self, api_key: str, base_url: str = 'http://api.weatherstack.com/current',
                 cache_timeout: int = 300, request_timeout: int = 10):
        """
        Initialize the WeatherStack API client
        
        Args:
            api_key: The API key for WeatherStack
            base_url: The base URL for the API
            cache_timeout: How long to cache results in seconds (default 5 minutes)
            request_timeout: How long to wait for API response in seconds (default 10 seconds)
        """
        self.api_key = api_key.strip()
        self.base_url = base_url
        self.cache_timeout = cache_timeout
        self.request_timeout = request_timeout
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum time between requests in seconds
        
    def get_weather(self, zip_code: str) -> Dict[str, Any]:
        """
        Get weather data for a specific ZIP code
        
        Args:
            zip_code: The ZIP code to get weather for
            
        Returns:
            Dict containing weather data
            
        Raises:
            ValueError: If the API key is invalid or ZIP code is invalid
            requests.RequestException: If the API request fails
            TimeoutError: If the API request times out
        """
        if not self._validate_api_key():
            raise ValueError("Invalid API key")
            
        if not self._validate_zip_code(zip_code):
            raise ValueError(f"Invalid ZIP code format: {zip_code}")

        # Apply rate limiting
        self._apply_rate_limit()
            
        # Try to get cached data first
        cached_data = self._get_cached_weather(zip_code)
        if cached_data:
            logger.debug(f"Returning cached weather data for {zip_code}")
            return cached_data
            
        params = {
            'access_key': self.api_key,
            'query': zip_code,
            'units': 'f'
        }
        
        # Log request details (with masked API key)
        debug_params = params.copy()
        debug_params['access_key'] = f"****{params['access_key'][-4:]}"
        logger.debug(f"API Request:")
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
                raise ValueError(error_message)

            # Cache the successful response
            self._cache_weather(zip_code, data)
            
            # Update last request time for rate limiting
            self._last_request_time = time.time()
                
            return data
            
        except requests.Timeout:
            logger.error("API request timed out")
            raise TimeoutError("Weather API request timed out")
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
            
    def _validate_api_key(self) -> bool:
        """Validate the API key format"""
        if not self.api_key:
            return False
        return True
        
    @staticmethod
    def _validate_zip_code(zip_code: str) -> bool:
        """Validate ZIP code format"""
        return bool(zip_code and len(zip_code) == 5 and zip_code.isnumeric())

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests"""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                sleep_time = self._min_request_interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

    # Cache for weather data
    _weather_cache: Dict[str, Dict[str, Any]] = {}
    _cache_timestamps: Dict[str, float] = {}

    def _get_cached_weather(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data if available and not expired"""
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
        """Cache weather data for a ZIP code"""
        self._weather_cache[zip_code] = data
        self._cache_timestamps[zip_code] = time.time() 