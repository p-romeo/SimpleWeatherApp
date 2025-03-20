"""
Unit tests for the LocationStorage class.
"""

import os
import json
import pytest
from pathlib import Path
from weather_app.storage.location_storage import LocationStorage

@pytest.fixture
def temp_storage_file(tmp_path):
    """Create a temporary storage file."""
    storage_file = tmp_path / "test_locations.json"
    return str(storage_file)

@pytest.fixture
def storage(temp_storage_file):
    """Create a LocationStorage instance for testing."""
    return LocationStorage(storage_file=temp_storage_file)

def test_init_storage(temp_storage_file):
    """Test storage initialization."""
    # Test with non-existent file
    storage = LocationStorage(storage_file=temp_storage_file)
    assert storage.locations == {}
    assert Path(temp_storage_file).exists()
    
    # Test with existing file
    data = {"12345": {"name": "Test City", "is_favorite": True}}
    with open(temp_storage_file, 'w') as f:
        json.dump(data, f)
    
    storage = LocationStorage(storage_file=temp_storage_file)
    assert storage.locations == data

def test_validate_zip_code(storage):
    """Test ZIP code validation."""
    # Valid ZIP codes
    assert storage._validate_zip_code("12345") is True
    
    # Invalid ZIP codes
    assert storage._validate_zip_code("1234") is False  # Too short
    assert storage._validate_zip_code("123456") is False  # Too long
    assert storage._validate_zip_code("abcde") is False  # Non-numeric
    assert storage._validate_zip_code("") is False  # Empty
    assert storage._validate_zip_code("12 34") is False  # Contains space

def test_add_location(storage):
    """Test adding locations."""
    # Add valid location
    assert storage.add_location("12345", "Test City") is True
    assert "12345" in storage.locations
    assert storage.locations["12345"]["name"] == "Test City"
    assert storage.locations["12345"]["is_favorite"] is False
    
    # Add invalid location
    with pytest.raises(ValueError):
        storage.add_location("invalid", "Test City")
    
    # Add duplicate location
    assert storage.add_location("12345", "New Name") is True
    assert storage.locations["12345"]["name"] == "New Name"

def test_remove_location(storage):
    """Test removing locations."""
    # Add and remove location
    storage.add_location("12345", "Test City")
    assert storage.remove_location("12345") is True
    assert "12345" not in storage.locations
    
    # Remove non-existent location
    assert storage.remove_location("54321") is False

def test_get_locations(storage):
    """Test retrieving locations."""
    # Empty storage
    assert storage.get_locations() == []
    
    # Add locations
    storage.add_location("12345", "City 1")
    storage.add_location("54321", "City 2")
    
    locations = storage.get_locations()
    assert len(locations) == 2
    assert "12345" in locations
    assert "54321" in locations

def test_set_favorite(storage):
    """Test favorite location functionality."""
    storage.add_location("12345", "Test City")
    
    # Set as favorite
    assert storage.set_favorite("12345", True) is True
    assert storage.locations["12345"]["is_favorite"] is True
    
    # Set as non-favorite
    assert storage.set_favorite("12345", False) is True
    assert storage.locations["12345"]["is_favorite"] is False
    
    # Set non-existent location
    with pytest.raises(KeyError):
        storage.set_favorite("54321", True)

def test_is_favorite(storage):
    """Test checking favorite status."""
    storage.add_location("12345", "Test City")
    
    # Initially not favorite
    assert storage.is_favorite("12345") is False
    
    # Set as favorite
    storage.set_favorite("12345", True)
    assert storage.is_favorite("12345") is True
    
    # Non-existent location
    assert storage.is_favorite("54321") is False

def test_save_and_load(storage, temp_storage_file):
    """Test saving and loading storage data."""
    # Add test data
    storage.add_location("12345", "Test City")
    storage.set_favorite("12345", True)
    
    # Save data
    storage.save()
    
    # Create new storage instance
    new_storage = LocationStorage(storage_file=temp_storage_file)
    
    # Verify data was loaded
    assert "12345" in new_storage.locations
    assert new_storage.locations["12345"]["name"] == "Test City"
    assert new_storage.locations["12345"]["is_favorite"] is True

def test_storage_file_permissions(temp_storage_file):
    """Test handling of storage file permission issues."""
    storage = LocationStorage(storage_file=temp_storage_file)
    
    # Make file read-only
    os.chmod(temp_storage_file, 0o444)
    
    # Attempt to save should not raise exception
    try:
        storage.save()
    except Exception as e:
        pytest.fail(f"save() raised {e} when handling permission error") 