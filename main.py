"""
Weather App - Main entry point
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.weather_app.api.weather_client import WeatherStackClient
from src.weather_app.ui.weather_app import WeatherApp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_key() -> str:
    """Load and validate the API key from environment variables"""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('WEATHERSTACK_API_KEY')

    if not api_key:
        logger.error("No API key found! Make sure WEATHERSTACK_API_KEY is set in your .env file")
        raise ValueError("API key not found")

    # Remove any whitespace and validate
    api_key = api_key.strip()
    
    # Log API key stats (masked)
    logger.debug(f"API key stats:")
    logger.debug(f"  Length: {len(api_key)}")
    logger.debug(f"  First 4 chars: {api_key[:4]}")
    logger.debug(f"  Last 4 chars: {api_key[-4:]}")
    logger.debug(f"  Contains whitespace: {'yes' if any(c.isspace() for c in api_key) else 'no'}")
    has_quotes = "'" in api_key or '"' in api_key
    logger.debug(f"  Contains quotes: {'yes' if has_quotes else 'no'}")
    
    return api_key

def main():
    """Main entry point for the Weather App"""
    try:
        # Initialize API client
        api_key = load_api_key()
        api_client = WeatherStackClient(api_key)
        
        # Start the application
        logger.debug("Starting Weather App")
        WeatherApp(api_client=api_client).run()
        
    except Exception as e:
        logger.error("Application failed to start", exc_info=True)
        raise

if __name__ == '__main__':
    main()
