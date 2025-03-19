"""
Main module for the Weather App

This module handles:
1. Environment configuration
2. Logging setup
3. API client initialization
4. Application startup
5. Graceful shutdown
"""

import os
import sys
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

from weather_app.ui.weather_app import WeatherApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)-7s] %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables."""
    load_dotenv()
    
    api_key = os.getenv('WEATHERSTACK_API_KEY', '').strip()
    if not api_key:
        logger.error("WEATHERSTACK_API_KEY environment variable is not set")
        return False
    
    if len(api_key) < 32:  # WeatherStack API keys are typically 32 characters
        logger.error("Invalid WEATHERSTACK_API_KEY format")
        return False
    
    return True

def main():
    """Main entry point for the Weather App"""
    try:
        # Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Initialize and run the app
        logger.info("Starting Weather App")
        app = WeatherApp()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
