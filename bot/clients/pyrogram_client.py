"""
Client Pyrogram (optionnel)
"""

from typing import Optional
from pyrogram import Client
from pyrogram.types import Message

from ..config import Config
from ..logger import setup_logger

logger = setup_logger(__name__)


class PyrogramClient:
    """Wrapper pour Pyrogram client"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[Client] = None
        
    async def create_client(self, session_name: str = "pyrogram_bot"):
        """Crée le client Pyrogram"""
        try:
            self.client = Client(
                session_name,
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                bot_token=self.config.BOT_TOKEN
            )
            
            logger.info("Client Pyrogram créé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du client Pyrogram: {e}")
            return False
    
    async def start(self):
        """Démarre le client"""
        if self.client:
            await self.client.start()
            logger.info("Client Pyrogram démarré")
            
            # Log des informations du bot
            me = await self.client.get_me()
            logger.info(f"Bot: @{me.username} (ID: {me.id})")
    
    async def stop(self):
        """Arrête le client"""
        if self.client:
            await self.client.stop()
            logger.info("Client Pyrogram arrêté")
    
    def get_client(self) -> Optional[Client]:
        """Retourne le client Pyrogram"""
        return self.client
    
    async def download_media(
        self,
        message: Message,
        file_path: Optional[str] = None,
        progress: Optional[callable] = None
    ):
        """Télécharge un média avec progress callback"""
        if not self.client:
            raise RuntimeError("Client Pyrogram non initialisé")
        
        return await self.client.download_media(
            message,
            file_name=file_path,
            progress=progress
        )
    
    async def send_document(
        self,
        chat_id: int,
        document: str,
        caption: Optional[str] = None,
        progress: Optional[callable] = None,
        **kwargs
    ):
        """Envoie un document avec progress callback"""
        if not self.client:
            raise RuntimeError("Client Pyrogram non initialisé")
        
        return await self.client.send_document(
            chat_id,
            document,
            caption=caption,
            progress=progress,
            **kwargs
        )
    
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        **kwargs
    ):
        """Édite le texte d'un message"""
        if not self.client:
            raise RuntimeError("Client Pyrogram non initialisé")
        
        return await self.client.edit_message_text(
            chat_id,
            message_id,
            text,
            **kwargs
        )
