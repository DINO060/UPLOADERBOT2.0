"""
Modèle User
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class User:
    """Modèle pour un utilisateur"""
    
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = "en"
    is_premium: bool = False
    is_banned: bool = False
    ban_reason: Optional[str] = None
    banned_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    # Statistiques
    total_posts: int = 0
    total_channels: int = 0
    total_files: int = 0
    storage_used: int = 0  # en bytes
    
    # Permissions
    is_admin: bool = False
    is_owner: bool = False
    can_broadcast: bool = False
    
    # Limites
    max_channels: int = 10
    max_file_size: int = 2147483648  # 2GB
    max_posts_per_day: int = 100
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "is_premium": self.is_premium,
            "is_banned": self.is_banned,
            "ban_reason": self.ban_reason,
            "banned_at": self.banned_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_seen": self.last_seen,
            "total_posts": self.total_posts,
            "total_channels": self.total_channels,
            "total_files": self.total_files,
            "storage_used": self.storage_used,
            "is_admin": self.is_admin,
            "is_owner": self.is_owner,
            "can_broadcast": self.can_broadcast,
            "max_channels": self.max_channels,
            "max_file_size": self.max_file_size,
            "max_posts_per_day": self.max_posts_per_day,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Crée un objet depuis un dictionnaire"""
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            language_code=data.get("language_code", "en"),
            is_premium=data.get("is_premium", False),
            is_banned=data.get("is_banned", False),
            ban_reason=data.get("ban_reason"),
            banned_at=data.get("banned_at"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            last_seen=data.get("last_seen", datetime.utcnow()),
            total_posts=data.get("total_posts", 0),
            total_channels=data.get("total_channels", 0),
            total_files=data.get("total_files", 0),
            storage_used=data.get("storage_used", 0),
            is_admin=data.get("is_admin", False),
            is_owner=data.get("is_owner", False),
            can_broadcast=data.get("can_broadcast", False),
            max_channels=data.get("max_channels", 10),
            max_file_size=data.get("max_file_size", 2147483648),
            max_posts_per_day=data.get("max_posts_per_day", 100),
            metadata=data.get("metadata", {})
        )
    
    @property
    def full_name(self) -> str:
        """Retourne le nom complet de l'utilisateur"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or f"User {self.user_id}"
    
    @property
    def mention(self) -> str:
        """Retourne la mention HTML de l'utilisateur"""
        return f'<a href="tg://user?id={self.user_id}">{self.full_name}</a>'
    
    def can_create_channel(self) -> bool:
        """Vérifie si l'utilisateur peut créer un nouveau canal"""
        return not self.is_banned and self.total_channels < self.max_channels
    
    def can_upload_file(self, file_size: int) -> bool:
        """Vérifie si l'utilisateur peut uploader un fichier"""
        return not self.is_banned and file_size <= self.max_file_size
    
    def can_create_post(self) -> bool:
        """Vérifie si l'utilisateur peut créer un nouveau post"""
        return not self.is_banned  # Ajouter la logique de limite quotidienne si nécessaire
