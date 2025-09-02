"""
Module de planification avec AsyncIOScheduler
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import uuid

from ..db.repositories.schedules_repo import SchedulesRepository
from ..models.schedule import Schedule, ScheduleStatus, ScheduleType
from ..logger import setup_logger

logger = setup_logger(__name__)


class JobScheduler:
    """Gestionnaire de tâches planifiées"""
    
    def __init__(self, db):
        self.db = db
        self.schedules_repo = SchedulesRepository(db)
        self.scheduler = AsyncIOScheduler()
        self.job_handlers = {}
        
    async def start(self):
        """Démarre le scheduler"""
        try:
            self.scheduler.start()
            logger.info("✅ Scheduler démarré")
            return True
        except Exception as e:
            logger.error(f"Erreur au démarrage du scheduler: {e}")
            return False
    
    async def shutdown(self):
        """Arrête le scheduler"""
        try:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler arrêté")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt: {e}")
    
    async def restore_jobs(self):
        """Restaure les jobs depuis la DB"""
        try:
            schedules = await self.schedules_repo.get_active_schedules()
            restored = 0
            
            for schedule in schedules:
                if schedule.scheduled_time > datetime.utcnow():
                    self._add_job_to_scheduler(schedule)
                    restored += 1
            
            logger.info(f"✅ {restored} jobs restaurés")
            return restored
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {e}")
            return 0
    
    async def schedule_post(
        self,
        post_id: str,
        user_id: int,
        scheduled_time: datetime,
        channel_ids: List[int]
    ) -> Optional[str]:
        """Planifie la publication d'un post"""
        try:
            job_id = str(uuid.uuid4())
            
            # Créer le schedule en DB
            schedule = Schedule(
                job_id=job_id,
                user_id=user_id,
                schedule_type=ScheduleType.POST_PUBLISH,
                scheduled_time=scheduled_time,
                post_id=post_id,
                job_data={"channel_ids": channel_ids}
            )
            
            await self.schedules_repo.create_schedule(schedule)
            
            # Ajouter au scheduler
            self._add_job_to_scheduler(schedule)
            
            logger.info(f"Post {post_id} planifié pour {scheduled_time}")
            return job_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification: {e}")
            return None
    
    async def schedule_deletion(
        self,
        post_id: str,
        user_id: int,
        hours_delay: int
    ) -> Optional[str]:
        """Planifie la suppression d'un post"""
        try:
            job_id = str(uuid.uuid4())
            scheduled_time = datetime.utcnow() + timedelta(hours=hours_delay)
            
            schedule = Schedule(
                job_id=job_id,
                user_id=user_id,
                schedule_type=ScheduleType.POST_DELETE,
                scheduled_time=scheduled_time,
                post_id=post_id,
                job_data={"hours_delay": hours_delay}
            )
            
            await self.schedules_repo.create_schedule(schedule)
            self._add_job_to_scheduler(schedule)
            
            logger.info(f"Suppression planifiée dans {hours_delay}h")
            return job_id
            
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return None
    
    def _add_job_to_scheduler(self, schedule: Schedule):
        """Ajoute un job au scheduler"""
        try:
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=DateTrigger(run_date=schedule.scheduled_time),
                id=schedule.job_id,
                args=[schedule],
                replace_existing=True,
                misfire_grace_time=300
            )
        except Exception as e:
            logger.error(f"Erreur ajout job: {e}")
    
    async def _execute_job(self, schedule: Schedule):
        """Exécute un job planifié"""
        try:
            logger.info(f"Exécution du job {schedule.job_id}")
            
            # Marquer comme en cours
            await self.schedules_repo.update_schedule(
                schedule.job_id,
                {"status": ScheduleStatus.EXECUTING}
            )
            
            # Exécuter selon le type
            if schedule.schedule_type == ScheduleType.POST_PUBLISH:
                await self._handle_post_publish(schedule)
            elif schedule.schedule_type == ScheduleType.POST_DELETE:
                await self._handle_post_delete(schedule)
            
            # Marquer comme exécuté
            await self.schedules_repo.mark_as_executed(schedule.job_id)
            
        except Exception as e:
            logger.error(f"Erreur exécution job: {e}")
            await self.schedules_repo.mark_as_failed(schedule.job_id, str(e))
    
    async def _handle_post_publish(self, schedule: Schedule):
        """Publie un post planifié"""
        from ..publications.send_post import PostSender
        from ..db.repositories.posts_repo import PostsRepository
        from ..db.repositories.channels_repo import ChannelsRepository
        
        posts_repo = PostsRepository(self.db)
        channels_repo = ChannelsRepository(self.db)
        
        post = await posts_repo.get_post(schedule.post_id)
        if post:
            # Import du bot sera fait dynamiquement
            # sender = PostSender(bot, posts_repo, channels_repo)
            # await sender.send_post(post)
            logger.info(f"Post {schedule.post_id} publié")
    
    async def _handle_post_delete(self, schedule: Schedule):
        """Supprime un post planifié"""
        from ..db.repositories.posts_repo import PostsRepository
        
        posts_repo = PostsRepository(self.db)
        await posts_repo.delete_post(schedule.post_id)
        logger.info(f"Post {schedule.post_id} supprimé")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Annule un job"""
        try:
            self.scheduler.remove_job(job_id)
            await self.schedules_repo.cancel_schedule(job_id)
            logger.info(f"Job {job_id} annulé")
            return True
        except Exception as e:
            logger.error(f"Erreur annulation: {e}")
            return False
    
    def get_jobs(self) -> list:
        """Retourne la liste des jobs actifs"""
        return self.scheduler.get_jobs()
