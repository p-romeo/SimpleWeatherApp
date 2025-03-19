"""
Location storage module for the Weather App
"""

from typing import List, Optional

class LocationStorage:
    """Class to handle storage and retrieval of weather locations"""
    
    def __init__(self):
        self.locations: List[str] = []
    
    def add_location(self, location: str) -> None:
        """Add a new location to the storage"""
        if location and location not in self.locations:
            self.locations.append(location)
    
    def remove_location(self, location: str) -> bool:
        """Remove a location from storage"""
        if location in self.locations:
            self.locations.remove(location)
            return True
        return False
    
    def get_locations(self) -> List[str]:
        """Get all stored locations"""
        return self.locations.copy()
    
    def clear(self) -> None:
        """Clear all stored locations"""
        self.locations.clear() 