from setuptools import setup, find_packages

setup(
    name="weather_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.2",
        "python-dotenv>=1.0.0",
        "kivy>=2.3.0"
    ],
) 