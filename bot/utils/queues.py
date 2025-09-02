"""
Gestion des files d'attente pour les opérations
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from collections import deque
from datetime import datetime
from enum import Enum

from ..logger import setup_logger

logger = setup_logger(__name__)


class QueuePriority(Enum):
    """Priorités pour les tâches"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Task:
    """Représente une tâche dans la file"""
    
    def __init__(
        self,
        task_id: str,
        user_id: int,
        task_type: str,
        data: Dict[str, Any],
        callback: Optional[Callable] = None,
        priority: QueuePriority = QueuePriority.NORMAL
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.task_type = task_type
        self.data = data
        self.callback = callback
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Any = None
        self.retries = 0
        self.max_retries = 3
    
    def __lt__(self, other):
        """Pour la comparaison dans la priority queue"""
        return self.priority.value > other.priority.value


class TaskQueue:
    """File d'attente pour les tâches"""
    
    def __init__(self, max_workers: int = 5, max_size: int = 1000):
        """
        Initialise la file d'attente
        
        Args:
            max_workers: Nombre maximum de workers
            max_size: Taille maximale de la file
        """
        self.max_workers = max_workers
        self.max_size = max_size
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_size)
        self.workers: List[asyncio.Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: deque = deque(maxlen=100)
        self.failed_tasks: deque = deque(maxlen=100)
        self.is_running = False
        self.task_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """
        Enregistre un handler pour un type de tâche
        
        Args:
            task_type: Type de tâche
            handler: Fonction de traitement
        """
        self.task_handlers[task_type] = handler
    
    async def add_task(self, task: Task) -> bool:
        """
        Ajoute une tâche à la file
        
        Args:
            task: Tâche à ajouter
        
        Returns:
            True si ajoutée avec succès
        """
        try:
            if self.queue.qsize() >= self.max_size:
                logger.warning(f"File pleine, tâche {task.task_id} rejetée")
                return False
            
            # Ajouter avec priorité inversée (plus grand = plus prioritaire)
            priority = -task.priority.value
            await self.queue.put((priority, task))
            logger.info(f"Tâche {task.task_id} ajoutée à la file")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche: {e}")
            return False
    
    async def start(self):
        """Démarre les workers"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Créer les workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"File d'attente démarrée avec {self.max_workers} workers")
    
    async def stop(self):
        """Arrête les workers"""
        self.is_running = False
        
        # Annuler tous les workers
        for worker in self.workers:
            worker.cancel()
        
        # Attendre la fin
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("File d'attente arrêtée")
    
    async def _worker(self, name: str):
        """Worker pour traiter les tâches"""
        logger.info(f"{name} démarré")
        
        while self.is_running:
            try:
                # Récupérer une tâche (avec timeout pour permettre l'arrêt)
                priority, task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                # Traiter la tâche
                await self._process_task(task)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{name} erreur: {e}")
        
        logger.info(f"{name} arrêté")
    
    async def _process_task(self, task: Task):
        """
        Traite une tâche
        
        Args:
            task: Tâche à traiter
        """
        task.started_at = datetime.utcnow()
        self.active_tasks[task.task_id] = task
        
        try:
            # Trouver le handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"Pas de handler pour le type {task.task_type}")
            
            # Exécuter le handler
            result = await handler(task)
            
            # Marquer comme complété
            task.completed_at = datetime.utcnow()
            task.result = result
            
            # Callback si fourni
            if task.callback:
                await task.callback(task)
            
            # Déplacer vers les tâches complétées
            self.completed_tasks.append(task)
            logger.info(f"Tâche {task.task_id} complétée avec succès")
            
        except Exception as e:
            task.error = str(e)
            task.retries += 1
            
            # Réessayer si possible
            if task.retries < task.max_retries:
                logger.warning(f"Tâche {task.task_id} échouée, réessai {task.retries}/{task.max_retries}")
                await asyncio.sleep(2 ** task.retries)  # Backoff exponentiel
                await self.add_task(task)
            else:
                # Trop d'échecs
                task.completed_at = datetime.utcnow()
                self.failed_tasks.append(task)
                logger.error(f"Tâche {task.task_id} définitivement échouée: {e}")
        
        finally:
            # Retirer des tâches actives
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtient le statut de la file
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            "is_running": self.is_running,
            "queue_size": self.queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "workers": len(self.workers)
        }
    
    def get_user_tasks(self, user_id: int) -> List[Task]:
        """
        Obtient les tâches d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Liste des tâches
        """
        tasks = []
        
        # Tâches actives
        for task in self.active_tasks.values():
            if task.user_id == user_id:
                tasks.append(task)
        
        return tasks


class ThumbnailQueue(TaskQueue):
    """File d'attente spécialisée pour les thumbnails"""
    
    def __init__(self):
        super().__init__(max_workers=3, max_size=100)
        self.register_handler("add_thumbnail", self._handle_thumbnail)
        self.register_handler("remove_thumbnail", self._handle_remove_thumbnail)
    
    async def _handle_thumbnail(self, task: Task) -> Any:
        """
        Traite l'ajout d'un thumbnail
        
        Args:
            task: Tâche de thumbnail
        
        Returns:
            Résultat du traitement
        """
        from ..utils.fileops import create_thumbnail
        
        image_path = task.data.get("image_path")
        output_path = task.data.get("output_path")
        size = task.data.get("size", (320, 320))
        
        success = await create_thumbnail(image_path, output_path, size)
        
        if not success:
            raise Exception("Échec de la création du thumbnail")
        
        return output_path
    
    async def _handle_remove_thumbnail(self, task: Task) -> Any:
        """
        Traite la suppression d'un thumbnail
        
        Args:
            task: Tâche de suppression
        
        Returns:
            Résultat
        """
        from ..utils.fileops import delete_file
        
        file_path = task.data.get("file_path")
        return delete_file(file_path)


class BroadcastQueue(TaskQueue):
    """File d'attente pour les broadcasts"""
    
    def __init__(self):
        super().__init__(max_workers=10, max_size=10000)
        self.register_handler("send_broadcast", self._handle_broadcast)
    
    async def _handle_broadcast(self, task: Task) -> Any:
        """
        Traite l'envoi d'un broadcast
        
        Args:
            task: Tâche de broadcast
        
        Returns:
            Résultat de l'envoi
        """
        # Implémentation spécifique au broadcast
        # À adapter selon les besoins
        pass


# Instances globales
thumbnail_queue = ThumbnailQueue()
broadcast_queue = BroadcastQueue()
