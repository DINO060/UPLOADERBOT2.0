"""
Module pour la suppression automatique planifiée
"""

from datetime import datetime, timedelta
from ..logger import setup_logger

logger = setup_logger(__name__)


class AutoDeleteManager:
    """Gère la suppression automatique des posts"""
    
    def __init__(self, scheduler, posts_repo):
        self.scheduler = scheduler
        self.posts_repo = posts_repo
    
    async def schedule_auto_delete(self, post_id: str, user_id: int, hours: int) -> bool:
        """Planifie la suppression automatique d'un post"""
        try:
            job_id = await self.scheduler.schedule_deletion(post_id, user_id, hours)
            
            if job_id:
                await self.posts_repo.set_auto_delete(post_id, hours)
                logger.info(f"Auto-delete planifié pour {post_id} dans {hours}h")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur auto-delete: {e}")
            return False
