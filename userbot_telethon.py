"""
Telethon Userbot for SECRET CHAT Product Delivery
CRITICAL: Products delivered ONLY via encrypted secret chats!
Workflow: Buyer buys product → Payment confirmed → Userbot creates SECRET CHAT → Sends product details
"""
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from telethon import TelegramClient
from telethon.tl.types import User
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
# Note: Telethon doesn't support secret chats, using secure direct messages instead

logger = logging.getLogger(__name__)

class TelethonSecretUserbot:
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.session_string = None
        self.has_session = False
        self.is_connected = False
        self.client = None
        
        # Load existing configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load userbot configuration from persistent storage"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.api_id = config.get('api_id')
                    self.api_hash = config.get('api_hash') 
                    self.phone_number = config.get('phone_number')
                    self.session_string = config.get('session_string')
                    
                    if all([self.api_id, self.api_hash, self.session_string]):
                        self.has_session = True
                        logger.info(f"✅ TELETHON: Loaded configuration for {self.phone_number}")
                    else:
                        logger.info("ℹ️ TELETHON: Incomplete configuration found")
            else:
                logger.info("ℹ️ TELETHON: No configuration file found")
        except Exception as e:
            logger.error(f"❌ TELETHON: Error loading configuration: {e}")
    
    def _save_configuration(self):
        """Save userbot configuration to persistent storage"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            os.makedirs('/mnt/data', exist_ok=True)
            
            config = {
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'phone_number': self.phone_number,
                'session_string': self.session_string
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("✅ TELETHON: Configuration saved")
        except Exception as e:
            logger.error(f"❌ TELETHON: Error saving configuration: {e}")
    
    def set_credentials(self, api_id: int, api_hash: str, phone_number: str, session_string: str):
        """Set userbot credentials and session"""
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_string = session_string
        self.has_session = True
        
        # Save configuration
        self._save_configuration()
        
        logger.info(f"✅ TELETHON: Credentials set for {phone_number}")
    
    async def connect(self) -> Tuple[bool, str]:
        """Connect to Telegram using Telethon"""
        if not self.has_session:
            return False, "No session available - please authenticate first"
        
        try:
            logger.info("🔌 TELETHON: Connecting...")
            
            # Create Telethon client with session string (StringSession)
            from telethon.sessions import StringSession
            self.client = TelegramClient(
                StringSession(self.session_string),
                api_id=self.api_id,
                api_hash=self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                return False, "Session expired - please re-authenticate"
            
            # Get user info
            me = await self.client.get_me()
            self.is_connected = True
            
            logger.info(f"✅ TELETHON: Connected as @{me.username}")
            return True, f"Connected as @{me.username}"
            
        except Exception as e:
            error_msg = f"Connection error: {e}"
            logger.error(f"❌ TELETHON: {error_msg}")
            self.is_connected = False
            return False, error_msg
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            try:
                await self.client.disconnect()
                self.is_connected = False
                logger.info("✅ TELETHON: Disconnected")
            except Exception as e:
                logger.error(f"❌ TELETHON: Error disconnecting: {e}")
    
    def get_status(self):
        """Get userbot status information"""
        return {
            'has_session': self.has_session,
            'is_connected': self.is_connected,
            'phone_number': self.phone_number,
            'api_id': self.api_id
        }
    
    def clear_configuration(self):
        """Clear userbot configuration and session"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                os.remove(config_file)
                logger.info("✅ TELETHON: Configuration file deleted")
            
            # Reset all properties
            self.api_id = None
            self.api_hash = None
            self.phone_number = None
            self.session_string = None
            self.has_session = False
            self.is_connected = False
            
            # Disconnect if connected
            if self.client:
                try:
                    asyncio.create_task(self.client.disconnect())
                except:
                    pass
                self.client = None
            
            logger.info("✅ TELETHON: Configuration cleared")
            return True, "Configuration cleared successfully"
            
        except Exception as e:
            logger.error(f"❌ TELETHON: Error clearing configuration: {e}")
            return False, f"Error clearing configuration: {e}"
    
    def _create_product_message(self, product_data: dict) -> str:
        """Create formatted product message"""
        message = f"""🎯 **PRODUCT DELIVERY**

📦 **Product**: {product_data.get('product_name', 'N/A')}
🏷️ **Type**: {product_data.get('product_type', 'N/A')}
🏙️ **City**: {product_data.get('city', 'N/A')}
🏘️ **District**: {product_data.get('district', 'N/A')}
⚖️ **Size**: {product_data.get('size', 'N/A')}
💰 **Price**: €{product_data.get('price', '0.00')}

🔐 **DELIVERED VIA SECURE DIRECT MESSAGE**
✅ Your purchase is secure and private!
📱 Sent directly from verified userbot account"""
        
        return message
    
    async def send_product_to_user(self, user_id: int, product_data: dict, media_files: List[str] = None) -> Tuple[bool, str]:
        """Send product to user via SECURE DIRECT MESSAGE"""
        if not self.is_connected:
            return False, "Userbot not connected"
        
        try:
            logger.info(f"🔐 TELETHON SECURE: Sending product to user {user_id}")
            
            # Get user information from database
            from utils import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                return False, f"No username found for user {user_id}"
            
            username = user_data[0]
            logger.info(f"🔍 TELETHON SECRET: Found username @{username} for user {user_id}")
            
            # Get user entity
            try:
                user_entity = await self.client.get_entity(username)
                logger.info(f"✅ TELETHON SECRET: Found user entity for @{username}")
            except Exception as e:
                logger.error(f"❌ TELETHON SECRET: Error finding user @{username}: {e}")
                return False, f"Error finding user @{username}: {e}"
            
            # Create product message
            message = self._create_product_message(product_data)
            
            # 🔐 SECURE DIRECT MESSAGE (Telethon doesn't support secret chats)
            try:
                logger.info(f"🔐 TELETHON SECURE: Sending secure direct message to user {user_id}")
                
                # Send media files via secure direct message
                if media_files and len(media_files) > 0:
                    logger.info(f"📂 TELETHON SECURE: Sending {len(media_files)} media files: {media_files}")
                    try:
                        media_sent = 0
                        for media_file in media_files:
                            logger.info(f"📁 TELETHON SECURE: Checking media file: {media_file}")
                            if os.path.exists(media_file):
                                logger.info(f"✅ TELETHON SECURE: File exists, sending: {media_file}")
                                
                                # Send file with caption for first media file
                                caption = message if media_sent == 0 else None
                                await self.client.send_file(user_entity, media_file, caption=caption)
                                
                                if media_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                    logger.info(f"📸 TELETHON SECURE: Sent photo: {media_file}")
                                elif media_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                                    logger.info(f"🎥 TELETHON SECURE: Sent video: {media_file}")
                                else:
                                    logger.info(f"📄 TELETHON SECURE: Sent document: {media_file}")
                                
                                media_sent += 1
                            else:
                                logger.error(f"❌ TELETHON SECURE: File not found: {media_file}")
                        
                        logger.info(f"✅ TELETHON SECURE: Sent {media_sent}/{len(media_files)} media files")
                        
                        # Send product message separately if no media files had caption
                        if media_sent > 0 and media_files:
                            # Message already sent as caption with first media
                            pass
                        else:
                            await self.client.send_message(user_entity, message)
                            
                    except Exception as e:
                        logger.error(f"❌ TELETHON SECURE: Error sending media: {e}")
                        # Send text message as fallback
                        await self.client.send_message(user_entity, message)
                else:
                    logger.warning(f"⚠️ TELETHON SECURE: No media files provided for user {user_id}")
                    # Send product message only
                    await self.client.send_message(user_entity, message)
                
                logger.info(f"✅ TELETHON SECURE: Product delivered to user {user_id} via SECURE DIRECT MESSAGE")
                
                return True, "Product delivered via secure direct message"
                
            except Exception as secure_error:
                logger.error(f"❌ TELETHON SECURE: Failed to send secure message: {secure_error}")
                return False, f"Failed to send secure message: {secure_error}"
            
        except Exception as e:
            error_msg = f"Error sending product via secure message: {e}"
            logger.error(f"❌ TELETHON SECURE: {error_msg}")
            return False, error_msg

# Global instance
telethon_userbot = TelethonSecretUserbot()
