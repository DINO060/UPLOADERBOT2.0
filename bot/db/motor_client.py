"""
Client MongoDB avec Motor (async)
"""

from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import Config
from logger import setup_logger

logger = setup_logger(__name__)


class MongoClient:
    """Client MongoDB asynchrone"""
    
    def __init__(self, connection_string: str, db_name: str = "telegram_bot"):
        self.connection_string = connection_string
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self) -> bool:
        """Connecte à MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test de connexion
            await self.client.admin.command('ping')
            
            self.db = self.client[self.db_name]
            logger.info(f"✅ Connecté à MongoDB: {self.db_name}")
            
            # Créer les index
            from .indexes import create_indexes
            await create_indexes(self.db)
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Impossible de se connecter à MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion à MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Déconnecte de MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Déconnecté de MongoDB")
    
    def get_collection(self, name: str):
        """Retourne une collection"""
        if not self.db:
            raise RuntimeError("Base de données non connectée")
        return self.db[name]
    
    # Collections helpers
    @property
    def users(self):
        """Collection des utilisateurs"""
        return self.get_collection("users")
    
    @property
    def channels(self):
        """Collection des canaux"""
        return self.get_collection("channels")
    
    @property
    def posts(self):
        """Collection des posts"""
        return self.get_collection("posts")
    
    @property
    def schedules(self):
        """Collection des planifications"""
        return self.get_collection("schedules")
    
    @property
    def files(self):
        """Collection des fichiers"""
        return self.get_collection("files")
    
    @property
    def settings(self):
        """Collection des paramètres"""
        return self.get_collection("settings")
    
    # Méthodes utilitaires
    async def find_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Trouve un document"""
        coll = self.get_collection(collection)
        return await coll.find_one(filter, projection)
    
    async def find_many(
        self,
        collection: str,
        filter: Dict[str, Any] = {},
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Trouve plusieurs documents"""
        coll = self.get_collection(collection)
        cursor = coll.find(filter, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        
        return await cursor.to_list(length=None)
    
    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any]
    ):
        """Insère un document"""
        coll = self.get_collection(collection)
        result = await coll.insert_one(document)
        return result.inserted_id
    
    async def update_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ):
        """Met à jour un document"""
        coll = self.get_collection(collection)
        result = await coll.update_one(filter, update, upsert=upsert)
        return result.modified_count
    
    async def delete_one(
        self,
        collection: str,
        filter: Dict[str, Any]
    ):
        """Supprime un document"""
        coll = self.get_collection(collection)
        result = await coll.delete_one(filter)
        return result.deleted_count
    
    async def count_documents(
        self,
        collection: str,
        filter: Dict[str, Any] = {}
    ) -> int:
        """Compte les documents"""
        coll = self.get_collection(collection)
        return await coll.count_documents(filter)


# Instance globale du client MongoDB
_mongo_client: Optional[MongoClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def init_mongo(mongo_uri: str, db_name: str) -> AsyncIOMotorDatabase:
    """Initialise la connexion MongoDB"""
    global _mongo_client, _database
    
    try:
        _mongo_client = MongoClient(mongo_uri, db_name)
        connected = await _mongo_client.connect()
        
        if connected:
            _database = _mongo_client.db
            logger.info(f"✅ Base de données connectée: {db_name}")
            return _database
        else:
            logger.error("❌ Impossible d'initialiser MongoDB")
            raise RuntimeError("Connexion MongoDB échouée")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la connexion à MongoDB: {e}")
        # En mode test, on retourne None
        return None


async def get_database() -> AsyncIOMotorDatabase:
    """Récupère l'instance de la base de données"""
    if _database is None:
        raise RuntimeError("Base de données non initialisée. Appelez init_mongo() d'abord.")
    return _database


def get_client() -> MongoClient:
    """Récupère l'instance du client MongoDB"""
    if _mongo_client is None:
        raise RuntimeError("Client MongoDB non initialisé. Appelez init_mongo() d'abord.")
    return _mongo_client
