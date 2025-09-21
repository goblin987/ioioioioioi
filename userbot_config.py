import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class UserbotConfig:
    """Configuration management for Telegram userbot integration"""
    
    def __init__(self):
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.phone_number: Optional[str] = None
        self.session_name: str = "userbot_session"
        self.enabled: bool = False
        self.auto_reconnect: bool = True
        self.max_retries: int = 3
        self.retry_delay: int = 5
        self.secret_chat_ttl: int = 86400  # 24 hours
        self.delivery_keywords: list = ["hello", "hi", "start", "product", "delivery"]
        
        self._load_from_database()
    
    def _load_from_database(self):
        """Load configuration from database"""
        try:
            from userbot_database import get_userbot_credentials, get_userbot_setting
            
            # Load credentials from database
            credentials = get_userbot_credentials()
            if credentials:
                self.api_id = credentials.get('api_id')
                self.api_hash = credentials.get('api_hash')
                self.phone_number = credentials.get('phone_number')
                self.session_name = credentials.get('session_name', 'userbot_session')
                self.enabled = credentials.get('is_configured', False)
            else:
                # Fallback to environment variables if no database credentials
                self._load_from_env_fallback()
            
            # Load settings from database
            self.auto_reconnect = get_userbot_setting('auto_reconnect', 'true').lower() == 'true'
            self.max_retries = int(get_userbot_setting('max_retries', '3'))
            self.retry_delay = int(get_userbot_setting('retry_delay', '5'))
            self.secret_chat_ttl = int(get_userbot_setting('secret_chat_ttl', '86400'))
            
            # Delivery keywords
            keywords_str = get_userbot_setting('delivery_keywords', 'hello,hi,start,product,delivery')
            self.delivery_keywords = [kw.strip().lower() for kw in keywords_str.split(',')]
            
            # Validate required settings
            if self.enabled and not self._validate_credentials():
                logger.error("❌ USERBOT: Invalid credentials - disabling userbot")
                self.enabled = False
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Error loading configuration: {e}")
            self.enabled = False
    
    def _load_from_env_fallback(self):
        """Fallback to environment variables if no database credentials"""
        try:
            # Required userbot credentials
            self.api_id = int(os.getenv('USERBOT_API_ID', 0))
            self.api_hash = os.getenv('USERBOT_API_HASH', '')
            self.phone_number = os.getenv('USERBOT_PHONE_NUMBER', '')
            
            # Optional settings
            self.session_name = os.getenv('USERBOT_SESSION_NAME', 'userbot_session')
            self.enabled = os.getenv('USERBOT_ENABLED', 'false').lower() == 'true'
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error loading from environment fallback: {e}")
            self.enabled = False
    
    def _validate_credentials(self) -> bool:
        """Validate that required credentials are present"""
        if not self.api_id or self.api_id == 0:
            logger.error("❌ USERBOT: API ID not set or invalid")
            return False
        
        if not self.api_hash or len(self.api_hash) < 10:
            logger.error("❌ USERBOT: API Hash not set or too short")
            return False
        
        if not self.phone_number:
            logger.error("❌ USERBOT: Phone number not set")
            return False
        
        return True
    
    def is_configured(self) -> bool:
        """Check if userbot is properly configured"""
        return self.enabled and self._validate_credentials()
    
    def get_session_path(self) -> str:
        """Get the path for the session file"""
        return f"{self.session_name}.session"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)"""
        return {
            'enabled': self.enabled,
            'configured': self.is_configured(),
            'api_id_set': bool(self.api_id and self.api_id != 0),
            'api_hash_set': bool(self.api_hash and len(self.api_hash) >= 10),
            'phone_set': bool(self.phone_number),
            'session_name': self.session_name,
            'auto_reconnect': self.auto_reconnect,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'secret_chat_ttl': self.secret_chat_ttl,
            'delivery_keywords': self.delivery_keywords
        }
    
    def reload_from_database(self):
        """Reload configuration from database"""
        self._load_from_database()
    
    def log_config_status(self):
        """Log the current configuration status"""
        if self.enabled:
            if self.is_configured():
                logger.info("✅ USERBOT: Configuration loaded successfully")
                logger.info(f"📱 USERBOT: Session: {self.session_name}")
                logger.info(f"🔄 USERBOT: Auto-reconnect: {self.auto_reconnect}")
                logger.info(f"⏰ USERBOT: Secret chat TTL: {self.secret_chat_ttl}s")
                logger.info(f"🔑 USERBOT: Delivery keywords: {', '.join(self.delivery_keywords)}")
            else:
                logger.warning("⚠️ USERBOT: Configuration incomplete - check database credentials")
        else:
            logger.info("ℹ️ USERBOT: Disabled in configuration")

# Global configuration instance
userbot_config = UserbotConfig()
