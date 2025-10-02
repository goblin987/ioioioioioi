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
        
        # Multi-userbot support
        self.userbots = []  # List of userbot configurations
        self.current_userbot_index = 0
        
        # Load existing configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load userbot configurations from persistent storage"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Check if it's multi-userbot format
                    if 'userbots' in config:
                        self.userbots = config['userbots']
                        logger.info(f"✅ MULTI-USERBOT: Loaded {len(self.userbots)} userbot configurations")
                        
                        # Set primary userbot as current
                        if self.userbots:
                            primary = self.userbots[0]
                            self.api_id = primary.get('api_id')
                            self.api_hash = primary.get('api_hash')
                            self.phone_number = primary.get('phone_number')
                            self.session_string = primary.get('session_string')
                            
                            if self.session_string:
                                self.has_session = True
                                logger.info(f"✅ MULTI-USERBOT: Primary userbot: {self.phone_number}")
                    else:
                        # Legacy single userbot format - convert to multi-userbot
                        legacy_userbot = {
                            'api_id': config.get('api_id'),
                            'api_hash': config.get('api_hash'),
                            'phone_number': config.get('phone_number'),
                            'session_string': config.get('session_string'),
                            'rate_limited_until': 0
                        }
                        self.userbots = [legacy_userbot]
                        
                        # Set legacy as current
                        self.api_id = legacy_userbot['api_id']
                        self.api_hash = legacy_userbot['api_hash']
                        self.phone_number = legacy_userbot['phone_number']
                        self.session_string = legacy_userbot['session_string']
                        
                        if self.session_string:
                            self.has_session = True
                            logger.info(f"✅ SIMPLE: Converted legacy config for {self.phone_number}")
                        
                        # Save in new format
                        self._save_configuration()
            else:
                logger.info(f"ℹ️ SIMPLE: No configuration file found")
        except Exception as e:
            logger.error(f"❌ SIMPLE: Error loading configuration: {e}")
    
    def _save_configuration(self):
        """Save userbot configurations to persistent storage"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            config = {
                'userbots': self.userbots,
                'current_userbot_index': self.current_userbot_index
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"✅ MULTI-USERBOT: Configuration saved ({len(self.userbots)} userbots)")
        except Exception as e:
            logger.error(f"❌ MULTI-USERBOT: Error saving configuration: {e}")
    
    def add_userbot(self, api_id: int, api_hash: str, phone_number: str, session_string: str = None):
        """Add a new userbot to the rotation"""
        new_userbot = {
            'api_id': api_id,
            'api_hash': api_hash,
            'phone_number': phone_number,
            'session_string': session_string,
            'rate_limited_until': 0
        }
        
        self.userbots.append(new_userbot)
        self._save_configuration()
        logger.info(f"✅ MULTI-USERBOT: Added userbot {phone_number} (Total: {len(self.userbots)})")
        return True, f"Userbot {phone_number} added successfully"
    
    def get_available_userbot(self):
        """Get next available userbot (not rate limited)"""
        import time
        current_time = time.time()
        
        # Check all userbots for availability
        for i, userbot in enumerate(self.userbots):
            if userbot.get('rate_limited_until', 0) < current_time:
                if userbot.get('session_string'):
                    logger.info(f"✅ MULTI-USERBOT: Using userbot {i+1}: {userbot['phone_number']}")
                    return i, userbot
        
        logger.warning(f"⚠️ MULTI-USERBOT: All {len(self.userbots)} userbots are rate limited")
        return None, None
    
    def mark_userbot_rate_limited(self, userbot_index: int, wait_seconds: int):
        """Mark a userbot as rate limited"""
        import time
        if userbot_index < len(self.userbots):
            self.userbots[userbot_index]['rate_limited_until'] = time.time() + wait_seconds
            self._save_configuration()
            logger.warning(f"⚠️ MULTI-USERBOT: Marked userbot {userbot_index+1} as rate limited for {wait_seconds}s")
    
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
    
    async def _switch_to_userbot(self, userbot_index: int):
        """Switch to a different userbot"""
        if userbot_index >= len(self.userbots):
            return False
        
        # Disconnect current userbot
        if self.client and self.is_connected:
            await self.disconnect()
        
        # Switch to new userbot
        userbot_config = self.userbots[userbot_index]
        self.api_id = userbot_config['api_id']
        self.api_hash = userbot_config['api_hash']
        self.phone_number = userbot_config['phone_number']
        self.session_string = userbot_config['session_string']
        self.current_userbot_index = userbot_index
        
        # Connect new userbot
        if self.session_string:
            self.has_session = True
            success, message = await self.connect()
            logger.info(f"🔄 MULTI-USERBOT: Switched to userbot {userbot_index+1}: {self.phone_number}")
            return success
        
        return False
    
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
        """🔐 MULTI-USERBOT SECRET CHAT - Automatic rotation to avoid rate limits"""
        
        # Get available userbot (not rate limited)
        userbot_index, userbot_config = self.get_available_userbot()
        if not userbot_config:
            return False, "All userbots are rate limited"
        
        # Switch to available userbot if different from current
        if userbot_index != self.current_userbot_index:
            logger.info(f"🔄 MULTI-USERBOT: Switching from userbot {self.current_userbot_index+1} to {userbot_index+1}")
            await self._switch_to_userbot(userbot_index)
        
        if not self.is_connected:
            return False, "Selected userbot not connected"
        
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
            
            # 🔐 CREATE OR REUSE SECRET CHAT (AVOID RATE LIMITS)
            try:
                from telethon_secret_chat import SecretChatManager
                secret_chat_manager = SecretChatManager(self.client, auto_accept=True)
                
                # Check if we have an existing secret chat with this user
                existing_chats = []
                try:
                    # Try to get existing secret chats
                    if hasattr(secret_chat_manager, 'get_all_secret_chats'):
                        existing_chats = secret_chat_manager.get_all_secret_chats()
                        logger.info(f"🔍 SECRET CHAT RETRY: Found {len(existing_chats)} existing secret chats")
                except Exception as check_error:
                    logger.info(f"ℹ️ SECRET CHAT RETRY: Could not check existing chats: {check_error}")
                
                # Try to reuse existing secret chat or create new one
                secret_chat_id = None
                for chat in existing_chats:
                    try:
                        # Check if this chat is with our target user
                        if hasattr(chat, 'user_id') and chat.user_id == user_entity.id:
                            secret_chat_id = chat.id
                            logger.info(f"✅ SECRET CHAT RETRY: Reusing existing secret chat, ID: {secret_chat_id}")
                            break
                    except:
                        continue
                
                # If no existing chat found, create new one
                if not secret_chat_id:
                    logger.info(f"🔐 SECRET CHAT RETRY: Creating NEW secret chat with @{username}")
                    secret_chat_id = await secret_chat_manager.start_secret_chat(user_entity)
                    logger.info(f"✅ SECRET CHAT RETRY: NEW secret chat created, ID: {secret_chat_id}")
                else:
                    logger.info(f"♻️ SECRET CHAT RETRY: Using EXISTING secret chat, ID: {secret_chat_id}")
                
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
                                    logger.info(f"🎥 SECRET CHAT RETRY: AUTO-DETECT APPROACH for {file_name}")
                                    
                                    # Let the plugin auto-detect ALL parameters - don't override anything!
                                    try:
                                        logger.info(f"🎬 SECRET CHAT RETRY: Letting plugin auto-detect video parameters")
                                        
                                        # Check if send_secret_video accepts just the file path
                                        import inspect
                                        sig = inspect.signature(secret_chat_manager.send_secret_video)
                                        logger.info(f"🔍 SECRET CHAT RETRY: send_secret_video signature: {sig}")
                                        
                                        # Try with only required parameters
                                        await secret_chat_manager.send_secret_video(target, media_file)
                                        logger.info(f"✅ SECRET CHAT RETRY: AUTO-DETECT video {i+1} sent!")
                                        
                                    except TypeError as type_error:
                                        logger.warning(f"⚠️ SECRET CHAT RETRY: Auto-detect failed (missing params): {type_error}")
                                        
                                        # Try with None values to let plugin detect
                                        try:
                                            logger.info(f"🔄 SECRET CHAT RETRY: Trying with None parameters for auto-detection")
                                            await secret_chat_manager.send_secret_video(
                                                target, media_file,
                                                thumb=None, thumb_w=None, thumb_h=None, duration=None,
                                                mime_type=None, w=None, h=None, size=None
                                            )
                                            logger.info(f"✅ SECRET CHAT RETRY: None-parameter video {i+1} sent!")
                                            
                                        except Exception as none_error:
                                            logger.error(f"❌ SECRET CHAT RETRY: None-parameter approach failed: {none_error}")
                                            
                                            # FINAL FALLBACK: Honest message about video encryption issues
                                            video_info = f"""🎥 **VIDEO ENCRYPTION ISSUE**
                                            
