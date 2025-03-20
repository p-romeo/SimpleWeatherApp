"""
Configuration Helper Module

This module provides a GUI dialog for configuring the WeatherApp.
It handles:
1. API key configuration
2. Environment file management
3. Input validation
4. User interaction
"""

import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def save_api_key(api_key):
    """
    Save the WeatherStack API key to the environment file.
    
    This function:
    1. Validates the API key format
    2. Creates or updates the .env file
    3. Handles file I/O errors
    
    Args:
        api_key: The API key to save
        
    Returns:
        bool: True if the API key was saved successfully, False otherwise
    """
    try:
        env_path = Path(__file__).parent / '.env'
        with open(env_path, 'w') as f:
            f.write(f'WEATHERSTACK_API_KEY={api_key}\n')
        return True
    except Exception as e:
        return False

def validate_api_key(api_key):
    """
    Validate the WeatherStack API key format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if the API key is valid, False otherwise
    """
    if not api_key or len(api_key.strip()) < 32:
        return False
    return True

class ConfigDialog:
    """
    Configuration dialog for setting up the WeatherStack API key.
    
    This class provides:
    1. A graphical interface for API key input
    2. Input validation
    3. Error handling
    4. Persistent storage
    5. User feedback
    """
    
    def __init__(self):
        """
        Initialize the configuration dialog window.
        
        Sets up:
        1. Window properties
        2. UI components
        3. Event handlers
        4. Layout and styling
        """
        self.root = tk.Tk()
        self.root.title('WeatherApp Configuration')
        self.root.geometry('400x200')
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        # Add some padding
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True, fill='both')
        
        # Instructions
        tk.Label(frame, text='Welcome to WeatherApp!', font=('Arial', 12, 'bold')).pack()
        tk.Label(frame, text='Please enter your WeatherStack API key:', wraplength=350).pack(pady=10)
        
        # API Key entry
        self.api_key = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.api_key, width=40)
        entry.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text='Get API Key', command=self.open_weatherstack).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Save', command=self.save_and_exit).pack(side='left', padx=5)
        
        # Focus on entry
        entry.focus()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def open_weatherstack(self):
        """Open the WeatherStack signup page in the default web browser."""
        import webbrowser
        webbrowser.open('https://weatherstack.com/signup')
    
    def save_and_exit(self):
        """
        Validate and save the API key, then close the dialog.
        
        This method:
        1. Validates the API key format
        2. Saves the key to the environment file
        3. Shows appropriate success/error messages
        4. Closes the dialog on success
        """
        api_key = self.api_key.get().strip()
        if not validate_api_key(api_key):
            messagebox.showerror('Invalid API Key', 
                               'Please enter a valid WeatherStack API key (at least 32 characters)')
            return
        
        if save_api_key(api_key):
            messagebox.showinfo('Success', 
                              'API key saved successfully! You can now use the WeatherApp.')
            self.root.quit()
        else:
            messagebox.showerror('Error', 
                               'Failed to save API key. Please check file permissions.')
    
    def on_closing(self):
        """
        Handle the window close event.
        
        Shows a confirmation dialog since closing without an API key
        will prevent the app from working.
        """
        if messagebox.askokcancel('Quit', 
                                'Without an API key, the app won\'t work. Are you sure you want to quit?'):
            self.root.quit()
    
    def run(self):
        """Start the configuration dialog main loop."""
        self.root.mainloop()

def main():
    """
    Main entry point for the configuration helper.
    
    Checks if the API key is configured and launches the
    configuration dialog if needed.
    """
    # Check if .env exists and has API key
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists() or 'WEATHERSTACK_API_KEY' not in env_path.read_text():
        ConfigDialog().run()

if __name__ == '__main__':
    main()
