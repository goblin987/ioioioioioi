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
        """🔐 NATIVE TELETHON SECRET CHAT - Using TL functions directly"""
        if not self.is_connected:
            return False, "Userbot not connected"
        
        try:
            logger.info(f"🔐 NATIVE SECRET CHAT: Starting encrypted delivery to user {user_id}")
            
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
            logger.info(f"🔍 NATIVE SECRET CHAT: Found username @{username} for user {user_id}")
            
            # Get user entity
            try:
                user_entity = await self.client.get_entity(username)
                logger.info(f"✅ NATIVE SECRET CHAT: Found user entity for @{username}")
            except Exception as e:
                logger.error(f"❌ NATIVE SECRET CHAT: Error finding user @{username}: {e}")
                return False, f"Error finding user @{username}: {e}"
            
            # 🔐 CREATE SECRET CHAT USING NATIVE TELETHON TL FUNCTIONS
            try:
                from telethon.tl.functions.messages import RequestEncryptionRequest
                from telethon.tl.types import InputUser
                
                logger.info(f"🔐 NATIVE SECRET CHAT: Creating encrypted secret chat with @{username} using TL functions")
                
                # Create InputUser from entity
                input_user = InputUser(user_entity.id, user_entity.access_hash)
                
                # Request encryption (secret chat)
                import random
                random_id = random.randint(1, 2**63 - 1)
                
                result = await self.client(RequestEncryptionRequest(
                    user_id=input_user,
                    random_id=random_id
                ))
                
                logger.info(f"✅ NATIVE SECRET CHAT: Secret chat requested with @{username}, result: {result}")
                logger.info(f"🔍 NATIVE SECRET CHAT: Result type: {type(result)}")
                
                # Wait a moment for secret chat to be established
                await asyncio.sleep(2)
                
                # Try to send message to the secret chat
                message = self._create_product_message(product_data)
                
                # Use the secret chat from the result
                if hasattr(result, 'chat'):
                    secret_chat = result.chat
                    logger.info(f"🔐 NATIVE SECRET CHAT: Using secret chat from result: {secret_chat}")
                    
                    # Send message to secret chat
                    await self.client.send_message(secret_chat, message)
                    logger.info(f"✅ NATIVE SECRET CHAT: Product details sent to secret chat")
                    
                    # Send media files
                    if media_files and len(media_files) > 0:
                        logger.info(f"📂 NATIVE SECRET CHAT: Sending {len(media_files)} media files to secret chat")
                        
                        for i, media_file in enumerate(media_files):
                            try:
                                caption = f"📦 Product Media {i+1}/{len(media_files)}" if i == 0 else None
                                await self.client.send_file(secret_chat, media_file, caption=caption)
                                logger.info(f"✅ NATIVE SECRET CHAT: Media file {i+1} sent: {os.path.basename(media_file)}")
                            except Exception as media_error:
                                logger.error(f"❌ NATIVE SECRET CHAT: Failed to send media {i+1}: {media_error}")
                        
                        logger.info(f"📂 NATIVE SECRET CHAT: All {len(media_files)} media files processed")
                    
                    logger.info(f"🎉 NATIVE SECRET CHAT: Product delivery completed for user {user_id}")
                    return True, f"Product delivered via NATIVE SECRET CHAT to @{username}"
                    
                else:
                    logger.error(f"❌ NATIVE SECRET CHAT: No chat object in result: {result}")
                    return False, f"Secret chat creation failed - no chat object"
                
            except Exception as secret_error:
                logger.error(f"❌ NATIVE SECRET CHAT: Failed to create secret chat: {secret_error}")
                return False, f"Failed to create secret chat: {secret_error}"
            
        except Exception as e:
            logger.error(f"❌ NATIVE SECRET CHAT: General error: {e}")
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
