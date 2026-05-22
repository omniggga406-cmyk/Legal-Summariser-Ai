import os

class Settings:
    # Paste your actual fresh Google AI Studio API key directly inside the quotes below
    GEMINI_API_KEY = "AIzaSyCrQKhihMSDiRSy4Kfp2uuKDo1HTfR1BsU"

    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY or "YourNewActual" in cls.GEMINI_API_KEY:
            raise ValueError("CRITICAL ERROR: Key is missing in config/settings.py")

Settings.validate()
