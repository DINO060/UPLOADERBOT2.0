"""
Repository pour la gestion des canaux
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.channel import Channel
from logger import setup_logger

logger = setup_logger(__name__)


class ChannelsRepository:
    """Repository pour les canaux"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.channels
    
    async def add_channel(self, channel: Channel) -> str:
        """Ajoute un nouveau canal"""
        try:
            channel_dict = channel.to_dict()
            result = await self.collection.insert_one(channel_dict)
            logger.info(f"Canal ajouté: {channel.channel_id} pour l'utilisateur {channel.user_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du canal: {e}")
            raise
    
    async def get_channel(self, channel_id: int) -> Optional[Channel]:
        """Récupère un canal par son ID"""
        try:
            channel_data = await self.collection.find_one({"channel_id": channel_id})
            if channel_data:
                return Channel.from_dict(channel_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du canal {channel_id}: {e}")
            return None
    
    async def get_user_channels(
        self,
        user_id: int,
        only_active: bool = False
    ) -> List[Channel]:
        """Récupère tous les canaux d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if only_active:
                filter_dict["is_active"] = True
            
            cursor = self.collection.find(filter_dict)
            channels = []
            async for channel_data in cursor:
                channels.append(Channel.from_dict(channel_data))
            return channels
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des canaux de l'utilisateur {user_id}: {e}")
            return []
    
    async def update_channel(
        self,
        channel_id: int,
        update_data: Dict[str, Any]
    ) -> bool:
        """Met à jour un canal"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"channel_id": channel_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du canal {channel_id}: {e}")
            return False
    
    async def upsert_channel(self, channel: Channel) -> bool:
        """Crée ou met à jour un canal"""
        try:
            channel_dict = channel.to_dict()
            result = await self.collection.update_one(
                {"channel_id": channel.channel_id, "user_id": channel.user_id},
                {"$set": channel_dict},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Erreur lors de l'upsert du canal {channel.channel_id}: {e}")
            return False
    
    async def delete_channel(self, channel_id: int, user_id: int) -> bool:
        """Supprime un canal"""
        try:
            result = await self.collection.delete_one({
                "channel_id": channel_id,
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du canal {channel_id}: {e}")
            return False
    
    async def toggle_channel_status(
        self,
        channel_id: int,
        user_id: int
    ) -> Optional[bool]:
        """Active/désactive un canal"""
        try:
            channel = await self.get_channel(channel_id)
            if channel and channel.user_id == user_id:
                new_status = not channel.is_active
                success = await self.update_channel(
                    channel_id,
                    {"is_active": new_status}
                )
                return new_status if success else None
            return None
        except Exception as e:
            logger.error(f"Erreur lors du toggle du canal {channel_id}: {e}")
            return None
    
    async def count_user_channels(
        self,
        user_id: int,
        only_active: bool = False
    ) -> int:
        """Compte le nombre de canaux d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if only_active:
                filter_dict["is_active"] = True
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Erreur lors du comptage des canaux: {e}")
            return 0
    
    async def get_all_channels(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Channel]:
        """Récupère tous les canaux avec pagination"""
        try:
            cursor = self.collection.find().skip(skip).limit(limit)
            channels = []
            async for channel_data in cursor:
                channels.append(Channel.from_dict(channel_data))
            return channels
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de tous les canaux: {e}")
            return []
    
    async def validate_channel_ownership(
        self,
        channel_id: int,
        user_id: int
    ) -> bool:
        """Vérifie si un utilisateur est propriétaire d'un canal"""
        try:
            channel = await self.get_channel(channel_id)
            return channel and channel.user_id == user_id
        except Exception as e:
            logger.error(f"Erreur lors de la validation du canal: {e}")
            return False
    
    async def update_last_post(
        self,
        channel_id: int,
        post_id: str
    ) -> bool:
        """Met à jour le dernier post envoyé dans le canal"""
        return await self.update_channel(
            channel_id,
            {
                "last_post_id": post_id,
                "last_post_at": datetime.utcnow()
            }
        )
