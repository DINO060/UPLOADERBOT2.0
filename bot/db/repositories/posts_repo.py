"""
Repository pour la gestion des posts
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.post import Post
from logger import setup_logger

logger = setup_logger(__name__)


class PostsRepository:
    """Repository pour les posts"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.posts
    
    async def create_post(self, post: Post) -> str:
        """Crée un nouveau post"""
        try:
            post_dict = post.to_dict()
            result = await self.collection.insert_one(post_dict)
            logger.info(f"Post créé: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur lors de la création du post: {e}")
            raise
    
    async def get_post(self, post_id: str) -> Optional[Post]:
        """Récupère un post par son ID"""
        try:
            from bson import ObjectId
            post_data = await self.collection.find_one({"_id": ObjectId(post_id)})
            if post_data:
                return Post.from_dict(post_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du post {post_id}: {e}")
            return None
    
    async def get_user_posts(
        self,
        user_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Post]:
        """Récupère les posts d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if status:
                filter_dict["status"] = status
            
            cursor = self.collection.find(filter_dict)\
                .sort("created_at", -1)\
                .skip(skip)\
                .limit(limit)
            
            posts = []
            async for post_data in cursor:
                posts.append(Post.from_dict(post_data))
            return posts
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des posts: {e}")
            return []
    
    async def update_post(
        self,
        post_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Met à jour un post"""
        try:
            from bson import ObjectId
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du post {post_id}: {e}")
            return False
    
    async def delete_post(self, post_id: str) -> bool:
        """Supprime un post"""
        try:
            from bson import ObjectId
            result = await self.collection.delete_one({"_id": ObjectId(post_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du post {post_id}: {e}")
            return False
    
    async def get_draft_posts(self, user_id: int) -> List[Post]:
        """Récupère les brouillons d'un utilisateur"""
        return await self.get_user_posts(user_id, status="draft")
    
    async def get_scheduled_posts(self, user_id: int) -> List[Post]:
        """Récupère les posts planifiés d'un utilisateur"""
        return await self.get_user_posts(user_id, status="scheduled")
    
    async def get_published_posts(self, user_id: int) -> List[Post]:
        """Récupère les posts publiés d'un utilisateur"""
        return await self.get_user_posts(user_id, status="published")
    
    async def get_pending_scheduled_posts(self) -> List[Post]:
        """Récupère tous les posts à publier"""
        try:
            filter_dict = {
                "status": "scheduled",
                "scheduled_at": {"$lte": datetime.utcnow()}
            }
            
            cursor = self.collection.find(filter_dict)
            posts = []
            async for post_data in cursor:
                posts.append(Post.from_dict(post_data))
            return posts
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des posts en attente: {e}")
            return []
    
    async def mark_as_published(
        self,
        post_id: str,
        message_ids: Dict[int, int]
    ) -> bool:
        """Marque un post comme publié"""
        return await self.update_post(
            post_id,
            {
                "status": "published",
                "published_at": datetime.utcnow(),
                "message_ids": message_ids
            }
        )
    
    async def set_auto_delete(
        self,
        post_id: str,
        hours: int
    ) -> bool:
        """Configure la suppression automatique d'un post"""
        expire_at = datetime.utcnow() + timedelta(hours=hours)
        return await self.update_post(
            post_id,
            {"expire_at": expire_at}
        )
    
    async def search_posts(
        self,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> List[Post]:
        """Recherche dans les posts d'un utilisateur"""
        try:
            filter_dict = {
                "user_id": user_id,
                "$text": {"$search": query}
            }
            
            cursor = self.collection.find(filter_dict)\
                .sort("score", {"$meta": "textScore"})\
                .limit(limit)
            
            posts = []
            async for post_data in cursor:
                posts.append(Post.from_dict(post_data))
            return posts
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de posts: {e}")
            return []
    
    async def count_posts(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Compte le nombre de posts"""
        try:
            filter_dict = {}
            if user_id:
                filter_dict["user_id"] = user_id
            if status:
                filter_dict["status"] = status
            
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Erreur lors du comptage des posts: {e}")
            return 0
    
    async def add_reaction(
        self,
        post_id: str,
        reaction: str
    ) -> bool:
        """Ajoute une réaction à un post"""
        try:
            from bson import ObjectId
            result = await self.collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"reactions": reaction}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la réaction: {e}")
            return False
