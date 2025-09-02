"""
Modèle Settings
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class Settings:
    """Modèle pour les paramètres utilisateur"""
    
    user_id: int
    
    # Préférences générales
    language: str = "en"
    timezone: str = "UTC"
    theme: str = "light"
    
    # Notifications
    notifications_enabled: bool = True
    notify_on_publish: bool = True
    notify_on_schedule: bool = True
    notify_on_error: bool = True
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    
    # Publication
    default_parse_mode: str = "HTML"
    default_disable_notification: bool = False
    default_disable_web_preview: bool = True
    default_protect_content: bool = False
    default_caption: Optional[str] = None
    caption_position: str = "bottom"  # "top" ou "bottom"
    
    # Auto-delete
    auto_delete_enabled: bool = False
    auto_delete_hours: int = 24
    
    # Watermark
    watermark_enabled: bool = False
    watermark_text: Optional[str] = None
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.7
    
    # Protection
    forward_protection: bool = False
    copy_protection: bool = False
    screenshot_protection: bool = False
    
    # Planification
    default_schedule_delay: int = 5  # minutes
    allow_past_scheduling: bool = False
    max_schedule_days: int = 30
    
    # Limites personnalisées
    custom_max_channels: Optional[int] = None
    custom_max_file_size: Optional[int] = None
    custom_max_posts_per_day: Optional[int] = None
    
    # Canaux favoris
    favorite_channels: List[int] = field(default_factory=list)
    
    # Réactions par défaut
    default_reactions: List[str] = field(default_factory=list)
    
    # Boutons URL par défaut
    default_url_buttons: List[Dict[str, str]] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            "user_id": self.user_id,
            "language": self.language,
            "timezone": self.timezone,
            "theme": self.theme,
            "notifications_enabled": self.notifications_enabled,
            "notify_on_publish": self.notify_on_publish,
            "notify_on_schedule": self.notify_on_schedule,
            "notify_on_error": self.notify_on_error,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "default_parse_mode": self.default_parse_mode,
            "default_disable_notification": self.default_disable_notification,
            "default_disable_web_preview": self.default_disable_web_preview,
            "default_protect_content": self.default_protect_content,
            "default_caption": self.default_caption,
            "caption_position": self.caption_position,
            "auto_delete_enabled": self.auto_delete_enabled,
            "auto_delete_hours": self.auto_delete_hours,
            "watermark_enabled": self.watermark_enabled,
            "watermark_text": self.watermark_text,
            "watermark_position": self.watermark_position,
            "watermark_opacity": self.watermark_opacity,
            "forward_protection": self.forward_protection,
            "copy_protection": self.copy_protection,
            "screenshot_protection": self.screenshot_protection,
            "default_schedule_delay": self.default_schedule_delay,
            "allow_past_scheduling": self.allow_past_scheduling,
            "max_schedule_days": self.max_schedule_days,
            "custom_max_channels": self.custom_max_channels,
            "custom_max_file_size": self.custom_max_file_size,
            "custom_max_posts_per_day": self.custom_max_posts_per_day,
            "favorite_channels": self.favorite_channels,
            "default_reactions": self.default_reactions,
            "default_url_buttons": self.default_url_buttons,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Crée un objet depuis un dictionnaire"""
        return cls(
            user_id=data["user_id"],
            language=data.get("language", "en"),
            timezone=data.get("timezone", "UTC"),
            theme=data.get("theme", "light"),
            notifications_enabled=data.get("notifications_enabled", True),
            notify_on_publish=data.get("notify_on_publish", True),
            notify_on_schedule=data.get("notify_on_schedule", True),
            notify_on_error=data.get("notify_on_error", True),
            quiet_hours_start=data.get("quiet_hours_start"),
            quiet_hours_end=data.get("quiet_hours_end"),
            default_parse_mode=data.get("default_parse_mode", "HTML"),
            default_disable_notification=data.get("default_disable_notification", False),
            default_disable_web_preview=data.get("default_disable_web_preview", True),
            default_protect_content=data.get("default_protect_content", False),
            default_caption=data.get("default_caption"),
            caption_position=data.get("caption_position", "bottom"),
            auto_delete_enabled=data.get("auto_delete_enabled", False),
            auto_delete_hours=data.get("auto_delete_hours", 24),
            watermark_enabled=data.get("watermark_enabled", False),
            watermark_text=data.get("watermark_text"),
            watermark_position=data.get("watermark_position", "bottom-right"),
            watermark_opacity=data.get("watermark_opacity", 0.7),
            forward_protection=data.get("forward_protection", False),
            copy_protection=data.get("copy_protection", False),
            screenshot_protection=data.get("screenshot_protection", False),
            default_schedule_delay=data.get("default_schedule_delay", 5),
            allow_past_scheduling=data.get("allow_past_scheduling", False),
            max_schedule_days=data.get("max_schedule_days", 30),
            custom_max_channels=data.get("custom_max_channels"),
            custom_max_file_size=data.get("custom_max_file_size"),
            custom_max_posts_per_day=data.get("custom_max_posts_per_day"),
            favorite_channels=data.get("favorite_channels", []),
            default_reactions=data.get("default_reactions", []),
            default_url_buttons=data.get("default_url_buttons", []),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            metadata=data.get("metadata", {})
        )
    
    def is_in_quiet_hours(self) -> bool:
        """Vérifie si on est dans les heures silencieuses"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from datetime import datetime
        import pytz
        
        try:
            tz = pytz.timezone(self.timezone)
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            
            # Gestion du cas où les heures traversent minuit
            if self.quiet_hours_start <= self.quiet_hours_end:
                return self.quiet_hours_start <= current_time <= self.quiet_hours_end
            else:
                return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        except:
            return False
    
    def should_notify(self, notification_type: str) -> bool:
        """Détermine si une notification doit être envoyée"""
        if not self.notifications_enabled:
            return False
        
        if self.is_in_quiet_hours():
            return False
        
        if notification_type == "publish":
            return self.notify_on_publish
        elif notification_type == "schedule":
            return self.notify_on_schedule
        elif notification_type == "error":
            return self.notify_on_error
        
        return True
