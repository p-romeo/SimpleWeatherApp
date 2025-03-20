"""
Build script for creating a signed Windows executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_config_helper():
    """Create a configuration helper script"""
    config_script = """import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def save_api_key(api_key):
    try:
        env_path = Path(__file__).parent / '.env'
        with open(env_path, 'w') as f:
            f.write(f'WEATHERSTACK_API_KEY={api_key}\\n')
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
                                'Without an API key, the app won\\'t work. Are you sure you want to quit?'):
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
"""
    
    # Write the configuration helper
    config_path = Path('src/weather_app/config_helper.py')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_script)
    return config_path

def run_command(command):
    """Run a command and print its output"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def build_exe():
    """Build the executable using PyInstaller"""
    try:
        # Ensure we're in the right directory
        os.chdir(Path(__file__).parent)
        
        # Create configuration helper
        print("Creating configuration helper...")
        config_path = create_config_helper()
        
        # Clean previous builds
        for dir_name in ['build', 'dist']:
            if Path(dir_name).exists():
                print(f"Cleaning {dir_name} directory...")
                shutil.rmtree(dir_name)
        
        # Install required packages
        print("Installing required packages...")
        run_command("pip install -r requirements.txt")
        run_command("pip install pyinstaller")
        
        # Create the executable
        print("Creating executable...")
        pyinstaller_command = (
            "pyinstaller --noconfirm --onefile --windowed "
            "--add-data src/weather_app/config_helper.py;weather_app "
            "--name WeatherApp main.py"
        )
        if not run_command(pyinstaller_command):
            print("Failed to create executable")
            return False
        
        # Sign the executable if code signing certificate is available
        cert_path = os.getenv("CODE_SIGNING_CERT")
        cert_password = os.getenv("CODE_SIGNING_PASSWORD")
        
        if cert_path and cert_password and Path(cert_path).exists():
            print("Signing executable...")
            signtool_path = shutil.which('signtool')
            if not signtool_path:
                print("Warning: signtool not found. Skipping signing step.")
            else:
                signtool_command = (
                    f'"{signtool_path}" sign /f "{cert_path}" /p {cert_password} '
                    '/tr http://timestamp.digicert.com /td sha256 /fd sha256 '
                    'dist/WeatherApp.exe'
                )
                if not run_command(signtool_command):
                    print("Failed to sign executable")
                    return False
        else:
            print("No code signing certificate found. Skipping signing step.")
        
        print("\nBuild completed successfully!")
        print("Executable location: dist/WeatherApp.exe")
        return True
        
    except Exception as e:
        print(f"Build failed: {e}")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1) 