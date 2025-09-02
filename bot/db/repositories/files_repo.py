"""
Repository pour la gestion des fichiers
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.file import File
from logger import setup_logger

logger = setup_logger(__name__)


class FilesRepository:
    """Repository pour les fichiers"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.files
    
    async def save_file(self, file: File) -> str:
        """Enregistre un fichier"""
        try:
            file_dict = file.to_dict()
            result = await self.collection.insert_one(file_dict)
            logger.info(f"Fichier enregistré: {file.file_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du fichier: {e}")
            raise
    
    async def get_file(self, file_id: str) -> Optional[File]:
        """Récupère un fichier par son file_id"""
        try:
            file_data = await self.collection.find_one({"file_id": file_id})
            if file_data:
                return File.from_dict(file_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du fichier {file_id}: {e}")
            return None
    
    async def get_user_files(
        self,
        user_id: int,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[File]:
        """Récupère les fichiers d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if file_type:
                filter_dict["file_type"] = file_type
            
            cursor = self.collection.find(filter_dict)\
                .sort("created_at", -1)\
                .skip(skip)\
                .limit(limit)
            
            files = []
            async for file_data in cursor:
                files.append(File.from_dict(file_data))
            return files
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fichiers: {e}")
            return []
    
    async def update_file(
        self,
        file_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Met à jour un fichier"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"file_id": file_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du fichier {file_id}: {e}")
            return False
    
    async def delete_file(self, file_id: str) -> bool:
        """Supprime un fichier"""
        try:
            result = await self.collection.delete_one({"file_id": file_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du fichier {file_id}: {e}")
            return False
    
    async def upsert_file(self, file: File) -> bool:
        """Crée ou met à jour un fichier"""
        try:
            file_dict = file.to_dict()
            result = await self.collection.update_one(
                {"file_id": file.file_id},
                {"$set": file_dict},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Erreur lors de l'upsert du fichier {file.file_id}: {e}")
            return False
    
    async def get_thumbnail(self, user_id: int) -> Optional[File]:
        """Récupère la miniature d'un utilisateur"""
        try:
            file_data = await self.collection.find_one({
                "user_id": user_id,
                "file_type": "thumbnail"
            })
            if file_data:
                return File.from_dict(file_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la miniature: {e}")
            return None
    
    async def save_thumbnail(
        self,
        user_id: int,
        file_id: str,
        file_name: Optional[str] = None
    ) -> bool:
        """Enregistre une miniature"""
        file = File(
            file_id=file_id,
            user_id=user_id,
            file_type="thumbnail",
            file_name=file_name or "thumbnail.jpg",
            file_size=0,
            mime_type="image/jpeg"
        )
        return await self.upsert_file(file)
    
    async def set_expiry(
        self,
        file_id: str,
        hours: int
    ) -> bool:
        """Configure l'expiration automatique d'un fichier"""
        expire_at = datetime.utcnow() + timedelta(hours=hours)
        return await self.update_file(
            file_id,
            {"expire_at": expire_at}
        )
    
    async def count_user_files(
        self,
        user_id: int,
        file_type: Optional[str] = None
    ) -> int:
        """Compte le nombre de fichiers d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if file_type:
                filter_dict["file_type"] = file_type
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Erreur lors du comptage des fichiers: {e}")
            return 0
    
    async def get_total_size(self, user_id: int) -> int:
        """Calcule la taille totale des fichiers d'un utilisateur"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_size": {"$sum": "$file_size"}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            if result:
                return result[0].get("total_size", 0)
            return 0
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la taille totale: {e}")
            return 0
    
    async def cleanup_expired_files(self) -> int:
        """Nettoie les fichiers expirés (géré par TTL index)"""
        # Cette méthode est principalement pour le logging
        # MongoDB supprime automatiquement via TTL index
        try:
            count = await self.collection.count_documents({
                "expire_at": {"$lte": datetime.utcnow()}
            })
            if count > 0:
                logger.info(f"{count} fichiers expirés seront supprimés par MongoDB TTL")
            return count
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des fichiers expirés: {e}")
            return 0