📁 Original: {file_name} ({file_size:,} bytes)
⚠️ **Secret chat video encryption corrupts the file.**

🔐 **Your payment is confirmed and video is available.**
📞 **Please contact support for manual video delivery.**"""
                                            
                                            await secret_chat_manager.send_secret_message(target, video_info)
                                            logger.info(f"✅ SECRET CHAT RETRY: Honest video issue message sent")
                                    
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
                
                # RATE LIMIT HANDLING: Mark current userbot as rate limited and try next one
                if "wait" in str(secret_error).lower() and "seconds" in str(secret_error).lower():
                    # Extract wait time from error message
                    import re
                    wait_match = re.search(r'wait of (\d+) seconds', str(secret_error))
                    wait_seconds = int(wait_match.group(1)) if wait_match else 3600  # Default 1 hour
                    
                    logger.warning(f"⚠️ MULTI-USERBOT: Current userbot rate limited for {wait_seconds}s")
                    self.mark_userbot_rate_limited(self.current_userbot_index, wait_seconds)
                    
                    # Try next available userbot
                    next_index, next_userbot = self.get_available_userbot()
                    if next_userbot:
                        logger.info(f"🔄 MULTI-USERBOT: Trying next userbot {next_index+1}")
                        await self._switch_to_userbot(next_index)
                        
                        # Retry delivery with new userbot
                        return await self.send_product_to_user(user_id, product_data, media_files)
                    else:
                        logger.error(f"❌ MULTI-USERBOT: All userbots are rate limited!")
                        return False, f"All userbots are rate limited. Please add more userbots or wait."
                else:
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
