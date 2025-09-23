#!/usr/bin/env python3
"""
🔐 SIMPLE TELETHON USERBOT - NO BUGGY PLUGINS
Direct message delivery that actually works!
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from telethon import TelegramClient
from telethon.tl.types import User
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

logger = logging.getLogger(__name__)

class SimpleUserbot:
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
                    
                    if self.session_string:
                        self.has_session = True
                        logger.info(f"✅ SIMPLE: Loaded configuration for {self.phone_number}")
                    else:
                        logger.info(f"ℹ️ SIMPLE: Configuration loaded but no session string")
            else:
                logger.info(f"ℹ️ SIMPLE: No configuration file found")
        except Exception as e:
            logger.error(f"❌ SIMPLE: Error loading configuration: {e}")
    
    def _save_configuration(self):
        """Save userbot configuration to persistent storage"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            config = {
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'phone_number': self.phone_number,
                'session_string': self.session_string
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
            logger.info(f"✅ SIMPLE: Configuration saved")
        except Exception as e:
            logger.error(f"❌ SIMPLE: Error saving configuration: {e}")
    
    def set_credentials(self, api_id: int, api_hash: str, phone_number: str, session_string: str = None):
        """Set userbot credentials"""
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        if session_string:
            self.session_string = session_string
            self.has_session = True
        
        self._save_configuration()
        logger.info(f"✅ SIMPLE: Credentials set for {phone_number}")
    
    def is_configured(self) -> bool:
        """Check if userbot is configured"""
        return bool(self.api_id and self.api_hash and self.phone_number)
    
    async def connect(self) -> Tuple[bool, str]:
        """Connect the userbot"""
        if not self.is_configured():
            return False, "Userbot not configured"
        
        if not self.has_session:
            return False, "No session available"
        
        try:
            logger.info(f"🔌 SIMPLE: Connecting...")
            
            # Create Telethon client with session string
            from telethon.sessions import StringSession
            self.client = TelegramClient(
                StringSession(self.session_string), 
                self.api_id, 
                self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                return False, "Session expired - please re-authenticate"
            
            # Get user info
            me = await self.client.get_me()
            self.is_connected = True
            
            success_msg = f"Connected as @{me.username or me.first_name}"
            logger.info(f"✅ SIMPLE: {success_msg}")
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ SIMPLE: Connection failed: {e}")
            return False, f"Connection error: {e}"
    
    async def disconnect(self):
        """Disconnect the userbot"""
        try:
            if self.client:
                await self.client.disconnect()
                self.client = None
            self.is_connected = False
            logger.info(f"✅ SIMPLE: Disconnected")
        except Exception as e:
            logger.error(f"❌ SIMPLE: Error disconnecting: {e}")
    
    def get_status(self) -> str:
        """Get userbot status"""
        if not self.is_configured():
            return "❌ Not configured"
        elif not self.has_session:
            return "⚠️ No session - needs authentication"
        elif self.is_connected:
            return "✅ Connected and ready"
        else:
            return "⚠️ Configured but not connected"
    
    def clear_configuration(self):
        """Clear userbot configuration and session"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                os.remove(config_file)
                logger.info("✅ SIMPLE: Configuration file deleted")
            
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
            
            logger.info("✅ SIMPLE: Configuration cleared")
            return True, "Configuration cleared successfully"
            
        except Exception as e:
            logger.error(f"❌ SIMPLE: Error clearing configuration: {e}")
            return False, f"Error clearing configuration: {e}"
    
    def _create_product_message(self, product_data: dict) -> str:
        """Create product message"""
        message = f"""🔐 **DIRECT SECURE DELIVERY** 🔐

📦 **Product**: {product_data['product_name']}
🏙️ **City**: {product_data['city'].title()}
🏘️ **District**: {product_data['district'].title()}
📏 **Size**: {product_data['size']}
💰 **Price**: {product_data['price']} EUR

✅ **Payment confirmed - product ready for pickup!**

🚀 **This message was delivered directly via secure userbot - no bot chat delivery!**"""
        return message
    
    async def send_product_to_user(self, user_id: int, product_data: dict, media_files: List[str] = None) -> Tuple[bool, str]:
        """🔐 SECRET CHAT WITH WAIT-AND-RETRY - Using plugin but with proper timing"""
        if not self.is_connected:
            return False, "Userbot not connected"
        
        try:
            logger.info(f"🔐 SECRET CHAT RETRY: Starting encrypted delivery to user {user_id}")
            
            # Get user's Telegram username from database
            from utils import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                return False, f"No username found for user {user_id}"
            
            username = user_data[0]
            logger.info(f"🔍 SECRET CHAT RETRY: Found username @{username} for user {user_id}")
            
            # Get user entity
            try:
                user_entity = await self.client.get_entity(username)
                logger.info(f"✅ SECRET CHAT RETRY: Found user entity for @{username}")
            except Exception as e:
                logger.error(f"❌ SECRET CHAT RETRY: Error finding user @{username}: {e}")
                return False, f"Error finding user @{username}: {e}"
            
            # 🔐 CREATE SECRET CHAT WITH WAIT-AND-RETRY APPROACH
            try:
                from telethon_secret_chat import SecretChatManager
                secret_chat_manager = SecretChatManager(self.client, auto_accept=True)
                
                logger.info(f"🔐 SECRET CHAT RETRY: Creating secret chat with @{username}")
                secret_chat_id = await secret_chat_manager.start_secret_chat(user_entity)
                logger.info(f"✅ SECRET CHAT RETRY: Secret chat created, ID: {secret_chat_id}")
                
                # 🔐 WAIT-AND-RETRY MESSAGE SENDING (5 attempts with increasing delays)
                message = self._create_product_message(product_data)
                message_sent = False
                
                for attempt in range(1, 6):  # 5 attempts
                    try:
                        wait_time = attempt * 2  # 2, 4, 6, 8, 10 seconds
                        logger.info(f"🔄 SECRET CHAT RETRY: Attempt {attempt}/5 - waiting {wait_time}s before sending")
                        await asyncio.sleep(wait_time)
                        
                        # Try to get the secret chat object
                        secret_chat_obj = secret_chat_manager.get_secret_chat(secret_chat_id)
                        if secret_chat_obj:
                            logger.info(f"🔍 SECRET CHAT RETRY: Got secret chat object: {type(secret_chat_obj)}")
                            await secret_chat_manager.send_secret_message(secret_chat_obj, message)
                        else:
                            logger.info(f"🔍 SECRET CHAT RETRY: No object, trying direct ID")
                            await secret_chat_manager.send_secret_message(secret_chat_id, message)
                        
                        logger.info(f"✅ SECRET CHAT RETRY: Message sent successfully on attempt {attempt}")
                        message_sent = True
                        break
                        
                    except Exception as send_error:
                        logger.warning(f"⚠️ SECRET CHAT RETRY: Attempt {attempt}/5 failed: {send_error}")
                        if attempt == 5:
                            logger.error(f"❌ SECRET CHAT RETRY: All 5 attempts failed!")
                
                if not message_sent:
                    return False, "Failed to send message to secret chat after 5 attempts"
                
                # 🔐 SEND ACTUAL MEDIA FILES TO SECRET CHAT
                if media_files and len(media_files) > 0:
                    logger.info(f"📂 SECRET CHAT RETRY: Sending {len(media_files)} ACTUAL media files")
                    
                    for i, media_file in enumerate(media_files):
                        media_sent = False
                        for attempt in range(1, 4):  # 3 attempts per media file
                            try:
                                await asyncio.sleep(2)  # Wait between attempts
                                
                                file_name = os.path.basename(media_file)
                                file_ext = os.path.splitext(media_file)[1].lower()
                                file_size = os.path.getsize(media_file)
                                
                                logger.info(f"📁 SECRET CHAT RETRY: Attempt {attempt}/3 for {file_name} ({file_size:,} bytes)")
                                
                                # Get secret chat object
                                secret_chat_obj = secret_chat_manager.get_secret_chat(secret_chat_id)
                                target = secret_chat_obj if secret_chat_obj else secret_chat_id
                                
                                # 🔐 TRY TO SEND ACTUAL MEDIA FILE WITH FILE PATH (PRESERVE FORMAT)
                                if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                    logger.info(f"📸 SECRET CHAT RETRY: Sending ACTUAL photo {file_name} using file path")
                                    
                                    # Try send_secret_photo with file path to preserve format
                                    await secret_chat_manager.send_secret_photo(
                                        target, media_file,  # Use file path, not bytes
                                        thumb=b'', thumb_w=100, thumb_h=100, w=800, h=600, size=file_size
                                    )
                                    logger.info(f"✅ SECRET CHAT RETRY: ACTUAL photo {i+1} sent with preserved format!")
                                    
                                elif file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
                                    logger.info(f"🎥 SECRET CHAT RETRY: Sending video {file_name} as PERFECT DOCUMENT")
                                    
                                    # Always send videos as documents with video MIME type for perfect quality
                                    if file_ext == '.mov':
                                        mime_type = 'video/quicktime'
                                        display_name = f"{os.path.splitext(file_name)[0]}.mov"
                                    elif file_ext == '.mp4':
                                        mime_type = 'video/mp4'
                                        display_name = f"{os.path.splitext(file_name)[0]}.mp4"
                                    elif file_ext == '.avi':
                                        mime_type = 'video/x-msvideo'
                                        display_name = f"{os.path.splitext(file_name)[0]}.avi"
                                    else:
                                        mime_type = 'video/mp4'
                                        display_name = f"{os.path.splitext(file_name)[0]}.mp4"
                                    
                                    # Send as document with proper video MIME type
                                    logger.info(f"📁 SECRET CHAT RETRY: Sending {display_name} as document with {mime_type}")
                                    await secret_chat_manager.send_secret_document(
                                        target, media_file,
                                        thumb=b'', thumb_w=0, thumb_h=0,
                                        file_name=display_name, mime_type=mime_type, size=file_size
                                    )
                                    logger.info(f"✅ SECRET CHAT RETRY: Video {i+1} sent as PERFECT document ({mime_type})!")
                                    
                                else:
                                    logger.info(f"📄 SECRET CHAT RETRY: Sending ACTUAL document {file_name} using file path")
                                    
                                    # Try send_secret_document with file path to preserve format
                                    await secret_chat_manager.send_secret_document(
                                        target, media_file,  # Use file path, not bytes
                                        thumb=b'', thumb_w=0, thumb_h=0,
                                        file_name=file_name, mime_type='application/octet-stream', size=file_size
                                    )
                                    logger.info(f"✅ SECRET CHAT RETRY: ACTUAL document {i+1} sent with preserved format!")
                                
                                media_sent = True
                                break  # Success - exit retry loop
                                
                            except Exception as send_error:
                                logger.warning(f"⚠️ SECRET CHAT RETRY: Attempt {attempt}/3 failed for {file_name}: {send_error}")
                                if attempt == 3:
                                    logger.error(f"❌ SECRET CHAT RETRY: All attempts failed for {file_name}")
                        
                        if not media_sent:
                            logger.error(f"❌ SECRET CHAT RETRY: Could not send actual media file {file_name}")
                    
                    logger.info(f"📂 SECRET CHAT RETRY: Finished sending ACTUAL media files")
                
                logger.info(f"🎉 SECRET CHAT RETRY: Delivery completed for user {user_id}")
                return True, f"Product delivered via SECRET CHAT to @{username}"
                
            except Exception as secret_error:
                logger.error(f"❌ SECRET CHAT RETRY: Failed to create secret chat: {secret_error}")
                return False, f"Failed to create secret chat: {secret_error}"
            
        except Exception as e:
            logger.error(f"❌ SECRET CHAT RETRY: General error: {e}")
            return False, f"Error in secret chat delivery: {e}"
    
    async def handle_secret_chat_confirmation(self, user_id: int, message_text: str) -> bool:
        """Handle confirmation message from secret chat"""
        if message_text.upper().strip() == "CONFIRM":
            try:
                logger.info(f"🎯 SECRET CHAT CONFIRMATION: Processing for user {user_id}")
                
                # Get pending delivery from database
                from utils import get_db_connection
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM pending_deliveries WHERE user_id = ?", (user_id,))
                delivery_data = c.fetchone()
                
                if not delivery_data:
                    logger.warning(f"⚠️ SECRET CHAT CONFIRMATION: No pending delivery for user {user_id}")
                    return False
                
                user_id, username, secret_chat_id, product_data_json, media_files_json, created_at = delivery_data
                product_data = json.loads(product_data_json)
                media_files = json.loads(media_files_json)
                
                logger.info(f"📦 SECRET CHAT CONFIRMATION: Delivering product to user {user_id}")
                
                # Create full product message
                message = self._create_product_message(product_data)
                
                # Send product details and media to secret chat
                from telethon_secret_chat import SecretChatManager
                secret_chat_manager = SecretChatManager(self.client, auto_accept=True)
                
                # Send product message
                await secret_chat_manager.send_secret_message(secret_chat_id, message)
                logger.info(f"✅ SECRET CHAT CONFIRMATION: Product details sent")
                
                # Send media files
                if media_files:
                    for i, media_file in enumerate(media_files):
                        try:
                            file_ext = os.path.splitext(media_file)[1].lower()
                            caption = f"📦 Product Media {i+1}/{len(media_files)}"
                            
                            if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                await secret_chat_manager.send_secret_photo(secret_chat_id, media_file, caption=caption)
                            elif file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
                                await secret_chat_manager.send_secret_video(secret_chat_id, media_file, caption=caption)
                            else:
                                await secret_chat_manager.send_secret_document(secret_chat_id, media_file, caption=caption)
                            
                            logger.info(f"✅ SECRET CHAT CONFIRMATION: Media {i+1} sent: {os.path.basename(media_file)}")
                        except Exception as media_error:
                            logger.error(f"❌ SECRET CHAT CONFIRMATION: Failed to send media {i+1}: {media_error}")
                
                # Remove from pending deliveries
                c.execute("DELETE FROM pending_deliveries WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                
                logger.info(f"🎉 SECRET CHAT CONFIRMATION: Delivery completed for user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"❌ SECRET CHAT CONFIRMATION: Error: {e}")
                return False
        
        return False

# Global instance
simple_userbot = SimpleUserbot()
