"""
Client Python-Telegram-Bot (PTB)
"""

from typing import Optional
from telegram.ext import Application, ApplicationBuilder, Defaults
from telegram import Update
from telegram.constants import ParseMode

from ..config import Config
from ..logger import setup_logger

logger = setup_logger(__name__)


class PTBClient:
    """Wrapper pour l'application PTB"""
    
    def __init__(self, config: Config):
        self.config = config
        self.app: Optional[Application] = None
        
    def build(self) -> Application:
        """Construit l'application PTB"""
        defaults = Defaults(
            parse_mode=ParseMode.HTML,
            disable_notification=False,
            disable_web_page_preview=True
        )
        
        builder = ApplicationBuilder()
        builder.token(self.config.BOT_TOKEN)
        builder.defaults(defaults)
        
        # Configuration du pool de connexions
        builder.concurrent_updates(True)
        builder.pool_timeout(30)
        builder.connect_timeout(30)
        builder.read_timeout(30)
        builder.write_timeout(30)
        
        # Rate limiting
        if self.config.RATE_LIMIT_MESSAGES > 0:
            builder.rate_limiter(self._create_rate_limiter())
        
        self.app = builder.build()
        
        # Ajout des middlewares personnalisés
        self._setup_middlewares()
        
        logger.info("Application PTB construite avec succès")
        return self.app
    
    def _create_rate_limiter(self):
        """Crée un rate limiter personnalisé"""
        from telegram.ext import AIORateLimiter
        return AIORateLimiter(
            max_retries=3,
            overall_max_rate=self.config.RATE_LIMIT_MESSAGES,
            overall_time_period=self.config.RATE_LIMIT_WINDOW
        )
    
    def _setup_middlewares(self):
        """Configure les middlewares personnalisés"""
        if not self.app:
            return
        
        # Ajout du middleware de force subscribe si activé
        if self.config.ENABLE_FORCE_SUB:
            from ..utils.forcesub import ForceSubscribeMiddleware
            middleware = ForceSubscribeMiddleware(
                self.config.FORCE_SUB_CHANNEL
            )
            self.app.add_handler(middleware, group=-1)
    
    async def initialize(self):
        """Initialise l'application"""
        if self.app:
            await self.app.initialize()
            logger.info("Application PTB initialisée")
    
    async def start(self):
        """Démarre l'application"""
        if self.app:
            await self.app.start()
            logger.info("Application PTB démarrée")
    
    async def stop(self):
        """Arrête l'application"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            logger.info("Application PTB arrêtée")
    
    def get_bot(self):
        """Retourne l'instance du bot"""
        return self.app.bot if self.app else None
    
    def get_application(self) -> Application:
        """Retourne l'application PTB"""
        return self.app
