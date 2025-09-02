"""
Gestion des fuseaux horaires
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import pytz


def get_timezone_list() -> List[Tuple[str, str]]:
    """
    Retourne la liste des fuseaux horaires avec leurs offsets
    
    Returns:
        Liste de tuples (timezone, display_name)
    """
    timezones = []
    now = datetime.now()
    
    for tz_name in pytz.common_timezones:
        try:
            tz = pytz.timezone(tz_name)
            offset = tz.utcoffset(now)
            
            if offset:
                hours = int(offset.total_seconds() / 3600)
                minutes = int((offset.total_seconds() % 3600) / 60)
                offset_str = f"UTC{hours:+03d}:{minutes:02d}"
            else:
                offset_str = "UTC+00:00"
            
            display = f"{offset_str} - {tz_name.replace('_', ' ')}"
            timezones.append((tz_name, display))
        except:
            continue
    
    # Trier par offset
    timezones.sort(key=lambda x: x[1])
    return timezones


def get_user_time(
    utc_time: datetime,
    user_timezone: str = "UTC"
) -> datetime:
    """
    Convertit un temps UTC vers le fuseau de l'utilisateur
    
    Args:
        utc_time: Temps en UTC
        user_timezone: Fuseau horaire de l'utilisateur
    
    Returns:
        Temps dans le fuseau de l'utilisateur
    """
    try:
        if utc_time.tzinfo is None:
            utc_time = pytz.UTC.localize(utc_time)
        
        user_tz = pytz.timezone(user_timezone)
        return utc_time.astimezone(user_tz)
    except:
        return utc_time


def convert_to_utc(
    local_time: datetime,
    timezone: str
) -> datetime:
    """
    Convertit un temps local vers UTC
    
    Args:
        local_time: Temps local
        timezone: Fuseau horaire local
    
    Returns:
        Temps en UTC
    """
    try:
        tz = pytz.timezone(timezone)
        
        if local_time.tzinfo is None:
            local_time = tz.localize(local_time)
        
        return local_time.astimezone(pytz.UTC)
    except:
        return local_time


def format_datetime(
    dt: datetime,
    timezone: str = "UTC",
    format: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Formate une datetime pour l'affichage
    
    Args:
        dt: datetime à formater
        timezone: Fuseau horaire pour l'affichage
        format: Format de sortie
    
    Returns:
        Chaîne formatée
    """
    user_time = get_user_time(dt, timezone)
    return user_time.strftime(format)


def format_relative_time(dt: datetime) -> str:
    """
    Formate un temps relatif (il y a X minutes, dans X heures, etc.)
    
    Args:
        dt: datetime à formater
    
    Returns:
        Temps relatif formaté
    """
    now = datetime.utcnow()
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    
    diff = dt - now
    
    # Futur
    if diff.total_seconds() > 0:
        if diff.days > 0:
            if diff.days == 1:
                return "demain"
            return f"dans {diff.days} jours"
        
        hours = diff.seconds // 3600
        if hours > 0:
            if hours == 1:
                return "dans 1 heure"
            return f"dans {hours} heures"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            if minutes == 1:
                return "dans 1 minute"
            return f"dans {minutes} minutes"
        
        return "maintenant"
    
    # Passé
    diff = -diff
    if diff.days > 0:
        if diff.days == 1:
            return "hier"
        return f"il y a {diff.days} jours"
    
    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return "il y a 1 heure"
        return f"il y a {hours} heures"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return "il y a 1 minute"
        return f"il y a {minutes} minutes"
    
    return "à l'instant"


def get_timezone_offset(timezone: str) -> str:
    """
    Obtient l'offset UTC d'un fuseau horaire
    
    Args:
        timezone: Nom du fuseau horaire
    
    Returns:
        Offset sous forme de chaîne (ex: "+02:00")
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        offset = now.strftime('%z')
        return f"{offset[:3]}:{offset[3:]}"
    except:
        return "+00:00"


def guess_user_timezone(offset_minutes: int) -> str:
    """
    Devine le fuseau horaire basé sur l'offset en minutes
    
    Args:
        offset_minutes: Offset en minutes depuis UTC
    
    Returns:
        Nom du fuseau horaire probable
    """
    offset_hours = offset_minutes / 60
    
    # Mapper les offsets communs
    timezone_map = {
        -12: "Pacific/Kwajalein",
        -11: "Pacific/Midway",
        -10: "Pacific/Honolulu",
        -9: "America/Anchorage",
        -8: "America/Los_Angeles",
        -7: "America/Denver",
        -6: "America/Chicago",
        -5: "America/New_York",
        -4: "America/Caracas",
        -3: "America/Sao_Paulo",
        -2: "Atlantic/South_Georgia",
        -1: "Atlantic/Azores",
        0: "UTC",
        1: "Europe/Paris",
        2: "Europe/Helsinki",
        3: "Europe/Moscow",
        4: "Asia/Dubai",
        5: "Asia/Karachi",
        5.5: "Asia/Kolkata",
        6: "Asia/Dhaka",
        7: "Asia/Bangkok",
        8: "Asia/Shanghai",
        9: "Asia/Tokyo",
        10: "Australia/Sydney",
        11: "Pacific/Noumea",
        12: "Pacific/Auckland"
    }
    
    # Trouver le plus proche
    closest = min(timezone_map.keys(), key=lambda x: abs(x - offset_hours))
    return timezone_map[closest]


def is_business_hours(
    timezone: str = "UTC",
    start_hour: int = 9,
    end_hour: int = 18
) -> bool:
    """
    Vérifie si on est dans les heures de bureau
    
    Args:
        timezone: Fuseau horaire
        start_hour: Heure de début (défaut: 9)
        end_hour: Heure de fin (défaut: 18)
    
    Returns:
        True si dans les heures de bureau
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        current_hour = now.hour
        
        # Vérifier aussi le jour de la semaine (0=lundi, 6=dimanche)
        if now.weekday() in [5, 6]:  # Samedi ou dimanche
            return False
        
        return start_hour <= current_hour < end_hour
    except:
        return True  # Par défaut, on considère que c'est ok


def get_next_business_day(
    timezone: str = "UTC",
    hour: int = 9
) -> datetime:
    """
    Obtient le prochain jour ouvrable
    
    Args:
        timezone: Fuseau horaire
        hour: Heure du jour (défaut: 9h)
    
    Returns:
        datetime du prochain jour ouvrable
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        next_day = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Si c'est déjà passé aujourd'hui, aller au lendemain
        if next_day <= now:
            next_day += timedelta(days=1)
        
        # Trouver le prochain jour ouvrable
        while next_day.weekday() in [5, 6]:  # Samedi ou dimanche
            next_day += timedelta(days=1)
        
        return next_day.astimezone(pytz.UTC)
    except:
        return datetime.utcnow() + timedelta(days=1)
