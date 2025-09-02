"""
Client Telethon (optionnel)
"""

from typing import Optional
from telethon import TelegramClient
from telethon.sessions import StringSession

from ..config import Config
from ..logger import setup_logger

logger = setup_logger(__name__)


class TelethonClient:
    """Wrapper pour Telethon client"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[TelegramClient] = None
        self.session_string = None
        
    async def create_client(self, session_string: Optional[str] = None):
        """Crée et connecte le client Telethon"""
        try:
            session = StringSession(session_string) if session_string else "telethon_session"
            
            self.client = TelegramClient(
                session,
                self.config.API_ID,
                self.config.API_HASH
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.warning("Client Telethon non autorisé - connexion requise")
                return False
            
            logger.info("Client Telethon connecté avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du client Telethon: {e}")
            return False
    
    async def start(self):
        """Démarre le client"""
        if self.client:
            await self.client.start(bot_token=self.config.BOT_TOKEN)
            logger.info("Client Telethon démarré")
    
    async def stop(self):
        """Arrête le client"""
        if self.client:
            await self.client.disconnect()
            logger.info("Client Telethon déconnecté")
    
    def get_client(self) -> Optional[TelegramClient]:
        """Retourne le client Telethon"""
        return self.client
    
    async def download_media(self, message, file_path: Optional[str] = None):
        """Télécharge un média"""
        if not self.client:
            raise RuntimeError("Client Telethon non initialisé")
        
        return await self.client.download_media(message, file_path)
    
    async def send_file(
        self,
        entity,
        file,
        caption: Optional[str] = None,
        **kwargs
    ):
        """Envoie un fichier"""
        if not self.client:
            raise RuntimeError("Client Telethon non initialisé")
        
        return await self.client.send_file(
            entity,
            file,
            caption=caption,
            **kwargs
        )
