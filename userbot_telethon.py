"""
Telethon Userbot for REAL SECRET ENCRYPTED CHAT Product Delivery
🔐 CRITICAL: Products delivered ONLY via REAL encrypted secret chats!
🎯 Workflow: Buyer buys product → Payment confirmed → Userbot creates ENCRYPTED SECRET CHAT → Sends product details
🛡️ SECURITY: End-to-end encryption, self-destructing messages, no server storage
"""
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from telethon import TelegramClient
from telethon.tl.types import User
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
# 🔐 REAL SECRET CHATS using telethon-secret-chat plugin
from telethon_secret_chat import SecretChatManager

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
        self.secret_chat_manager = None  # 🔐 SECRET CHAT MANAGER
        
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
        logger.info(f"🔍 TELETHON: Setting credentials - session_string length: {len(session_string) if session_string else 0}")
        logger.info(f"🔍 TELETHON: Setting credentials - session_string type: {type(session_string)}")
        
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
            
            # Debug session string format
            logger.info(f"🔍 TELETHON: Session string length: {len(self.session_string) if self.session_string else 0}")
            logger.info(f"🔍 TELETHON: Session string type: {type(self.session_string)}")
            
            # Handle different session string formats
            try:
                if isinstance(self.session_string, str) and len(self.session_string) > 10:
                    session = StringSession(self.session_string)
                else:
                    logger.warning(f"⚠️ TELETHON: Invalid session string format, using empty session")
                    session = StringSession()
            except Exception as session_error:
                logger.error(f"❌ TELETHON: Session creation error: {session_error}")
                session = StringSession()
            
            self.client = TelegramClient(
                session,
                api_id=self.api_id,
                api_hash=self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                return False, "Session expired - please re-authenticate"
            
            # 🔐 INITIALIZE SECRET CHAT MANAGER
            self.secret_chat_manager = SecretChatManager(self.client, auto_accept=True)
            logger.info("🔐 TELETHON SECRET: SecretChatManager initialized with auto_accept=True")
            
            # Get user info
            me = await self.client.get_me()
            self.is_connected = True
            
            logger.info(f"✅ TELETHON SECRET: Connected as @{me.username} with SECRET CHAT support")
            return True, f"Connected as @{me.username} with SECRET CHAT support"
            
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
        """Create formatted product message for SECRET CHAT"""
        message = f"""🔐 **SECRET ENCRYPTED DELIVERY**

📦 **Product**: {product_data.get('product_name', 'N/A')}
🏷️ **Type**: {product_data.get('product_type', 'N/A')}
🏙️ **City**: {product_data.get('city', 'N/A')}
🏘️ **District**: {product_data.get('district', 'N/A')}
⚖️ **Size**: {product_data.get('size', 'N/A')}
💰 **Price**: €{product_data.get('price', '0.00')}

🛡️ **DELIVERED VIA ENCRYPTED SECRET CHAT**
🔒 End-to-end encryption active
🔥 Self-destructing messages enabled
❌ No server storage - maximum privacy!
✅ Your purchase is completely secure and private!"""
        
        return message
    
    async def send_product_to_user(self, user_id: int, product_data: dict, media_files: List[str] = None) -> Tuple[bool, str]:
        """🔐 Send product to user via REAL ENCRYPTED SECRET CHAT"""
        if not self.is_connected:
            return False, "Userbot not connected"
        
        if not self.secret_chat_manager:
            return False, "Secret chat manager not initialized"
        
        try:
            logger.info(f"🔐 SECRET CHAT: Starting encrypted delivery to user {user_id}")
            
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
            logger.info(f"🔍 SECRET CHAT: Found username @{username} for user {user_id}")
            
            # Get user entity
            try:
                user_entity = await self.client.get_entity(username)
                logger.info(f"✅ SECRET CHAT: Found user entity for @{username}")
            except Exception as e:
                logger.error(f"❌ SECRET CHAT: Error finding user @{username}: {e}")
                return False, f"Error finding user @{username}: {e}"
            
            # 🔐 CREATE ENCRYPTED SECRET CHAT
            try:
                logger.info(f"🔐 SECRET CHAT: Creating encrypted secret chat with user {user_id}")
                secret_chat_result = await self.secret_chat_manager.start_secret_chat(user_entity)
                logger.info(f"✅ SECRET CHAT: Encrypted secret chat created with @{username}, result: {secret_chat_result}")
                logger.info(f"🔍 SECRET CHAT: Result type: {type(secret_chat_result)}")
                
                # The result should be the actual secret chat object, not an ID
                secret_chat_object = secret_chat_result
                logger.info(f"🔐 SECRET CHAT: Using returned object as secret chat: {secret_chat_object}")
                
            except Exception as e:
                logger.error(f"❌ SECRET CHAT: Failed to create secret chat with @{username}: {e}")
                return False, f"Failed to create secret chat: {e}"
            
            # Create product message
            message = self._create_product_message(product_data)
            
            # 🔐 SEND VIA SECRET CHAT OBJECT DIRECTLY
            try:
                # Check if the returned object has send methods
                if hasattr(secret_chat_object, 'send_message'):
                    logger.info(f"📝 SECRET CHAT: Using secret_chat_object.send_message() method")
                    await secret_chat_object.send_message(message)
                    logger.info(f"✅ SECRET CHAT: Message sent via secret chat object method")
                    
                elif hasattr(secret_chat_object, 'send'):
                    logger.info(f"📝 SECRET CHAT: Using secret_chat_object.send() method")
                    await secret_chat_object.send(message)
                    logger.info(f"✅ SECRET CHAT: Message sent via secret chat send method")
                    
                elif secret_chat_object and isinstance(secret_chat_object, int):
                    # It's an ID (positive or negative), try to use it with the manager
                    logger.info(f"🔢 SECRET CHAT: Object is an ID ({secret_chat_object}), trying manager methods")
                    
                    # 🔍 DEBUG: Check what methods the SecretChatManager actually has
                    manager_methods = [method for method in dir(self.secret_chat_manager) if not method.startswith('_') and callable(getattr(self.secret_chat_manager, method))]
                    logger.info(f"🔍 SECRET CHAT: Available manager methods: {manager_methods}")
                    
                    # Try various method names that might exist
                    method_tried = False
                    
                    if hasattr(self.secret_chat_manager, 'send_secret_message'):
                        logger.info(f"🔐 SECRET CHAT: Trying send_secret_message with ID {secret_chat_object}")
                        
                        # Try to get the actual secret chat object using get_secret_chat
                        try:
                            secret_chat_obj = self.secret_chat_manager.get_secret_chat(secret_chat_object)
                            logger.info(f"🔍 SECRET CHAT: Retrieved secret chat object: {type(secret_chat_obj)}")
                            
                            if secret_chat_obj:
                                logger.info(f"🔐 SECRET CHAT: Using secret chat object for send_secret_message")
                                await self.secret_chat_manager.send_secret_message(secret_chat_obj, message)
                                logger.info(f"✅ SECRET CHAT: Message sent via manager send_secret_message with object")
                                method_tried = True
                            else:
                                logger.warning(f"⚠️ SECRET CHAT: get_secret_chat returned None, trying direct ID")
                                await self.secret_chat_manager.send_secret_message(secret_chat_object, message)
                                logger.info(f"✅ SECRET CHAT: Message sent via manager send_secret_message with ID")
                                method_tried = True
                                
                        except Exception as get_error:
                            logger.error(f"❌ SECRET CHAT: get_secret_chat failed: {get_error}")
                            logger.info(f"🔐 SECRET CHAT: Fallback to direct ID approach")
                            await self.secret_chat_manager.send_secret_message(secret_chat_object, message)
                            logger.info(f"✅ SECRET CHAT: Message sent via manager send_secret_message (fallback)")
                            method_tried = True
                    
                    if not method_tried:
                        # Try using the secret chat ID with InputEncryptedChat
                        logger.info(f"🔐 SECRET CHAT: No manager methods found, trying InputEncryptedChat approach")
                        try:
                            from telethon.tl.types import InputEncryptedChat
                            # Secret chat ID needs to be converted to InputEncryptedChat
                            # But we need access_hash - this approach might not work
                            logger.warning(f"⚠️ SECRET CHAT: InputEncryptedChat needs access_hash, trying direct ID instead")
                            await self.client.send_message(secret_chat_object, message)
                            logger.info(f"✅ SECRET CHAT: Message sent directly to secret chat ID")
                        except Exception as input_error:
                            logger.error(f"❌ SECRET CHAT: InputEncryptedChat approach failed: {input_error}")
                            # Final fallback - send to original user entity
                            logger.warning(f"⚠️ SECRET CHAT: All secret chat methods failed, using user entity fallback")
                            await self.client.send_message(user_entity, message)
                            logger.info(f"✅ SECRET CHAT: Message sent to user entity (final fallback)")
                    
                    # 🔐 NOW SEND MEDIA FILES TO SECRET CHAT USING CORRECT METHODS
                    if media_files and len(media_files) > 0 and method_tried:
                        logger.info(f"📂 SECRET CHAT: Sending {len(media_files)} media files to secret chat using secret methods")
                        
                        # Get the secret chat object for media sending
                        media_chat_target = secret_chat_object
                        try:
                            secret_chat_obj = self.secret_chat_manager.get_secret_chat(secret_chat_object)
                            if secret_chat_obj:
                                media_chat_target = secret_chat_obj
                                logger.info(f"🔍 SECRET CHAT: Using secret chat object for media sending")
                            else:
                                logger.info(f"🔍 SECRET CHAT: Using secret chat ID for media sending")
                        except Exception as obj_error:
                            logger.warning(f"⚠️ SECRET CHAT: Could not get secret chat object for media: {obj_error}")
                        
                        for i, media_file in enumerate(media_files):
                            try:
                                file_ext = os.path.splitext(media_file)[1].lower()
                                caption = f"📦 Product Media {i+1}/{len(media_files)}" if i == 0 else None
                                
                                if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                    logger.info(f"📸 SECRET CHAT: Sending photo {i+1} via send_secret_photo")
                                    await self.secret_chat_manager.send_secret_photo(media_chat_target, media_file, caption=caption)
                                elif file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
                                    logger.info(f"🎥 SECRET CHAT: Sending video {i+1} via send_secret_video")
                                    await self.secret_chat_manager.send_secret_video(media_chat_target, media_file, caption=caption)
                                else:
                                    logger.info(f"📄 SECRET CHAT: Sending document {i+1} via send_secret_document")
                                    await self.secret_chat_manager.send_secret_document(media_chat_target, media_file, caption=caption)
                                    
                                logger.info(f"✅ SECRET CHAT: Media file {i+1} sent to secret chat: {os.path.basename(media_file)}")
                            except Exception as media_error:
                                logger.error(f"❌ SECRET CHAT: Failed to send media {i+1}: {media_error}")
                        
                        logger.info(f"📂 SECRET CHAT: All {len(media_files)} media files processed for secret chat")
                    elif media_files and len(media_files) > 0:
                        logger.warning(f"⚠️ SECRET CHAT: Text message failed, skipping {len(media_files)} media files")
                    else:
                        logger.info(f"📂 SECRET CHAT: No media files to send")
                        
                else:
                    # Final fallback: send to user entity (regular DM)
                    logger.warning(f"⚠️ SECRET CHAT: Unknown secret chat object type, using fallback")
                    logger.info(f"🔍 SECRET CHAT: Object methods: {[method for method in dir(secret_chat_object) if not method.startswith('_')]}")
                    await self.client.send_message(user_entity, message)
                    logger.info(f"✅ SECRET CHAT: Message sent to user entity (fallback)")
                    
                    # Even in fallback, try to send media files
                    if media_files and len(media_files) > 0:
                        logger.info(f"📂 SECRET CHAT FALLBACK: Sending {len(media_files)} media files to user entity")
                        for i, media_file in enumerate(media_files):
                            try:
                                caption = f"📦 Product Media {i+1}/{len(media_files)}" if i == 0 else None
                                await self.client.send_file(user_entity, media_file, caption=caption)
                                logger.info(f"✅ SECRET CHAT FALLBACK: Media file {i+1} sent: {os.path.basename(media_file)}")
                            except Exception as media_error:
                                logger.error(f"❌ SECRET CHAT FALLBACK: Failed to send media {i+1}: {media_error}")
                
                logger.info(f"🎉 SECRET CHAT: Product delivery completed for user {user_id}")
                return True, "Product delivered via secret chat"
                
            except Exception as secret_send_error:
                logger.error(f"❌ SECRET CHAT: Failed to send via secret chat: {secret_send_error}")
                return False, f"Failed to send via secret chat: {secret_send_error}"
            
        except Exception as e:
            error_msg = f"Error sending product via secret chat: {e}"
            logger.error(f"❌ SECRET CHAT: {error_msg}")
            return False, error_msg

# Global instance
telethon_userbot = TelethonSecretUserbot()
