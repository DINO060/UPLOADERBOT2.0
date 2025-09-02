"""
Configuration centralisée de l'application
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class Config:
    """Configuration de l'application"""
    
    def __init__(self):
        # Bot Configuration
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.BOT_USERNAME = os.getenv("BOT_USERNAME", "")
        
        # Database Configuration
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.DB_NAME = os.getenv("DB_NAME", "telegram_bot")
        
        # Admin Configuration
        self.ADMIN_IDS = self._parse_list(os.getenv("ADMIN_IDS", ""))
        self.OWNER_ID = int(os.getenv("OWNER_ID", "0"))
        
        # Force Subscribe Configuration
        self.FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
        
        # API Configuration (for Telethon/Pyrogram if needed)
        self.API_ID = int(os.getenv("API_ID", "0"))
        self.API_HASH = os.getenv("API_HASH", "")
        
        # File Configuration
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "2097152000"))  # 2GB
        self.THUMBNAIL_SIZE = (320, 320)
        self.ALLOWED_EXTENSIONS = self._parse_list(
            os.getenv("ALLOWED_EXTENSIONS", ".jpg,.png,.mp4,.mkv,.zip")
        )
        
        # Scheduler Configuration
        self.DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
        self.AUTO_DELETE_HOURS = int(os.getenv("AUTO_DELETE_HOURS", "24"))
        
        # Rate Limiting
        self.RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "30"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "bot.log")
        
        # Feature Flags
        self.ENABLE_REACTIONS = os.getenv("ENABLE_REACTIONS", "true").lower() == "true"
        self.ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        self.ENABLE_FORCE_SUB = os.getenv("ENABLE_FORCE_SUB", "false").lower() == "true"
        
        self._validate_config()
    
    def _parse_list(self, value: str) -> list:
        """Parse une chaîne séparée par des virgules en liste"""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _validate_config(self):
        """Valide la configuration"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN est requis dans le fichier .env")
        
        if self.ENABLE_FORCE_SUB and not self.FORCE_SUB_CHANNEL:
            raise ValueError("FORCE_SUB_CHANNEL est requis quand ENABLE_FORCE_SUB est activé")
    
    @property
    def is_development(self) -> bool:
        """Vérifie si on est en mode développement"""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Vérifie si on est en mode production"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_collection_name(self, collection: str) -> str:
        """Retourne le nom de la collection avec préfixe si nécessaire"""
        prefix = os.getenv("COLLECTION_PREFIX", "")
        return f"{prefix}{collection}" if prefix else collection
