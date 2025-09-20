import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pyrogram import Client, filters
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneNumberInvalid,
    FloodWait,
    AuthKeyUnregistered,
    ConnectionError as PyrogramConnectionError
)

from userbot_config import userbot_config
from utils import get_db_connection

logger = logging.getLogger(__name__)

class UserbotManager:
    """Main userbot client manager for Telegram integration"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected: bool = False
        self.is_authenticated: bool = False
        self.connection_retries: int = 0
        self.last_connection_attempt: Optional[datetime] = None
        self.secret_chats: Dict[int, int] = {}  # user_id -> secret_chat_id
        self.active_deliveries: Dict[int, Dict] = {}  # user_id -> delivery_data
        
    async def initialize(self) -> bool:
        """Initialize the userbot client"""
        if not userbot_config.is_configured():
            logger.warning("⚠️ USERBOT: Not configured - skipping initialization")
            return False
        
        try:
            logger.info("🚀 USERBOT: Initializing client...")
            
            # Create Pyrogram client
            self.client = Client(
                name=userbot_config.session_name,
                api_id=userbot_config.api_id,
                api_hash=userbot_config.api_hash,
                phone_number=userbot_config.phone_number,
                workdir="."
            )
            
            # Set up event handlers
            self._setup_handlers()
            
            # Attempt connection
            success = await self._connect()
            if success:
                logger.info("✅ USERBOT: Successfully initialized and connected")
                return True
            else:
                logger.error("❌ USERBOT: Failed to initialize")
                return False
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Initialization error: {e}")
            return False
    
    def _setup_handlers(self):
        """Set up Pyrogram event handlers"""
        if not self.client:
            return
        
        @self.client.on_message(filters.private & filters.text)
        async def handle_private_message(client, message):
            """Handle incoming private messages for product delivery"""
            try:
                await self._process_delivery_message(message)
            except Exception as e:
                logger.error(f"❌ USERBOT: Error processing message: {e}")
        
        @self.client.on_message(filters.private & filters.photo)
        async def handle_photo_message(client, message):
            """Handle incoming photo messages"""
            try:
                await self._process_delivery_message(message)
            except Exception as e:
                logger.error(f"❌ USERBOT: Error processing photo: {e}")
    
    async def _connect(self) -> bool:
        """Establish connection to Telegram"""
        if not self.client:
            return False
        
        try:
            self.last_connection_attempt = datetime.now(timezone.utc)
            
            # Start the client
            await self.client.start()
            
            # Verify connection
            me = await self.client.get_me()
            if me:
                self.is_connected = True
                self.is_authenticated = True
                self.connection_retries = 0
                logger.info(f"✅ USERBOT: Connected as @{me.username or me.first_name}")
                return True
            else:
                logger.error("❌ USERBOT: Failed to get user info after connection")
                return False
                
        except SessionPasswordNeeded:
            logger.error("❌ USERBOT: Two-factor authentication required - please set up 2FA")
            return False
        except PhoneCodeInvalid:
            logger.error("❌ USERBOT: Invalid phone code")
            return False
        except PhoneNumberInvalid:
            logger.error("❌ USERBOT: Invalid phone number")
            return False
        except FloodWait as e:
            logger.warning(f"⏳ USERBOT: Rate limited - waiting {e.value} seconds")
            await asyncio.sleep(e.value)
            return await self._connect()
        except AuthKeyUnregistered:
            logger.error("❌ USERBOT: Session expired - please re-authenticate")
            return False
        except PyrogramConnectionError as e:
            logger.error(f"❌ USERBOT: Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ USERBOT: Unexpected connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect the userbot client"""
        if self.client and self.is_connected:
            try:
                await self.client.stop()
                self.is_connected = False
                self.is_authenticated = False
                logger.info("🔌 USERBOT: Disconnected")
            except Exception as e:
                logger.error(f"❌ USERBOT: Error during disconnect: {e}")
    
    async def ensure_connected(self) -> bool:
        """Ensure userbot is connected, attempt reconnection if needed"""
        if self.is_connected and self.is_authenticated:
            return True
        
        if not userbot_config.auto_reconnect:
            return False
        
        # Check retry limits
        if self.connection_retries >= userbot_config.max_retries:
            logger.error(f"❌ USERBOT: Max retries ({userbot_config.max_retries}) exceeded")
            return False
        
        # Check retry delay
        if self.last_connection_attempt:
            time_since_last = (datetime.now(timezone.utc) - self.last_connection_attempt).total_seconds()
            if time_since_last < userbot_config.retry_delay:
                return False
        
        logger.info(f"🔄 USERBOT: Attempting reconnection (attempt {self.connection_retries + 1})")
        self.connection_retries += 1
        
        success = await self._connect()
        if success:
            logger.info("✅ USERBOT: Reconnection successful")
        else:
            logger.warning(f"⚠️ USERBOT: Reconnection failed (attempt {self.connection_retries})")
        
        return success
    
    async def create_secret_chat(self, user_id: int) -> Optional[int]:
        """Create a secret chat with the specified user"""
        if not await self.ensure_connected():
            logger.error("❌ USERBOT: Cannot create secret chat - not connected")
            return None
        
        try:
            # Get user info from database
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT telegram_username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                logger.error(f"❌ USERBOT: No username found for user {user_id}")
                return None
            
            username = user_data[0]
            if not username.startswith('@'):
                username = f"@{username}"
            
            # Resolve username to user ID
            try:
                user_entity = await self.client.get_users(username)
                if not user_entity:
                    logger.error(f"❌ USERBOT: User {username} not found")
                    return None
            except Exception as e:
                logger.error(f"❌ USERBOT: Error resolving user {username}: {e}")
                return None
            
            # Create secret chat
            secret_chat = await self.client.create_secret_chat(user_entity.id)
            if secret_chat:
                secret_chat_id = secret_chat.id
                self.secret_chats[user_id] = secret_chat_id
                
                # Store in database
                await self._store_secret_chat(user_id, secret_chat_id)
                
                logger.info(f"✅ USERBOT: Secret chat created for user {user_id} (chat_id: {secret_chat_id})")
                return secret_chat_id
            else:
                logger.error(f"❌ USERBOT: Failed to create secret chat for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Error creating secret chat for user {user_id}: {e}")
            return None
    
    async def _store_secret_chat(self, user_id: int, secret_chat_id: int):
        """Store secret chat information in database"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO userbot_secret_chats 
                (user_id, secret_chat_id, created_at, status) 
                VALUES (?, ?, ?, ?)
            """, (user_id, secret_chat_id, datetime.now(timezone.utc).isoformat(), 'active'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ USERBOT: Error storing secret chat: {e}")
    
    async def _process_delivery_message(self, message):
        """Process incoming messages for product delivery"""
        try:
            # Check if this is a secret chat
            if not message.chat.is_secret_chat:
                return
            
            # Find user by secret chat ID
            user_id = None
            for uid, chat_id in self.secret_chats.items():
                if chat_id == message.chat.id:
                    user_id = uid
                    break
            
            if not user_id:
                logger.warning(f"⚠️ USERBOT: Unknown secret chat ID: {message.chat.id}")
                return
            
            # Check if user has pending delivery
            if user_id not in self.active_deliveries:
                return
            
            # Check for delivery keywords
            if message.text:
                message_text = message.text.lower().strip()
                if any(keyword in message_text for keyword in userbot_config.delivery_keywords):
                    logger.info(f"🎯 USERBOT: Delivery keyword detected from user {user_id}")
                    await self._trigger_delivery(user_id)
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error processing delivery message: {e}")
    
    async def _trigger_delivery(self, user_id: int):
        """Trigger product delivery for user"""
        try:
            delivery_data = self.active_deliveries.get(user_id)
            if not delivery_data:
                logger.warning(f"⚠️ USERBOT: No delivery data for user {user_id}")
                return
            
            # Import here to avoid circular imports
            from product_delivery import ProductDeliveryHandler
            delivery_handler = ProductDeliveryHandler(self.client)
            
            success = await delivery_handler.deliver_product(user_id, delivery_data)
            if success:
                # Remove from active deliveries
                del self.active_deliveries[user_id]
                logger.info(f"✅ USERBOT: Product delivered to user {user_id}")
            else:
                logger.error(f"❌ USERBOT: Failed to deliver product to user {user_id}")
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Error triggering delivery: {e}")
    
    async def schedule_delivery(self, user_id: int, product_data: Dict[str, Any]):
        """Schedule product delivery for a user"""
        try:
            # Create secret chat if not exists
            if user_id not in self.secret_chats:
                secret_chat_id = await self.create_secret_chat(user_id)
                if not secret_chat_id:
                    logger.error(f"❌ USERBOT: Cannot schedule delivery - no secret chat for user {user_id}")
                    return False
            
            # Store delivery data
            self.active_deliveries[user_id] = product_data
            
            # Send initial message
            await self._send_delivery_notification(user_id)
            
            logger.info(f"📦 USERBOT: Delivery scheduled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error scheduling delivery: {e}")
            return False
    
    async def _send_delivery_notification(self, user_id: int):
        """Send initial delivery notification to user"""
        try:
            secret_chat_id = self.secret_chats.get(user_id)
            if not secret_chat_id:
                return
            
            message = (
                "🔒 **SECRET DELIVERY**\n\n"
                "Your product is ready for delivery!\n"
                "Send any message to receive your product details.\n\n"
                "💡 **Tip**: Say 'hello' or 'product' to get started."
            )
            
            await self.client.send_message(secret_chat_id, message)
            logger.info(f"📨 USERBOT: Delivery notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error sending delivery notification: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current userbot status"""
        return {
            'connected': self.is_connected,
            'authenticated': self.is_authenticated,
            'retries': self.connection_retries,
            'max_retries': userbot_config.max_retries,
            'active_secret_chats': len(self.secret_chats),
            'pending_deliveries': len(self.active_deliveries),
            'last_connection_attempt': self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
        }

# Global userbot manager instance
userbot_manager = UserbotManager()
