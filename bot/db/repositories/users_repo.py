"""
Repository pour la gestion des utilisateurs
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.user import User
from logger import setup_logger

logger = setup_logger(__name__)


class UsersRepository:
    """Repository pour les utilisateurs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users
        
    async def create_user(self, user: User) -> str:
        """Crée un nouvel utilisateur"""
        try:
            user_dict = user.to_dict()
            result = await self.collection.insert_one(user_dict)
            logger.info(f"Utilisateur créé: {user.user_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        try:
            user_data = await self.collection.find_one({"user_id": user_id})
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur {user_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Met à jour un utilisateur"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur {user_id}: {e}")
            return False
    
    async def upsert_user(self, user: User) -> bool:
        """Crée ou met à jour un utilisateur"""
        try:
            user_dict = user.to_dict()
            result = await self.collection.update_one(
                {"user_id": user.user_id},
                {"$set": user_dict},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Erreur lors de l'upsert de l'utilisateur {user.user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur"""
        try:
            result = await self.collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur {user_id}: {e}")
            return False
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """Récupère tous les utilisateurs avec pagination"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
            users = []
            async for user_data in cursor:
                users.append(User.from_dict(user_data))
            return users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []
    
    async def count_users(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Compte le nombre d'utilisateurs"""
        try:
            filter_dict = filter_dict or {}
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Erreur lors du comptage des utilisateurs: {e}")
            return 0
    
    async def ban_user(self, user_id: int, reason: Optional[str] = None) -> bool:
        """Bannit un utilisateur"""
        return await self.update_user(
            user_id,
            {
                "is_banned": True,
                "ban_reason": reason,
                "banned_at": datetime.utcnow()
            }
        )
    
    async def unban_user(self, user_id: int) -> bool:
        """Débannit un utilisateur"""
        return await self.update_user(
            user_id,
            {
                "is_banned": False,
                "ban_reason": None,
                "banned_at": None
            }
        )
    
    async def is_banned(self, user_id: int) -> bool:
        """Vérifie si un utilisateur est banni"""
        user = await self.get_user(user_id)
        return user.is_banned if user else False
    
    async def update_last_seen(self, user_id: int) -> bool:
        """Met à jour la dernière activité de l'utilisateur"""
        return await self.update_user(
            user_id,
            {"last_seen": datetime.utcnow()}
        )
    
    async def get_active_users(self, days: int = 7) -> List[User]:
        """Récupère les utilisateurs actifs dans les X derniers jours"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        filter_dict = {
            "last_seen": {"$gte": cutoff_date},
            "is_banned": False
        }
        
        return await self.get_all_users(filter_dict=filter_dict, limit=0)
