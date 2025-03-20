import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def save_api_key(api_key):
    try:
        env_path = Path(__file__).parent / '.env'
        with open(env_path, 'w') as f:
            f.write(f'WEATHERSTACK_API_KEY={api_key}\n')
        return True
    except Exception as e:
        return False

def validate_api_key(api_key):
    # Basic validation
    if not api_key or len(api_key.strip()) < 32:
        return False
    return True

class ConfigDialog:
    def __init__(self):
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
        import webbrowser
        webbrowser.open('https://weatherstack.com/signup')
    
    def save_and_exit(self):
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
        if messagebox.askokcancel('Quit', 
                                'Without an API key, the app won\'t work. Are you sure you want to quit?'):
            self.root.quit()
    
    def run(self):
        self.root.mainloop()

def main():
    # Check if .env exists and has API key
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists() or 'WEATHERSTACK_API_KEY' not in env_path.read_text():
        ConfigDialog().run()

if __name__ == '__main__':
    main()
