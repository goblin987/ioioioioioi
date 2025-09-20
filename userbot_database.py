import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def init_userbot_tables():
    """Initialize userbot-related database tables"""
    try:
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
        conn = sqlite3.connect('bot_database.db')
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
