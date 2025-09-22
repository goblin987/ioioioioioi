import asyncio
import logging
import os
import random
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaDocument, InputPeerUser
from pyrogram.raw.functions.messages import RequestEncryption
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneNumberInvalid,
    FloodWait,
    AuthKeyUnregistered,
    UsernameNotOccupied,
    UsernameInvalid
)
from session_generator import session_generator

logger = logging.getLogger(__name__)

class ImprovedSimpleUserbot:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.is_authenticated = False
        self.session_name = "improved_userbot"
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.session_string = None
        self.max_retries = 3
        self.retry_delay = 2
        
    def _validate_credentials(self, api_id: int, api_hash: str, phone_number: str) -> Tuple[bool, str]:
        """Validate userbot credentials"""
        try:
            # Validate API ID
            if not isinstance(api_id, int) or api_id <= 0:
                return False, "Invalid API ID: must be a positive integer"
            
            # Validate API Hash
            if not isinstance(api_hash, str) or len(api_hash) != 32:
                return False, "Invalid API Hash: must be 32 characters"
            
            if not re.match(r'^[a-f0-9]{32}$', api_hash):
                return False, "Invalid API Hash: must contain only hexadecimal characters"
            
            # Validate phone number
            if not isinstance(phone_number, str):
                return False, "Invalid phone number: must be a string"
            
            if not re.match(r'^\+[1-9]\d{1,14}$', phone_number):
                return False, "Invalid phone number: must start with + and contain only digits"
            
            return True, "Valid credentials"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def _validate_verification_code(self, code: str) -> Tuple[bool, str]:
        """Validate verification code format"""
        if not isinstance(code, str):
            return False, "Verification code must be a string"
        
        code = code.strip()
        if len(code) < 4 or len(code) > 8:
            return False, "Verification code must be 4-8 characters"
        
        if not code.isdigit():
            return False, "Verification code must contain only digits"
        
        return True, "Valid verification code"
    
    def set_credentials(self, api_id: int, api_hash: str, phone_number: str) -> Tuple[bool, str]:
        """Set userbot credentials with validation"""
        try:
            # Validate credentials
            is_valid, message = self._validate_credentials(api_id, api_hash, phone_number)
            if not is_valid:
                logger.error(f"❌ USERBOT: {message}")
                return False, message
            
            self.api_id = api_id
            self.api_hash = api_hash
            self.phone_number = phone_number
            logger.info(f"✅ USERBOT: Credentials validated and set - API ID: {api_id}, Phone: {phone_number}")
            return True, "Credentials set successfully"
            
        except Exception as e:
            error_msg = f"Error setting credentials: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_code(self, code: str) -> Tuple[bool, str]:
        """Authenticate with verification code and generate session string"""
        try:
            # Validate code
            is_valid, message = self._validate_verification_code(code)
            if not is_valid:
                logger.error(f"❌ USERBOT: {message}")
                return False, message
            
            if not all([self.api_id, self.api_hash, self.phone_number]):
                error_msg = "Credentials not set"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info("📱 USERBOT: Generating session string with verification code...")
            
            # Generate session string
            success, result = await session_generator.generate_session_string(
                self.api_id, 
                self.api_hash, 
                self.phone_number, 
                code.strip()
            )
            
            if success:
                self.session_string = result
                logger.info("✅ USERBOT: Session string generated successfully")
                
                # Initialize client with session string
                init_success, init_message = await self.initialize()
                return init_success, init_message
            else:
                logger.error(f"❌ USERBOT: Session generation failed: {result}")
                return False, result
                
        except Exception as e:
            error_msg = f"Authentication error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_2fa(self, code: str, password: str) -> Tuple[bool, str]:
        """Authenticate with verification code and 2FA password"""
        try:
            # Validate inputs
            is_valid, message = self._validate_verification_code(code)
            if not is_valid:
                return False, message
            
            if not password or len(password.strip()) < 1:
                return False, "2FA password cannot be empty"
            
            if not all([self.api_id, self.api_hash, self.phone_number]):
                error_msg = "Credentials not set"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info("🔐 USERBOT: Generating session string with 2FA...")
            
            # Generate session string with 2FA
            success, result = await session_generator.generate_session_string_with_2fa(
                self.api_id, 
                self.api_hash, 
                self.phone_number, 
                code.strip(),
                password.strip()
            )
            
            if success:
                self.session_string = result
                logger.info("✅ USERBOT: Session string generated with 2FA")
                
                # Initialize client with session string
                init_success, init_message = await self.initialize()
                return init_success, init_message
            else:
                logger.error(f"❌ USERBOT: 2FA session generation failed: {result}")
                return False, result
                
        except Exception as e:
            error_msg = f"2FA authentication error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
        
    async def initialize(self) -> Tuple[bool, str]:
        """Initialize the userbot with session string"""
        try:
            if not self.session_string:
                error_msg = "No session string available - authenticate first"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
            
            if not all([self.api_id, self.api_hash]):
                error_msg = "API credentials not set"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info("🚀 USERBOT: Initializing with session string...")
            
            # Create client with session string
            self.client = Client(
                name=self.session_name,
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
                self.is_authenticated = True
                logger.info(f"✅ USERBOT: Connected as @{me.username or me.first_name}")
                return True, f"Connected as @{me.username or me.first_name}"
            else:
                error_msg = "Failed to get user info"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Initialization error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def _get_user_entity(self, user_id: int) -> Tuple[Optional[Any], str]:
        """Get user entity with proper error handling"""
        try:
            from utils import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT telegram_username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                return None, f"No username found for user {user_id}"
            
            username = user_data[0]
            if not username.startswith('@'):
                username = f"@{username}"
            
            # Get user entity
            try:
                user_entity = await self.client.get_users(username)
                if not user_entity:
                    return None, f"User {username} not found"
                
                return user_entity, "User entity retrieved successfully"
                
            except UsernameNotOccupied:
                return None, f"Username {username} is not occupied"
            except UsernameInvalid:
                return None, f"Invalid username format: {username}"
            except Exception as e:
                return None, f"Error getting user {username}: {e}"
                
        except Exception as e:
            return None, f"Database error: {e}"
    
    async def send_secret_message(self, user_id: int, message: str, media_files: List[str] = None) -> Tuple[bool, str]:
        """Send message through secret chat - simplified approach"""
        try:
            if not self.is_connected or not self.client:
                error_msg = "Userbot not connected"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
            
            if not message or not message.strip():
                error_msg = "Message cannot be empty"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info(f"📨 USERBOT: Sending message to user {user_id}")
            
            # Get user entity
            user_entity, user_msg = await self._get_user_entity(user_id)
            if not user_entity:
                logger.error(f"❌ USERBOT: {user_msg}")
                return False, user_msg
            
            # For now, send as regular message instead of secret chat
            # Secret chats are complex and often fail in server environments
            try:
                # Send media files if any
                if media_files:
                    media_objects = []
                    for media_file in media_files:
                        if os.path.exists(media_file):
                            if media_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                media_objects.append(InputMediaPhoto(media_file))
                            else:
                                media_objects.append(InputMediaDocument(media_file))
                    
                    if media_objects:
                        await self.client.send_media_group(user_entity.id, media_objects)
                        logger.info(f"✅ USERBOT: Sent {len(media_objects)} media files")
                
                # Send text message
                await self.client.send_message(user_entity.id, message)
                logger.info(f"✅ USERBOT: Sent message to user {user_id}")
                return True, "Message sent successfully via userbot"
                
            except Exception as e:
                error_msg = f"Error sending message: {e}"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Error in send_secret_message: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def disconnect(self) -> Tuple[bool, str]:
        """Disconnect the userbot"""
        if self.client and self.is_connected:
            try:
                await self.client.stop()
                self.is_connected = False
                self.is_authenticated = False
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
            'authenticated': self.is_authenticated,
            'has_credentials': all([self.api_id, self.api_hash, self.phone_number]),
            'has_session': bool(self.session_string),
            'session_length': len(self.session_string) if self.session_string else 0
        }

# Global instance
improved_simple_userbot = ImprovedSimpleUserbot()
