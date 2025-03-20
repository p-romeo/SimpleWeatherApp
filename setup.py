from setuptools import setup, find_packages

setup(
    name="weather_app",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "kivy>=2.3.0",
        "kivymd>=1.1.1",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple weather application using Kivy and WeatherStack API",
    keywords="weather, kivy, gui",
    entry_points={
        'console_scripts': [
            'weather-app=weather_app.main:main',
        ],
        'gui_scripts': [
            'weather-app-gui=weather_app.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Win32 (MS Windows)",
    ],
    package_data={
        'weather_app': ['*.kv', '*.png', '*.ico'],
    },
    include_package_data=True,
) 