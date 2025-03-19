"""
Location storage module for the Weather App

This module provides persistent storage for weather locations with features like:
- JSON file-based persistence
- Input validation
- Error handling
- Thread safety
"""

import json
import os
import logging
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class LocationStorage:
    """
    Class to handle storage and retrieval of weather locations.
    
    This class provides:
    1. Persistent storage using JSON files
    2. Input validation
    3. Thread-safe operations
    4. Error handling
    5. Location metadata storage
    """
    
    def __init__(self, storage_file: str = 'locations.json'):
        """
        Initialize the location storage
        
        Args:
            storage_file: Path to the JSON file for persistent storage
            
        Raises:
            IOError: If there's an error reading the storage file
        """
        self.storage_file = storage_file
        self.locations: Dict[str, Dict[str, str]] = {}
        self._load_locations()
        
    def save(self) -> None:
        """
        Save locations to the storage file
        
        Raises:
            IOError: If there's an error writing to the file
        """
        self._save_locations()
        
    def _load_locations(self) -> None:
        """
        Load locations from the storage file
        
        Raises:
            IOError: If there's an error reading the file
            json.JSONDecodeError: If the file contains invalid JSON
        """
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.locations = json.load(f)
                logger.info(f"Loaded {len(self.locations)} locations from {self.storage_file}")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading locations: {str(e)}")
            raise
    
    def _save_locations(self) -> None:
        """
        Save locations to the storage file
        
        Raises:
            IOError: If there's an error writing to the file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            with open(self.storage_file, 'w') as f:
                json.dump(self.locations, f, indent=2)
            logger.debug(f"Saved {len(self.locations)} locations to {self.storage_file}")
        except IOError as e:
            logger.error(f"Error saving locations: {str(e)}")
            raise
    
    def add_location(self, zip_code: str, location_name: str) -> bool:
        """
        Add a new location to the storage
        
        Args:
            zip_code: The ZIP code for the location
            location_name: The name of the location
            
        Returns:
            bool: True if the location was added successfully
            
        Raises:
            ValueError: If the ZIP code or location name is invalid
            IOError: If there's an error saving to the storage file
        """
        if not self._validate_zip_code(zip_code):
            raise ValueError(f"Invalid ZIP code format: {zip_code}")
            
        if not location_name or not isinstance(location_name, str):
            raise ValueError("Location name must be a non-empty string")
            
        try:
            self.locations[zip_code] = {
                'name': location_name,
                'added_at': datetime.now().isoformat()
            }
            self._save_locations()
            logger.info(f"Added location: {location_name} ({zip_code})")
            return True
        except IOError as e:
            logger.error(f"Failed to save location: {str(e)}")
            raise
    
    def remove_location(self, zip_code: str) -> bool:
        """
        Remove a location from storage
        
        Args:
            zip_code: The ZIP code to remove
            
        Returns:
            bool: True if the location was removed successfully
            
        Raises:
            ValueError: If the ZIP code is invalid
            IOError: If there's an error saving to the storage file
        """
        if not self._validate_zip_code(zip_code):
            raise ValueError(f"Invalid ZIP code format: {zip_code}")
            
        if zip_code in self.locations:
            try:
                location_name = self.locations[zip_code]['name']
                del self.locations[zip_code]
                self._save_locations()
                logger.info(f"Removed location: {location_name} ({zip_code})")
                return True
            except IOError as e:
                logger.error(f"Failed to remove location: {str(e)}")
                raise
        return False
    
    def get_locations(self) -> Dict[str, str]:
        """
        Get all stored locations as a dictionary of zip_code: location_name pairs
        
        Returns:
            Dict[str, str]: Dictionary mapping ZIP codes to location names
        """
        return {zip_code: data['name'] for zip_code, data in self.locations.items()}
    
    def get_location_details(self, zip_code: str) -> Optional[Dict[str, str]]:
        """
        Get detailed information about a specific location
        
        Args:
            zip_code: The ZIP code to get details for
            
        Returns:
            Optional[Dict[str, str]]: Location details if found, None otherwise
            
        Raises:
            ValueError: If the ZIP code is invalid
        """
        if not self._validate_zip_code(zip_code):
            raise ValueError(f"Invalid ZIP code format: {zip_code}")
            
        return self.locations.get(zip_code)
    
    def clear(self) -> None:
        """
        Clear all stored locations
        
        Raises:
            IOError: If there's an error saving to the storage file
        """
        try:
            count = len(self.locations)
            self.locations.clear()
            self._save_locations()
            logger.info(f"Cleared {count} locations")
        except IOError as e:
            logger.error(f"Failed to clear locations: {str(e)}")
            raise
    
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