"""
Modèle Schedule
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ScheduleStatus(str, Enum):
    """Statuts possibles d'une planification"""
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleType(str, Enum):
    """Types de planifications"""
    POST_PUBLISH = "post_publish"
    POST_DELETE = "post_delete"
    CHANNEL_CLEANUP = "channel_cleanup"
    BACKUP = "backup"
    BROADCAST = "broadcast"
    CUSTOM = "custom"


@dataclass
class Schedule:
    """Modèle pour une planification"""
    
    job_id: str
    user_id: int
    schedule_type: str  # ScheduleType
    scheduled_time: datetime
    
    # Référence à l'objet concerné
    post_id: Optional[str] = None
    channel_id: Optional[int] = None
    
    # Status
    status: str = ScheduleStatus.PENDING
    
    # Configuration de la tâche
    job_data: Dict[str, Any] = field(default_factory=dict)
    
    # Récurrence
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # cron expression
    recurrence_end_date: Optional[datetime] = None
    
    # Exécution
    executed_at: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Erreurs
    error: Optional[str] = None
    failed_at: Optional[datetime] = None
    
    # Annulation
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[int] = None
    cancellation_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "schedule_type": self.schedule_type,
            "scheduled_time": self.scheduled_time,
            "post_id": self.post_id,
            "channel_id": self.channel_id,
            "status": self.status,
            "job_data": self.job_data,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "recurrence_end_date": self.recurrence_end_date,
            "executed_at": self.executed_at,
            "next_run_time": self.next_run_time,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error,
            "failed_at": self.failed_at,
            "cancelled_at": self.cancelled_at,
            "cancelled_by": self.cancelled_by,
            "cancellation_reason": self.cancellation_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Crée un objet depuis un dictionnaire"""
        return cls(
            job_id=data["job_id"],
            user_id=data["user_id"],
            schedule_type=data.get("schedule_type", ScheduleType.CUSTOM),
            scheduled_time=data["scheduled_time"],
            post_id=data.get("post_id"),
            channel_id=data.get("channel_id"),
            status=data.get("status", ScheduleStatus.PENDING),
            job_data=data.get("job_data", {}),
            is_recurring=data.get("is_recurring", False),
            recurrence_pattern=data.get("recurrence_pattern"),
            recurrence_end_date=data.get("recurrence_end_date"),
            executed_at=data.get("executed_at"),
            next_run_time=data.get("next_run_time"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error=data.get("error"),
            failed_at=data.get("failed_at"),
            cancelled_at=data.get("cancelled_at"),
            cancelled_by=data.get("cancelled_by"),
            cancellation_reason=data.get("cancellation_reason"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            metadata=data.get("metadata", {})
        )
    
    @property
    def is_pending(self) -> bool:
        """Vérifie si la planification est en attente"""
        return self.status == ScheduleStatus.PENDING
    
    @property
    def is_executed(self) -> bool:
        """Vérifie si la planification a été exécutée"""
        return self.status == ScheduleStatus.EXECUTED
    
    @property
    def is_failed(self) -> bool:
        """Vérifie si la planification a échoué"""
        return self.status == ScheduleStatus.FAILED
    
    @property
    def is_cancelled(self) -> bool:
        """Vérifie si la planification a été annulée"""
        return self.status == ScheduleStatus.CANCELLED
    
    @property
    def is_overdue(self) -> bool:
        """Vérifie si la planification est en retard"""
        return (
            self.is_pending and 
            self.scheduled_time < datetime.utcnow()
        )
    
    def can_retry(self) -> bool:
        """Vérifie si la tâche peut être réessayée"""
        return self.retry_count < self.max_retries
    
    def can_cancel(self) -> bool:
        """Vérifie si la planification peut être annulée"""
        return self.status in [ScheduleStatus.PENDING, ScheduleStatus.FAILED]
    
    def get_next_retry_time(self) -> datetime:
        """Calcule le prochain moment de retry (backoff exponentiel)"""
        from datetime import timedelta
        delay_seconds = min(60 * (2 ** self.retry_count), 3600)  # Max 1 heure
        return datetime.utcnow() + timedelta(seconds=delay_seconds)
