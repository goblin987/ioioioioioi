import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def init_userbot_tables():
    """Initialize userbot-related database tables"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Userbot secret chats table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_secret_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            secret_chat_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            last_activity TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, secret_chat_id)
        )''')
        
        # Userbot deliveries table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_type TEXT DEFAULT NULL,
            delivery_type TEXT DEFAULT 'default',
            delivered_at TEXT NOT NULL,
            status TEXT DEFAULT 'delivered',
            media_files TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )''')
        
        # Userbot session data table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT UNIQUE NOT NULL,
            phone_number TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT DEFAULT NULL,
            status TEXT DEFAULT 'active',
            connection_count INTEGER DEFAULT 0,
            last_error TEXT DEFAULT NULL
        )''')
        
        # Userbot delivery keywords table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_delivery_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL
        )''')
        
        # Insert default delivery keywords
        default_keywords = ['hello', 'hi', 'start', 'product', 'delivery', 'ready', 'get']
        for keyword in default_keywords:
            c.execute('''INSERT OR IGNORE INTO userbot_delivery_keywords (keyword, created_at) 
                        VALUES (?, ?)''', (keyword, datetime.now(timezone.utc).isoformat()))
        
        # Userbot settings table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # Userbot credentials table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id INTEGER UNIQUE NOT NULL,
            api_hash TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            session_name TEXT DEFAULT 'userbot_session',
            is_configured BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # Userbot authentication state table
        c.execute('''CREATE TABLE IF NOT EXISTS userbot_auth_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            auth_step TEXT NOT NULL,
            temp_data TEXT DEFAULT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )''')
        
        # Insert default settings
        default_settings = [
            ('enabled', 'false'),
            ('auto_reconnect', 'true'),
            ('max_retries', '3'),
            ('retry_delay', '5'),
            ('secret_chat_ttl', '86400'),
            ('delivery_notification', 'true'),
            ('media_delivery', 'true')
        ]
        
        for setting_name, setting_value in default_settings:
            c.execute('''INSERT OR IGNORE INTO userbot_settings (setting_name, setting_value, updated_at) 
                        VALUES (?, ?, ?)''', (setting_name, setting_value, datetime.now(timezone.utc).isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ USERBOT: Database tables initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error initializing database tables: {e}")
        return False

def get_userbot_setting(setting_name: str, default_value: str = None) -> str:
    """Get a userbot setting value"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT setting_value FROM userbot_settings WHERE setting_name = ?", (setting_name,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else default_value
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error getting setting {setting_name}: {e}")
        return default_value

def set_userbot_setting(setting_name: str, setting_value: str) -> bool:
    """Set a userbot setting value"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO userbot_settings (setting_name, setting_value, updated_at) 
                    VALUES (?, ?, ?)''', (setting_name, setting_value, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Setting {setting_name} updated to {setting_value}")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error setting {setting_name}: {e}")
        return False

def get_delivery_keywords() -> list:
    """Get active delivery keywords"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT keyword FROM userbot_delivery_keywords WHERE is_active = 1")
        results = c.fetchall()
        conn.close()
        
        return [row[0] for row in results]
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error getting delivery keywords: {e}")
        return []

def add_delivery_keyword(keyword: str) -> bool:
    """Add a new delivery keyword"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO userbot_delivery_keywords (keyword, created_at) 
                    VALUES (?, ?)''', (keyword.lower().strip(), datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Added delivery keyword: {keyword}")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error adding keyword {keyword}: {e}")
        return False

def remove_delivery_keyword(keyword: str) -> bool:
    """Remove a delivery keyword"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("UPDATE userbot_delivery_keywords SET is_active = 0 WHERE keyword = ?", (keyword.lower().strip(),))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Removed delivery keyword: {keyword}")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error removing keyword {keyword}: {e}")
        return False

