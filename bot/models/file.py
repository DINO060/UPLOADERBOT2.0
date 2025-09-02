"""
Modèle File
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Types de fichiers"""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ANIMATION = "animation"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    STICKER = "sticker"
    THUMBNAIL = "thumbnail"
    OTHER = "other"


@dataclass
class File:
    """Modèle pour un fichier"""
    
    file_id: str
    user_id: int
    file_type: str  # FileType
    
    # Informations du fichier
    file_name: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    file_unique_id: Optional[str] = None
    
    # Métadonnées spécifiques au type
    width: Optional[int] = None  # Pour images/vidéos
    height: Optional[int] = None
    duration: Optional[int] = None  # Pour audio/vidéo (en secondes)
    thumbnail_file_id: Optional[str] = None
    
    # Informations de téléchargement
    file_path: Optional[str] = None  # Chemin local si téléchargé
    download_url: Optional[str] = None
    is_downloaded: bool = False
    downloaded_at: Optional[datetime] = None
    
    # Traitement
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    
    # Association
    post_id: Optional[str] = None
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    
    # Expiration
    expire_at: Optional[datetime] = None
    
    # Statistiques
    download_count: int = 0
    forward_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    # Métadonnées personnalisées
    custom_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            "file_id": self.file_id,
            "user_id": self.user_id,
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_unique_id": self.file_unique_id,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "thumbnail_file_id": self.thumbnail_file_id,
            "file_path": self.file_path,
            "download_url": self.download_url,
            "is_downloaded": self.is_downloaded,
            "downloaded_at": self.downloaded_at,
            "is_processed": self.is_processed,
            "processed_at": self.processed_at,
            "processing_error": self.processing_error,
            "post_id": self.post_id,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "expire_at": self.expire_at,
            "download_count": self.download_count,
            "forward_count": self.forward_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed": self.last_accessed,
            "custom_name": self.custom_name,
            "tags": self.tags,
            "description": self.description,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        """Crée un objet depuis un dictionnaire"""
        # Import List ici pour éviter l'erreur
        from typing import List
        
        return cls(
            file_id=data["file_id"],
            user_id=data["user_id"],
            file_type=data.get("file_type", FileType.OTHER),
            file_name=data.get("file_name"),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type"),
            file_unique_id=data.get("file_unique_id"),
            width=data.get("width"),
            height=data.get("height"),
            duration=data.get("duration"),
            thumbnail_file_id=data.get("thumbnail_file_id"),
            file_path=data.get("file_path"),
            download_url=data.get("download_url"),
            is_downloaded=data.get("is_downloaded", False),
            downloaded_at=data.get("downloaded_at"),
            is_processed=data.get("is_processed", False),
            processed_at=data.get("processed_at"),
            processing_error=data.get("processing_error"),
            post_id=data.get("post_id"),
            channel_id=data.get("channel_id"),
            message_id=data.get("message_id"),
            expire_at=data.get("expire_at"),
            download_count=data.get("download_count", 0),
            forward_count=data.get("forward_count", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            last_accessed=data.get("last_accessed", datetime.utcnow()),
            custom_name=data.get("custom_name"),
            tags=data.get("tags", []),
            description=data.get("description"),
            metadata=data.get("metadata", {})
        )
    
    @property
    def display_name(self) -> str:
        """Retourne le nom d'affichage du fichier"""
        return self.custom_name or self.file_name or f"file_{self.file_id[:8]}"
    
    @property
    def is_media(self) -> bool:
        """Vérifie si le fichier est un média"""
        return self.file_type in [
            FileType.PHOTO,
            FileType.VIDEO,
            FileType.AUDIO,
            FileType.ANIMATION,
            FileType.VOICE,
            FileType.VIDEO_NOTE
        ]
    
    @property
    def is_image(self) -> bool:
        """Vérifie si le fichier est une image"""
        return self.file_type == FileType.PHOTO
    
    @property
    def is_video(self) -> bool:
        """Vérifie si le fichier est une vidéo"""
        return self.file_type in [FileType.VIDEO, FileType.ANIMATION, FileType.VIDEO_NOTE]
    
    @property
    def is_audio(self) -> bool:
        """Vérifie si le fichier est un audio"""
        return self.file_type in [FileType.AUDIO, FileType.VOICE]
    
    @property
    def size_mb(self) -> float:
        """Retourne la taille en MB"""
        return self.file_size / (1024 * 1024)
    
    @property
    def size_formatted(self) -> str:
        """Retourne la taille formatée"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def can_expire(self) -> bool:
        """Vérifie si le fichier peut expirer"""
        return self.expire_at is not None
    
    def is_expired(self) -> bool:
        """Vérifie si le fichier est expiré"""
        return self.expire_at and self.expire_at < datetime.utcnow()
    
    def get_duration_formatted(self) -> str:
        """Retourne la durée formatée"""
        if not self.duration:
            return "00:00"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
