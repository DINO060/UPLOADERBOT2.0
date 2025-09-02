"""
Modèle Channel
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Channel:
    """Modèle pour un canal"""
    
    channel_id: int
    user_id: int
    username: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    member_count: int = 0
    is_active: bool = True
    is_verified: bool = False
    is_broadcast: bool = True
    is_private: bool = False
    
    # Permissions
    can_post_messages: bool = True
    can_edit_messages: bool = True
    can_delete_messages: bool = True
    
    # Statistiques
    total_posts: int = 0
    last_post_id: Optional[str] = None
    last_post_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Configuration
    auto_forward: bool = False
    forward_to: Optional[int] = None
    signature_enabled: bool = False
    signature_text: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "username": self.username,
            "title": self.title,
            "description": self.description,
            "member_count": self.member_count,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_broadcast": self.is_broadcast,
            "is_private": self.is_private,
            "can_post_messages": self.can_post_messages,
            "can_edit_messages": self.can_edit_messages,
            "can_delete_messages": self.can_delete_messages,
            "total_posts": self.total_posts,
            "last_post_id": self.last_post_id,
            "last_post_at": self.last_post_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "auto_forward": self.auto_forward,
            "forward_to": self.forward_to,
            "signature_enabled": self.signature_enabled,
            "signature_text": self.signature_text,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Channel":
        """Crée un objet depuis un dictionnaire"""
        return cls(
            channel_id=data["channel_id"],
            user_id=data["user_id"],
            username=data.get("username"),
            title=data.get("title"),
            description=data.get("description"),
            member_count=data.get("member_count", 0),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            is_broadcast=data.get("is_broadcast", True),
            is_private=data.get("is_private", False),
            can_post_messages=data.get("can_post_messages", True),
            can_edit_messages=data.get("can_edit_messages", True),
            can_delete_messages=data.get("can_delete_messages", True),
            total_posts=data.get("total_posts", 0),
            last_post_id=data.get("last_post_id"),
            last_post_at=data.get("last_post_at"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            auto_forward=data.get("auto_forward", False),
            forward_to=data.get("forward_to"),
            signature_enabled=data.get("signature_enabled", False),
            signature_text=data.get("signature_text"),
            metadata=data.get("metadata", {})
        )
    
    @property
    def display_name(self) -> str:
        """Retourne le nom d'affichage du canal"""
        if self.title:
            return self.title
        if self.username:
            return f"@{self.username}"
        return f"Channel {self.channel_id}"
    
    @property
    def link(self) -> Optional[str]:
        """Retourne le lien du canal si public"""
        if self.username:
            return f"https://t.me/{self.username}"
        if not self.is_private:
            return f"https://t.me/c/{str(self.channel_id)[4:]}"
        return None
    
    def can_post(self) -> bool:
        """Vérifie si on peut poster dans ce canal"""
        return self.is_active and self.can_post_messages
    
    def format_signature(self, text: str) -> str:
        """Ajoute la signature au texte si activée"""
        if self.signature_enabled and self.signature_text:
            return f"{text}\n\n{self.signature_text}"
        return text