def log_userbot_activity(activity_type: str, user_id: int = None, details: str = None) -> bool:
    """Log userbot activity"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO userbot_activity_log 
                    (activity_type, user_id, details, timestamp) 
                    VALUES (?, ?, ?, ?)''', (
            activity_type,
            user_id,
            details,
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error logging activity: {e}")
        return False

def get_userbot_stats() -> dict:
    """Get userbot statistics"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Get secret chat count
        c.execute("SELECT COUNT(*) FROM userbot_secret_chats WHERE status = 'active'")
        active_chats = c.fetchone()[0]
        
        # Get delivery count
        c.execute("SELECT COUNT(*) FROM userbot_deliveries WHERE status = 'delivered'")
        total_deliveries = c.fetchone()[0]
        
        # Get recent deliveries (last 24 hours)
        c.execute('''SELECT COUNT(*) FROM userbot_deliveries 
                    WHERE status = 'delivered' 
                    AND delivered_at > datetime('now', '-1 day')''')
        recent_deliveries = c.fetchone()[0]
        
        # Get session status
        c.execute("SELECT status FROM userbot_sessions ORDER BY last_used DESC LIMIT 1")
        session_result = c.fetchone()
        session_status = session_result[0] if session_result else 'unknown'
        
        conn.close()
        
        return {
            'active_secret_chats': active_chats,
            'total_deliveries': total_deliveries,
            'recent_deliveries': recent_deliveries,
            'session_status': session_status
        }
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error getting stats: {e}")
        return {}

def cleanup_old_deliveries(days: int = 30) -> bool:
    """Clean up old delivery records"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''DELETE FROM userbot_deliveries 
                    WHERE delivered_at < datetime('now', '-{} days')'''.format(days))
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Cleaned up {deleted_count} old delivery records")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error cleaning up deliveries: {e}")
        return False

def get_userbot_credentials() -> dict:
    """Get userbot credentials from database"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT api_id, api_hash, phone_number, session_name, is_configured FROM userbot_credentials ORDER BY updated_at DESC LIMIT 1")
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'api_id': result[0],
                'api_hash': result[1],
                'phone_number': result[2],
                'session_name': result[3],
                'is_configured': bool(result[4])
            }
        return {}
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error getting credentials: {e}")
        return {}

def set_userbot_credentials(api_id: int, api_hash: str, phone_number: str, session_name: str = 'userbot_session') -> bool:
    """Set userbot credentials in database"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO userbot_credentials 
                    (api_id, api_hash, phone_number, session_name, is_configured, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, 1, ?, ?)''', (
            api_id, api_hash, phone_number, session_name,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Credentials updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error setting credentials: {e}")
        return False

def clear_userbot_credentials() -> bool:
    """Clear userbot credentials from database"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM userbot_credentials")
        conn.commit()
        conn.close()
        
        logger.info(f"✅ USERBOT: Credentials cleared")
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error clearing credentials: {e}")
        return False

def set_userbot_auth_state(user_id: int, auth_step: str, temp_data: str = None, expires_minutes: int = 30) -> bool:
    """Set userbot authentication state"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Clear existing auth state for user
        c.execute("DELETE FROM userbot_auth_state WHERE user_id = ?", (user_id,))
        
        # Insert new auth state
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        c.execute('''INSERT INTO userbot_auth_state 
                    (user_id, auth_step, temp_data, created_at, expires_at) 
                    VALUES (?, ?, ?, ?, ?)''', (
            user_id, auth_step, temp_data,
            datetime.now(timezone.utc).isoformat(),
            expires_at.isoformat()
        ))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error setting auth state: {e}")
        return False

def get_userbot_auth_state(user_id: int) -> dict:
    """Get userbot authentication state"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''SELECT auth_step, temp_data, expires_at 
                    FROM userbot_auth_state 
                    WHERE user_id = ? AND expires_at > datetime('now')''', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'auth_step': result[0],
                'temp_data': result[1],
                'expires_at': result[2]
            }
        return {}
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error getting auth state: {e}")
        return {}

def clear_userbot_auth_state(user_id: int) -> bool:
    """Clear userbot authentication state"""
    try:
        from utils import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM userbot_auth_state WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ USERBOT: Error clearing auth state: {e}")
        return False
