"""
Location storage module for the Weather App
"""

from typing import Dict, Optional

class LocationStorage:
    """Class to handle storage and retrieval of weather locations"""
    
    def __init__(self):
        self.locations: Dict[str, str] = {}
    
    def add_location(self, zip_code: str, location_name: str) -> None:
        """Add a new location to the storage"""
        if zip_code and location_name:
            self.locations[zip_code] = location_name
    
    def remove_location(self, zip_code: str) -> bool:
        """Remove a location from storage"""
        if zip_code in self.locations:
            del self.locations[zip_code]
            return True
        return False
    
    def get_locations(self) -> Dict[str, str]:
        """Get all stored locations as a dictionary of zip_code: location_name pairs"""
        return self.locations.copy()
    
    def clear(self) -> None:
        """Clear all stored locations"""
        self.locations.clear() 