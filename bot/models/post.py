"""
Modèle Post
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PostStatus(str, Enum):
    """Statuts possibles d'un post"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class PostType(str, Enum):
    """Types de posts"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ANIMATION = "animation"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    MEDIA_GROUP = "media_group"


@dataclass
class Post:
    """Modèle pour un post"""
    
    user_id: int
    channel_ids: List[int]
    content_type: str  # PostType
    
    # Contenu
    text: Optional[str] = None
    caption: Optional[str] = None
    file_id: Optional[str] = None
    file_ids: List[str] = field(default_factory=list)  # Pour media groups
    thumbnail_id: Optional[str] = None
    
    # Status et planning
    status: str = PostStatus.DRAFT
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    
    # Messages publiés (channel_id -> message_id)
    message_ids: Dict[int, int] = field(default_factory=dict)
    
    # Options de formatage
    parse_mode: str = "HTML"
    disable_notification: bool = False
    disable_web_page_preview: bool = True
    protect_content: bool = False
    
    # Boutons et réactions
    inline_buttons: List[List[Dict[str, str]]] = field(default_factory=list)
    reactions: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Statistiques
    views_count: int = 0
    forwards_count: int = 0
    reactions_count: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ID MongoDB (sera ajouté après insertion)
    _id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        data = {
            "user_id": self.user_id,
            "channel_ids": self.channel_ids,
            "content_type": self.content_type,
            "text": self.text,
            "caption": self.caption,
            "file_id": self.file_id,
            "file_ids": self.file_ids,
            "thumbnail_id": self.thumbnail_id,
            "status": self.status,
            "scheduled_at": self.scheduled_at,
            "published_at": self.published_at,
            "expire_at": self.expire_at,
            "message_ids": self.message_ids,
            "parse_mode": self.parse_mode,
            "disable_notification": self.disable_notification,
            "disable_web_page_preview": self.disable_web_page_preview,
            "protect_content": self.protect_content,
            "inline_buttons": self.inline_buttons,
            "reactions": self.reactions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "views_count": self.views_count,
            "forwards_count": self.forwards_count,
            "reactions_count": self.reactions_count,
            "metadata": self.metadata
        }
        
        if self._id:
            data["_id"] = self._id
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Post":
        """Crée un objet depuis un dictionnaire"""
        post = cls(
            user_id=data["user_id"],
            channel_ids=data.get("channel_ids", []),
            content_type=data.get("content_type", PostType.TEXT),
            text=data.get("text"),
            caption=data.get("caption"),
            file_id=data.get("file_id"),
            file_ids=data.get("file_ids", []),
            thumbnail_id=data.get("thumbnail_id"),
            status=data.get("status", PostStatus.DRAFT),
            scheduled_at=data.get("scheduled_at"),
            published_at=data.get("published_at"),
            expire_at=data.get("expire_at"),
            message_ids=data.get("message_ids", {}),
            parse_mode=data.get("parse_mode", "HTML"),
            disable_notification=data.get("disable_notification", False),
            disable_web_page_preview=data.get("disable_web_page_preview", True),
            protect_content=data.get("protect_content", False),
            inline_buttons=data.get("inline_buttons", []),
            reactions=data.get("reactions", []),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            views_count=data.get("views_count", 0),
            forwards_count=data.get("forwards_count", 0),
            reactions_count=data.get("reactions_count", 0),
            metadata=data.get("metadata", {})
        )
        
        # Ajouter l'ID MongoDB si présent
        if "_id" in data:
            post._id = str(data["_id"])
        
        return post
    
    @property
    def is_scheduled(self) -> bool:
        """Vérifie si le post est planifié"""
        return self.status == PostStatus.SCHEDULED and self.scheduled_at is not None
    
    @property
    def is_published(self) -> bool:
        """Vérifie si le post est publié"""
        return self.status == PostStatus.PUBLISHED
    
    @property
    def is_draft(self) -> bool:
        """Vérifie si le post est un brouillon"""
        return self.status == PostStatus.DRAFT
    
    @property
    def has_media(self) -> bool:
        """Vérifie si le post contient des médias"""
        return self.file_id is not None or len(self.file_ids) > 0
    
    @property
    def display_text(self) -> str:
        """Retourne le texte à afficher"""
        return self.caption or self.text or ""
    
    def can_be_scheduled(self) -> bool:
        """Vérifie si le post peut être planifié"""
        return self.status in [PostStatus.DRAFT, PostStatus.FAILED]
    
    def can_be_edited(self) -> bool:
        """Vérifie si le post peut être édité"""
        return self.status in [PostStatus.DRAFT, PostStatus.SCHEDULED]
    
    def can_be_deleted(self) -> bool:
        """Vérifie si le post peut être supprimé"""
        return self.status != PostStatus.PUBLISHING
