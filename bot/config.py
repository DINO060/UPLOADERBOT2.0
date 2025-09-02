"""
Configuration centralisée de l'application (robuste .env)
"""
import os
from typing import Optional, List, Set
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de l'application"""

    def __init__(self) -> None:
        # ---- Bot
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
        self.BOT_USERNAME: str = os.getenv("BOT_USERNAME", "").strip()

        # ---- Database (accepte MONGODB_URI ou MONGO_URI)
        mongo_uri = os.getenv("MONGODB_URI", "").strip() or os.getenv("MONGO_URI", "").strip()
        self.MONGO_URI: str = mongo_uri or "mongodb://localhost:27017"
        self.DB_NAME: str = os.getenv("DB_NAME", "telegram_bot").strip() or "telegram_bot"
        self.COLLECTION_PREFIX: str = os.getenv("COLLECTION_PREFIX", "").strip()

        # ---- Admins / Owner
        self.ADMIN_IDS: List[int] = self._parse_int_list(os.getenv("ADMIN_IDS", ""))
        self.OWNER_ID: int = self._parse_int(os.getenv("OWNER_ID", "0"))

        # ---- Force Subscribe (1 ou plusieurs canaux)
        #  - rétro-compat: FORCE_SUB_CHANNEL (string simple)
        #  - nouveau: FORCE_SUB_CHANNELS (liste)
        self.FORCE_SUB_CHANNEL: str = os.getenv("FORCE_SUB_CHANNEL", "").strip()
        self.FORCE_SUB_CHANNELS: List[str] = self._parse_str_list(os.getenv("FORCE_SUB_CHANNELS", ""))

        # ---- API (optionnel pour Telethon/Pyrogram)
        self.API_ID: int = self._parse_int(os.getenv("API_ID", "0"))
        self.API_HASH: str = os.getenv("API_HASH", "").strip()

        # ---- Fichiers
        self.MAX_FILE_SIZE: int = self._parse_int(os.getenv("MAX_FILE_SIZE", str(2 * 1024 * 1024 * 1024)))  # 2GB
        self.THUMBNAIL_SIZE = (320, 320)
        self.ALLOWED_EXTENSIONS: Set[str] = self._parse_ext_set(
            os.getenv("ALLOWED_EXTENSIONS", ".jpg,.png,.mp4,.mkv,.zip")
        )

        # ---- Scheduler / Time
        self.DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "UTC").strip()
        self.AUTO_DELETE_HOURS: int = self._parse_int(os.getenv("AUTO_DELETE_HOURS", "24"))

        # ---- Rate limiting
        self.RATE_LIMIT_MESSAGES: int = self._parse_int(os.getenv("RATE_LIMIT_MESSAGES", "30"))
        self.RATE_LIMIT_WINDOW: int = self._parse_int(os.getenv("RATE_LIMIT_WINDOW", "60"))

        # ---- Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FILE: str = os.getenv("LOG_FILE", "bot.log").strip()

        # ---- Feature flags
        self.ENABLE_REACTIONS: bool = self._get_bool(os.getenv("ENABLE_REACTIONS", "true"))
        self.ENABLE_SCHEDULER: bool = self._get_bool(os.getenv("ENABLE_SCHEDULER", "true"))
        self.ENABLE_FORCE_SUB: bool = self._get_bool(os.getenv("ENABLE_FORCE_SUB", "false"))

        # ---- Environment
        env = os.getenv("ENVIRONMENT", "development").lower().strip()
        self._ENV = env if env in {"development", "staging", "production"} else "development"

        self._validate_config()

    # -------- Helpers parsing --------
    def _get_bool(self, v: Optional[str]) -> bool:
        return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}

    def _parse_int(self, v: str, *, default: int = 0) -> int:
        try:
            return int(str(v).strip())
        except Exception:
            return default

    def _parse_str_list(self, value: str) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def _parse_int_list(self, value: str) -> List[int]:
        out: List[int] = []
        for item in self._parse_str_list(value):
            try:
                out.append(int(item))
            except Exception:
                # ignore silencieusement les entrées non numériques
                pass
        return out

    def _parse_ext_set(self, value: str) -> Set[str]:
        # normalise en set minuscule, avec point
        items = self._parse_str_list(value)
        norm = []
        for it in items:
            it = it.lower()
            if not it.startswith("."):
                it = "." + it
            norm.append(it)
        return set(norm)

    # -------- Validation --------
    def _validate_config(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN est requis dans le fichier .env")

        if not (self.MONGO_URI.startswith("mongodb://") or self.MONGO_URI.startswith("mongodb+srv://")):
            raise ValueError("MONGO_URI/MONGODB_URI doit commencer par mongodb:// ou mongodb+srv://")

        if not self.DB_NAME:
            raise ValueError("DB_NAME est requis (non vide)")

        if self.ENABLE_FORCE_SUB:
            # accepte l'un ou l'autre
            if not self.FORCE_SUB_CHANNEL and not self.FORCE_SUB_CHANNELS:
                raise ValueError("FORCE_SUB_CHANNEL(S) requis quand ENABLE_FORCE_SUB=true")

        if self.MAX_FILE_SIZE <= 0:
            raise ValueError("MAX_FILE_SIZE doit être > 0")

        if self.RATE_LIMIT_MESSAGES <= 0 or self.RATE_LIMIT_WINDOW <= 0:
            raise ValueError("RATE_LIMIT_MESSAGES et RATE_LIMIT_WINDOW doivent être > 0")

    # -------- Utils --------
    @property
    def is_development(self) -> bool:
        return self._ENV == "development"

    @property
    def is_production(self) -> bool:
        return self._ENV == "production"

    def get_collection_name(self, collection: str) -> str:
        """Retourne le nom de la collection avec préfixe si nécessaire"""
        return f"{self.COLLECTION_PREFIX}{collection}" if self.COLLECTION_PREFIX else collection