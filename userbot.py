"""
Simple Userbot for Product Delivery
Workflow: Buyer buys product → Payment confirmed → Userbot creates secret chat → Sends product details
"""
import asyncio
import json
import logging
import os
import re
from typing import Optional, Dict, Any, List, Tuple
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaDocument
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneNumberInvalid,
    FloodWait,
    UsernameNotOccupied,
    UsernameInvalid
)

logger = logging.getLogger(__name__)

class SimpleUserbot:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.session_string = None
        self.has_session = False
        
        # Load existing configuration at startup
        self._load_configuration()
    
    def _load_configuration(self):
        """Load userbot configuration from file"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.api_id = config.get('api_id')
                self.api_hash = config.get('api_hash')
                self.phone_number = config.get('phone_number')
                self.session_string = config.get('session_string')
                
                if self.api_id and self.api_hash and self.phone_number and self.session_string:
                    self.has_session = True
                    logger.info(f"✅ USERBOT: Loaded configuration for {self.phone_number}")
                else:
                    logger.info("ℹ️ USERBOT: Incomplete configuration found")
            else:
                logger.info("ℹ️ USERBOT: No configuration file found")
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Error loading configuration: {e}")
    
    def _save_configuration(self):
        """Save userbot configuration to file"""
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
            
            logger.info("✅ USERBOT: Configuration saved")
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error saving configuration: {e}")
    
    def clear_configuration(self):
        """Clear userbot configuration and session"""
        try:
            config_file = '/mnt/data/userbot_config.json'
            if os.path.exists(config_file):
                os.remove(config_file)
                logger.info("✅ USERBOT: Configuration file deleted")
            
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
                    asyncio.create_task(self.client.stop())
                except:
                    pass
                self.client = None
            
            logger.info("✅ USERBOT: Configuration cleared")
            return True, "Configuration cleared successfully"
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error clearing configuration: {e}")
            return False, f"Error clearing configuration: {e}"
        
    def set_credentials(self, api_id: int, api_hash: str, phone_number: str) -> Tuple[bool, str]:
        """Set userbot credentials"""
        try:
            # Basic validation
            if not isinstance(api_id, int) or api_id <= 0:
                return False, "Invalid API ID"
            
            if not isinstance(api_hash, str) or len(api_hash) != 32:
                return False, "Invalid API Hash (must be 32 characters)"
            
            if not isinstance(phone_number, str) or not phone_number.startswith('+'):
                return False, "Invalid phone number (must start with +)"
            
            self.api_id = api_id
            self.api_hash = api_hash
            self.phone_number = phone_number
            
            logger.info(f"✅ USERBOT: Credentials set for {phone_number}")
            return True, "Credentials set successfully"
            
        except Exception as e:
            error_msg = f"Error setting credentials: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_code(self, code: str) -> Tuple[bool, str]:
        """Generate session string and connect"""
        try:
            if not all([self.api_id, self.api_hash, self.phone_number]):
                return False, "Credentials not set"
            
            if not code or not code.strip().isdigit():
                return False, "Invalid verification code"
                
            logger.info("📱 USERBOT: Authenticating...")
            
            # Create temporary client for authentication
            temp_client = Client(
                name="temp_auth",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir="temp"
            )
            
            # Ensure temp directory exists
            os.makedirs("temp", exist_ok=True)
            
            # Authenticate and get session string
            await temp_client.start(phone_code=code.strip())
            self.session_string = await temp_client.export_session_string()
            await temp_client.stop()
            
            # Clean up temp files
            self._cleanup_temp_files()
            
            # Connect with session string
            success, message = await self.connect()
            return success, message
            
        except PhoneCodeInvalid:
            self._cleanup_temp_files()
            return False, "Invalid verification code"
        except SessionPasswordNeeded:
            self._cleanup_temp_files()
            return False, "2FA password required - use authenticate_with_2fa instead"
        except Exception as e:
            self._cleanup_temp_files()
            error_msg = f"Authentication error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_2fa(self, code: str, password: str) -> Tuple[bool, str]:
        """Authenticate with 2FA"""
        try:
            if not all([self.api_id, self.api_hash, self.phone_number]):
                return False, "Credentials not set"
            
            if not code or not code.strip().isdigit():
                return False, "Invalid verification code"
            
            if not password or not password.strip():
                return False, "2FA password required"
                
            logger.info("🔐 USERBOT: Authenticating with 2FA...")
            
            # Create temporary client for authentication
            temp_client = Client(
                name="temp_auth_2fa",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir="temp"
            )
            
            # Ensure temp directory exists
            os.makedirs("temp", exist_ok=True)
            
            # Authenticate with code and password
            await temp_client.start(phone_code=code.strip(), password=password.strip())
            self.session_string = await temp_client.export_session_string()
            await temp_client.stop()
            
            # Clean up temp files
            self._cleanup_temp_files()
            
            # Connect with session string
            success, message = await self.connect()
            return success, message
            
        except Exception as e:
            self._cleanup_temp_files()
            error_msg = f"2FA authentication error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def connect(self) -> Tuple[bool, str]:
        """Connect userbot using session string"""
        try:
            if not self.session_string:
                return False, "No session string - authenticate first"
            
            logger.info("🔌 USERBOT: Connecting...")
            
            # Create client with session string
            self.client = Client(
                name="userbot",
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=self.session_string
            )
            
            # Start client
            await self.client.start()
            
            # Verify connection
            me = await self.client.get_me()
            if me:
                self.is_connected = True
                logger.info(f"✅ USERBOT: Connected as @{me.username or me.first_name}")
                return True, f"Connected as @{me.username or me.first_name}"
            else:
                return False, "Failed to get user info"
                
        except Exception as e:
            error_msg = f"Connection error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def send_product_to_user(self, user_id: int, product_data: dict, media_files: List[str] = None) -> Tuple[bool, str]:
        """
        Main workflow: Send product to user via direct message
        This is the core function for the workflow you described
        """
        try:
            if not self.is_connected or not self.client:
                return False, "Userbot not connected"
            
            logger.info(f"📦 USERBOT: Sending product to user {user_id}")
            
            # Get user info from database
            from utils import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT telegram_username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                return False, f"No username found for user {user_id}"
            
            username = user_data[0]
            if not username.startswith('@'):
                username = f"@{username}"
            
            # Get user entity
            try:
                user_entity = await self.client.get_users(username)
                if not user_entity:
                    return False, f"User {username} not found"
            except (UsernameNotOccupied, UsernameInvalid):
                return False, f"Invalid username: {username}"
            except Exception as e:
                return False, f"Error finding user {username}: {e}"
            
            # Create product message
            message = self._create_product_message(product_data)
            
            # Send media files if any
            if media_files and len(media_files) > 0:
                try:
                    media_objects = []
                    for media_file in media_files:
                        if os.path.exists(media_file):
                            if media_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                media_objects.append(InputMediaPhoto(media_file))
                            else:
                                media_objects.append(InputMediaDocument(media_file))
                    
                    if media_objects:
                        await self.client.send_media_group(user_entity.id, media_objects)
                        logger.info(f"✅ USERBOT: Sent {len(media_objects)} media files to user {user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ USERBOT: Error sending media: {e}")
            
            # Send product message
            await self.client.send_message(user_entity.id, message)
            logger.info(f"✅ USERBOT: Product delivered to user {user_id}")
            
            return True, "Product delivered successfully"
            
        except Exception as e:
            error_msg = f"Error sending product: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    def _create_product_message(self, product_data: dict) -> str:
        """Create formatted product message"""
        try:
            message = "🎉 **YOUR PRODUCT IS READY!**\n\n"
            
            if product_data.get('product_name'):
                message += f"📦 **Product**: {product_data['product_name']}\n"
            
            if product_data.get('product_type'):
                message += f"🏷️ **Type**: {product_data['product_type']}\n"
            
            if product_data.get('city') and product_data.get('district'):
                message += f"📍 **Location**: {product_data['city']}, {product_data['district']}\n"
            
            if product_data.get('size'):
                message += f"📏 **Size**: {product_data['size']}\n"
            
            if product_data.get('price'):
                message += f"💰 **Price**: {product_data['price']} EUR\n"
            
            message += "\n✅ **Delivered securely via userbot**\n"
            message += "🔒 **This message was sent privately to you**"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error creating message: {e}")
            return "🎉 **YOUR PRODUCT IS READY!**\n\nProduct details are attached."
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = "temp"
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
        except Exception as e:
            logger.warning(f"⚠️ USERBOT: Cleanup error: {e}")
    
    async def disconnect(self) -> Tuple[bool, str]:
        """Disconnect userbot"""
        if self.client and self.is_connected:
            try:
                await self.client.stop()
                self.is_connected = False
                logger.info("✅ USERBOT: Disconnected")
                return True, "Disconnected successfully"
            except Exception as e:
                error_msg = f"Error disconnecting: {e}"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
        else:
            return True, "Already disconnected"
    
    def get_status(self) -> Dict[str, Any]:
        """Get userbot status"""
        return {
            'connected': self.is_connected,
            'has_credentials': all([self.api_id, self.api_hash, self.phone_number]),
            'has_session': bool(self.session_string),
            'phone_number': self.phone_number if self.phone_number else None
        }

# Global instance
userbot = SimpleUserbot()
