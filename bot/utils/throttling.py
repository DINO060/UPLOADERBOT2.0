"""
Système de limitation de taux (rate limiting)
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .errors import RateLimitError
from .constants import Limits


class RateLimiter:
    """Limiteur de taux pour les utilisateurs"""
    
    def __init__(
        self,
        max_requests: int = Limits.RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = Limits.RATE_LIMIT_WINDOW
    ):
        """
        Initialise le rate limiter
        
        Args:
            max_requests: Nombre maximum de requêtes
            window_seconds: Fenêtre de temps en secondes
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        self.user_warnings: Dict[int, int] = defaultdict(int)
    
    def check_rate_limit(self, user_id: int) -> Tuple[bool, Optional[int]]:
        """
        Vérifie si un utilisateur a dépassé la limite
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Tuple (est_autorisé, temps_attente_si_refusé)
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Nettoyer les anciennes requêtes
        while user_queue and user_queue[0] < current_time - self.window_seconds:
            user_queue.popleft()
        
        # Vérifier la limite
        if len(user_queue) >= self.max_requests:
            # Calculer le temps d'attente
            oldest_request = user_queue[0]
            wait_time = int(oldest_request + self.window_seconds - current_time) + 1
            return False, wait_time
        
        # Ajouter la requête actuelle
        user_queue.append(current_time)
        return True, None
    
    def add_warning(self, user_id: int) -> int:
        """
        Ajoute un avertissement pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Nombre total d'avertissements
        """
        self.user_warnings[user_id] += 1
        return self.user_warnings[user_id]
    
    def reset_user(self, user_id: int):
        """
        Réinitialise les compteurs d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
        if user_id in self.user_warnings:
            del self.user_warnings[user_id]
    
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Obtient le nombre de requêtes restantes
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Nombre de requêtes restantes
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Nettoyer les anciennes requêtes
        while user_queue and user_queue[0] < current_time - self.window_seconds:
            user_queue.popleft()
        
        return max(0, self.max_requests - len(user_queue))


class MessageThrottler:
    """Throttler pour les messages vers les canaux"""
    
    def __init__(self, messages_per_second: float = 1.0):
        """
        Initialise le throttler
        
        Args:
            messages_per_second: Messages par seconde autorisés
        """
        self.messages_per_second = messages_per_second
        self.min_interval = 1.0 / messages_per_second
        self.last_message_time: Dict[int, float] = {}
    
    async def wait_if_needed(self, channel_id: int):
        """
        Attend si nécessaire avant d'envoyer un message
        
        Args:
            channel_id: ID du canal
        """
        import asyncio
        
        current_time = time.time()
        last_time = self.last_message_time.get(channel_id, 0)
        
        time_since_last = current_time - last_time
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_message_time[channel_id] = time.time()


class APIRateLimiter:
    """Rate limiter pour les appels API"""
    
    def __init__(self):
        """Initialise le rate limiter API"""
        self.limits = {
            "send_message": (30, 1),      # 30 messages par seconde
            "edit_message": (30, 1),      # 30 éditions par seconde
            "delete_message": (30, 1),    # 30 suppressions par seconde
            "send_media": (10, 1),        # 10 médias par seconde
            "send_media_group": (1, 1),   # 1 groupe par seconde
            "get_chat": (10, 1),          # 10 requêtes par seconde
            "get_file": (20, 60),         # 20 fichiers par minute
            "download_file": (5, 60),     # 5 téléchargements par minute
        }
        self.call_times: Dict[str, deque] = defaultdict(deque)
    
    async def check_and_wait(self, method: str):
        """
        Vérifie et attend si nécessaire pour un appel API
        
        Args:
            method: Nom de la méthode API
        """
        import asyncio
        
        if method not in self.limits:
            return  # Pas de limite pour cette méthode
        
        max_calls, window_seconds = self.limits[method]
        current_time = time.time()
        call_queue = self.call_times[method]
        
        # Nettoyer les anciens appels
        while call_queue and call_queue[0] < current_time - window_seconds:
            call_queue.popleft()
        
        # Si on a atteint la limite, attendre
        if len(call_queue) >= max_calls:
            oldest_call = call_queue[0]
            wait_time = oldest_call + window_seconds - current_time
            if wait_time > 0:
                await asyncio.sleep(wait_time + 0.1)  # Petite marge
        
        # Enregistrer cet appel
        call_queue.append(current_time)


class UserActionCooldown:
    """Cooldown pour les actions utilisateur"""
    
    def __init__(self):
        """Initialise le système de cooldown"""
        self.cooldowns = {
            "create_post": 5,        # 5 secondes
            "schedule_post": 10,     # 10 secondes
            "broadcast": 300,        # 5 minutes
            "backup": 3600,         # 1 heure
            "bulk_delete": 60,      # 1 minute
            "add_channel": 30,      # 30 secondes
            "change_settings": 5,   # 5 secondes
        }
        self.last_action: Dict[Tuple[int, str], float] = {}
    
    def is_on_cooldown(
        self,
        user_id: int,
        action: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Vérifie si une action est en cooldown
        
        Args:
            user_id: ID de l'utilisateur
            action: Type d'action
        
        Returns:
            Tuple (est_en_cooldown, temps_restant)
        """
        if action not in self.cooldowns:
            return False, None
        
        key = (user_id, action)
        current_time = time.time()
        
        if key in self.last_action:
            time_passed = current_time - self.last_action[key]
            cooldown_time = self.cooldowns[action]
            
            if time_passed < cooldown_time:
                remaining = int(cooldown_time - time_passed) + 1
                return True, remaining
        
        return False, None
    
    def set_cooldown(self, user_id: int, action: str):
        """
        Définit un cooldown pour une action
        
        Args:
            user_id: ID de l'utilisateur
            action: Type d'action
        """
        if action in self.cooldowns:
            self.last_action[(user_id, action)] = time.time()
    
    def reset_cooldown(self, user_id: int, action: Optional[str] = None):
        """
        Réinitialise les cooldowns
        
        Args:
            user_id: ID de l'utilisateur
            action: Action spécifique ou None pour toutes
        """
        if action:
            key = (user_id, action)
            if key in self.last_action:
                del self.last_action[key]
        else:
            # Supprimer tous les cooldowns de l'utilisateur
            keys_to_remove = [
                key for key in self.last_action
                if key[0] == user_id
            ]
            for key in keys_to_remove:
                del self.last_action[key]


# Instances globales
rate_limiter = RateLimiter()
message_throttler = MessageThrottler()
api_limiter = APIRateLimiter()
action_cooldown = UserActionCooldown()
