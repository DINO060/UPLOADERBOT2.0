"""
Repository pour la gestion des planifications
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.schedule import Schedule
from logger import setup_logger

logger = setup_logger(__name__)


class SchedulesRepository:
    """Repository pour les planifications"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.schedules
    
    async def create_schedule(self, schedule: Schedule) -> str:
        """Crée une nouvelle planification"""
        try:
            schedule_dict = schedule.to_dict()
            result = await self.collection.insert_one(schedule_dict)
            logger.info(f"Planification créée: {schedule.job_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la planification: {e}")
            raise
    
    async def get_schedule(self, job_id: str) -> Optional[Schedule]:
        """Récupère une planification par son job_id"""
        try:
            schedule_data = await self.collection.find_one({"job_id": job_id})
            if schedule_data:
                return Schedule.from_dict(schedule_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la planification {job_id}: {e}")
            return None
    
    async def get_user_schedules(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> List[Schedule]:
        """Récupère les planifications d'un utilisateur"""
        try:
            filter_dict = {"user_id": user_id}
            if status:
                filter_dict["status"] = status
            
            cursor = self.collection.find(filter_dict)\
                .sort("scheduled_time", 1)
            
            schedules = []
            async for schedule_data in cursor:
                schedules.append(Schedule.from_dict(schedule_data))
            return schedules
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des planifications: {e}")
            return []
    
    async def get_pending_schedules(self) -> List[Schedule]:
        """Récupère toutes les planifications en attente"""
        try:
            filter_dict = {
                "status": "pending",
                "scheduled_time": {"$lte": datetime.utcnow()}
            }
            
            cursor = self.collection.find(filter_dict)
            schedules = []
            async for schedule_data in cursor:
                schedules.append(Schedule.from_dict(schedule_data))
            return schedules
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des planifications en attente: {e}")
            return []
    
    async def update_schedule(
        self,
        job_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Met à jour une planification"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la planification {job_id}: {e}")
            return False
    
    async def delete_schedule(self, job_id: str) -> bool:
        """Supprime une planification"""
        try:
            result = await self.collection.delete_one({"job_id": job_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la planification {job_id}: {e}")
            return False
    
    async def mark_as_executed(self, job_id: str) -> bool:
        """Marque une planification comme exécutée"""
        return await self.update_schedule(
            job_id,
            {
                "status": "executed",
                "executed_at": datetime.utcnow()
            }
        )
    
    async def mark_as_failed(
        self,
        job_id: str,
        error: str
    ) -> bool:
        """Marque une planification comme échouée"""
        return await self.update_schedule(
            job_id,
            {
                "status": "failed",
                "error": error,
                "failed_at": datetime.utcnow()
            }
        )
    
    async def cancel_schedule(self, job_id: str) -> bool:
        """Annule une planification"""
        return await self.update_schedule(
            job_id,
            {
                "status": "cancelled",
                "cancelled_at": datetime.utcnow()
            }
        )
    
    async def get_active_schedules(self) -> List[Schedule]:
        """Récupère toutes les planifications actives"""
        try:
            filter_dict = {
                "status": "pending",
                "scheduled_time": {"$gt": datetime.utcnow()}
            }
            
            cursor = self.collection.find(filter_dict)
            schedules = []
            async for schedule_data in cursor:
                schedules.append(Schedule.from_dict(schedule_data))
            return schedules
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des planifications actives: {e}")
            return []
    
    async def cleanup_old_schedules(self, days: int = 30) -> int:
        """Nettoie les vieilles planifications"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.collection.delete_many({
                "$or": [
                    {"status": "executed", "executed_at": {"$lt": cutoff_date}},
                    {"status": "failed", "failed_at": {"$lt": cutoff_date}},
                    {"status": "cancelled", "cancelled_at": {"$lt": cutoff_date}}
                ]
            })
            
            logger.info(f"Nettoyé {result.deleted_count} vieilles planifications")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des planifications: {e}")
            return 0
    
    async def reschedule(
        self,
        job_id: str,
        new_time: datetime
    ) -> bool:
        """Replanifie une tâche"""
        return await self.update_schedule(
            job_id,
            {
                "scheduled_time": new_time,
                "status": "pending",
                "rescheduled_at": datetime.utcnow()
            }
        )
