"""
Weather App - Main entry point

This module serves as the main entry point for the Weather App application.
It handles:
1. Environment configuration and validation
2. Logging setup
3. API client initialization
4. Application startup
5. Graceful shutdown
"""

import os
import sys
import logging
import signal
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from src.weather_app.api.weather_client import WeatherStackClient
from src.weather_app.storage.location_storage import LocationStorage
from src.weather_app.ui.weather_app import WeatherApp

# Initialize logger
logger = logging.getLogger(__name__)

# Global variables for cleanup
api_client: Optional[WeatherStackClient] = None
weather_app: Optional[WeatherApp] = None

def setup_logging() -> None:
    """
    Set up application logging.
    
    This function:
    1. Creates a logs directory if it doesn't exist
    2. Configures logging format and handlers
    3. Sets up both file and console logging
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Set up handlers
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / 'weather_app.log')
    ]
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Log startup message
    logger.info("Logging system initialized")

def setup_environment() -> Dict[str, Any]:
    """
    Set up the application environment.
    
    This function:
    1. Loads environment variables from .env file
    2. Validates required environment variables
    3. Sets up any necessary environment configurations
    
    Returns:
        Dict[str, Any]: Configuration dictionary
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Load environment variables
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ['WEATHERSTACK_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Build configuration dictionary
    config = {
        'api_key': os.getenv('WEATHERSTACK_API_KEY', '').strip(),
        'storage_file': os.getenv('LOCATIONS_FILE', 'data/locations.json'),
        'cache_timeout': int(os.getenv('CACHE_TIMEOUT', '300')),
        'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '10'))
    }
    
    return config

def load_api_key(api_key: str) -> str:
    """
    Load and validate the API key.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        str: The validated API key
        
    Raises:
        ValueError: If the API key is invalid
    """
    api_key = api_key.strip()
    
    if not api_key:
        logger.error("No API key found! Make sure WEATHERSTACK_API_KEY is set in your .env file")
        raise ValueError("API key not found")
    
    # Validate API key format
    if len(api_key) < 32:
        logger.error("API key appears to be invalid (too short)")
        raise ValueError("Invalid API key format")
    
    # Log API key stats (masked for security)
    logger.debug("API key validation:")
    logger.debug(f"  Length: {len(api_key)}")
    logger.debug(f"  First 4 chars: {api_key[:4]}")
    logger.debug(f"  Last 4 chars: {api_key[-4:]}")
    logger.debug(f"  Contains whitespace: {'yes' if any(c.isspace() for c in api_key) else 'no'}")
    has_quotes = "'" in api_key or '"' in api_key
    logger.debug(f"  Contains quotes: {'yes' if has_quotes else 'no'}")
    
    return api_key

def initialize_components(config: Dict[str, Any]) -> None:
    """
    Initialize application components.
    
    Args:
        config: Application configuration dictionary
        
    Raises:
        Exception: If component initialization fails
    """
    global api_client, weather_app
    
    try:
        # Initialize API client
        api_key = load_api_key(config['api_key'])
        api_client = WeatherStackClient(
            api_key=api_key,
            cache_timeout=config['cache_timeout'],
            request_timeout=config['request_timeout']
        )
        logger.info("API client initialized successfully")
        
        # Initialize location storage
        storage = LocationStorage(storage_file=config['storage_file'])
        logger.info("Location storage initialized successfully")
        
        # Initialize weather app
        weather_app = WeatherApp(api_client=api_client, location_storage=storage)
        logger.info("Weather app initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize components", exc_info=True)
        raise

def cleanup() -> None:
    """
    Clean up application resources.
    
    This function:
    1. Closes any open connections
    2. Saves any pending data
    3. Performs final cleanup
    """
    global api_client, weather_app
    
    logger.info("Starting application cleanup")
    
    try:
        if weather_app:
            weather_app.cleanup()
        if api_client:
            api_client.cleanup()
    except Exception as e:
        logger.error("Error during cleanup", exc_info=True)
    
    logger.info("Cleanup completed")

def signal_handler(signum: int, frame: Any) -> None:
    """
    Handle system signals for graceful shutdown.
    
    Args:
        signum: The signal number
        frame: The current stack frame
    """
    logger.info(f"Received signal {signum}, initiating shutdown")
    cleanup()
    sys.exit(0)

def main() -> None:
    """
    Main entry point for the Weather App.
    
    This function:
    1. Sets up the environment
    2. Initializes components
    3. Starts the application
    4. Handles any startup errors
    """
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Set up logging
        setup_logging()
        
        # Set up environment
        config = setup_environment()
        
        # Initialize components
        initialize_components(config)
        
        # Start the application
        logger.info("Starting Weather App")
        weather_app.run()
        
    except Exception as e:
        logger.error("Application failed to start", exc_info=True)
        cleanup()
        sys.exit(1)
    finally:
        cleanup()

if __name__ == '__main__':
    main()
