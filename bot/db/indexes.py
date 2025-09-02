"""
Création des index MongoDB
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from logger import setup_logger

logger = setup_logger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase):
    """Crée tous les index nécessaires"""
    try:
        # Index pour les utilisateurs
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("username")
        await db.users.create_index("created_at")
        await db.users.create_index("is_banned")
        
        # Index pour les canaux
        await db.channels.create_index("channel_id", unique=True)
        await db.channels.create_index("user_id")
        await db.channels.create_index([("user_id", ASCENDING), ("channel_id", ASCENDING)])
        await db.channels.create_index("is_active")
        
        # Index pour les posts
        await db.posts.create_index("post_id")
        await db.posts.create_index("user_id")
        await db.posts.create_index("channel_id")
        await db.posts.create_index("created_at")
        await db.posts.create_index("scheduled_at")
        await db.posts.create_index("status")
        await db.posts.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
        await db.posts.create_index([("channel_id", ASCENDING), ("scheduled_at", ASCENDING)])
        
        # Index texte pour la recherche dans les posts
        await db.posts.create_index([("caption", TEXT)])
        
        # Index pour les planifications
        await db.schedules.create_index("job_id", unique=True)
        await db.schedules.create_index("user_id")
        await db.schedules.create_index("post_id")
        await db.schedules.create_index("scheduled_time")
        await db.schedules.create_index("status")
        await db.schedules.create_index([("status", ASCENDING), ("scheduled_time", ASCENDING)])
        
        # Index pour les fichiers
        await db.files.create_index("file_id", unique=True)
        await db.files.create_index("user_id")
        await db.files.create_index("file_type")
        await db.files.create_index("created_at")
        await db.files.create_index([("user_id", ASCENDING), ("file_type", ASCENDING)])
        
        # Index pour les paramètres
        await db.settings.create_index("user_id", unique=True)
        await db.settings.create_index("updated_at")
        
        # Index TTL pour auto-suppression des vieux posts
        await db.posts.create_index(
            "expire_at",
            expireAfterSeconds=0,
            partialFilterExpression={"expire_at": {"$exists": True}}
        )
        
        # Index TTL pour les fichiers temporaires
        await db.files.create_index(
            "expire_at",
            expireAfterSeconds=0,
            partialFilterExpression={"expire_at": {"$exists": True}}
        )
        
        logger.info("✅ Tous les index ont été créés avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des index: {e}")
        raise


async def ensure_indexes(db: AsyncIOMotorDatabase):
    """Alias pour create_indexes - assure que les index existent"""
    await create_indexes(db)
