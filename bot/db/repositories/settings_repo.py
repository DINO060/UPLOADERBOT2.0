"""
Repository pour la gestion des paramètres utilisateur
"""

from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.settings import Settings
from logger import setup_logger

logger = setup_logger(__name__)


class SettingsRepository:
    """Repository pour les paramètres"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.settings
    
    async def get_settings(self, user_id: int) -> Optional[Settings]:
        """Récupère les paramètres d'un utilisateur"""
        try:
            settings_data = await self.collection.find_one({"user_id": user_id})
            if settings_data:
                return Settings.from_dict(settings_data)
            
            # Créer des paramètres par défaut si inexistants
            default_settings = Settings(user_id=user_id)
            await self.save_settings(default_settings)
            return default_settings
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des paramètres: {e}")
            return None
    
    async def save_settings(self, settings: Settings) -> bool:
        """Enregistre les paramètres"""
        try:
            settings_dict = settings.to_dict()
            result = await self.collection.update_one(
                {"user_id": settings.user_id},
                {"$set": settings_dict},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des paramètres: {e}")
            return False
    
    async def update_settings(
        self,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> bool:
        """Met à jour les paramètres"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des paramètres: {e}")
            return False
    
    async def set_timezone(self, user_id: int, timezone: str) -> bool:
        """Configure le fuseau horaire"""
        return await self.update_settings(
            user_id,
            {"timezone": timezone}
        )
    
    async def set_language(self, user_id: int, language: str) -> bool:
        """Configure la langue"""
        return await self.update_settings(
            user_id,
            {"language": language}
        )
    
    async def toggle_notifications(self, user_id: int) -> Optional[bool]:
        """Active/désactive les notifications"""
        try:
            settings = await self.get_settings(user_id)
            if settings:
                new_status = not settings.notifications_enabled
                success = await self.update_settings(
                    user_id,
                    {"notifications_enabled": new_status}
                )
                return new_status if success else None
            return None
        except Exception as e:
            logger.error(f"Erreur lors du toggle des notifications: {e}")
            return None
    
    async def toggle_auto_delete(self, user_id: int) -> Optional[bool]:
        """Active/désactive la suppression automatique"""
        try:
            settings = await self.get_settings(user_id)
            if settings:
                new_status = not settings.auto_delete_enabled
                success = await self.update_settings(
                    user_id,
                    {"auto_delete_enabled": new_status}
                )
                return new_status if success else None
            return None
        except Exception as e:
            logger.error(f"Erreur lors du toggle de l'auto-delete: {e}")
            return None
    
    async def set_auto_delete_hours(
        self,
        user_id: int,
        hours: int
    ) -> bool:
        """Configure le délai de suppression automatique"""
        return await self.update_settings(
            user_id,
            {"auto_delete_hours": hours}
        )
    
    async def set_default_caption(
        self,
        user_id: int,
        caption: str
    ) -> bool:
        """Configure la légende par défaut"""
        return await self.update_settings(
            user_id,
            {"default_caption": caption}
        )
    
    async def toggle_watermark(self, user_id: int) -> Optional[bool]:
        """Active/désactive le watermark"""
        try:
            settings = await self.get_settings(user_id)
            if settings:
                new_status = not settings.watermark_enabled
                success = await self.update_settings(
                    user_id,
                    {"watermark_enabled": new_status}
                )
                return new_status if success else None
            return None
        except Exception as e:
            logger.error(f"Erreur lors du toggle du watermark: {e}")
            return None
    
    async def set_watermark_text(
        self,
        user_id: int,
        text: str
    ) -> bool:
        """Configure le texte du watermark"""
        return await self.update_settings(
            user_id,
            {"watermark_text": text}
        )
    
    async def toggle_forward_protection(
        self,
        user_id: int
    ) -> Optional[bool]:
        """Active/désactive la protection contre le transfert"""
        try:
            settings = await self.get_settings(user_id)
            if settings:
                new_status = not settings.forward_protection
                success = await self.update_settings(
                    user_id,
                    {"forward_protection": new_status}
                )
                return new_status if success else None
            return None
        except Exception as e:
            logger.error(f"Erreur lors du toggle de la protection: {e}")
            return None
    
    async def reset_settings(self, user_id: int) -> bool:
        """Réinitialise les paramètres aux valeurs par défaut"""
        try:
            default_settings = Settings(user_id=user_id)
            return await self.save_settings(default_settings)
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            return False
