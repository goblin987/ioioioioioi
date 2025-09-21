import asyncio
import logging
import os
import random
import re
import hashlib
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

logger = logging.getLogger(__name__)

class SecureUserbot:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.is_authenticated = False
        self.session_name = "secure_userbot"
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.max_retries = 3
        self.retry_delay = 2
        
        # Create secure session directory
        self.session_dir = os.path.join(os.getcwd(), "sessions")
        os.makedirs(self.session_dir, exist_ok=True)
        
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
        
        if len(code) < 4 or len(code) > 8:
            return False, "Verification code must be 4-8 characters"
        
        if not code.isdigit():
            return False, "Verification code must contain only digits"
        
        return True, "Valid verification code"
    
    def _validate_2fa_password(self, password: str) -> Tuple[bool, str]:
        """Validate 2FA password"""
        if not isinstance(password, str):
            return False, "2FA password must be a string"
        
        if len(password) < 6:
            return False, "2FA password must be at least 6 characters"
        
        return True, "Valid 2FA password"
    
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
        
    async def initialize(self) -> Tuple[bool, str]:
        """Initialize the userbot with proper error handling"""
        if not all([self.api_id, self.api_hash, self.phone_number]):
            error_msg = "Credentials not set"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
            
        try:
            logger.info("🚀 USERBOT: Initializing...")
            
            # Create client with secure session path
            session_path = os.path.join(self.session_dir, f"{self.session_name}.session")
            self.client = Client(
                name=self.session_name,
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir=self.session_dir,
                session_string=None
            )
            
            # Try to start with existing session
            try:
                await self.client.start()
                me = await self.client.get_me()
                if me:
                    self.is_connected = True
                    self.is_authenticated = True
                    logger.info(f"✅ USERBOT: Connected with existing session as @{me.username or me.first_name}")
                    return True, "Connected with existing session"
            except Exception as e:
                logger.info(f"🔄 USERBOT: No existing session, need authentication: {e}")
                
            # If no session, we need to authenticate
            logger.info("🔐 USERBOT: Authentication required")
            return False, "Authentication required"
            
        except Exception as e:
            error_msg = f"Initialization error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_code(self, code: str) -> Tuple[bool, str]:
        """Authenticate with verification code"""
        try:
            # Validate code
            is_valid, message = self._validate_verification_code(code)
            if not is_valid:
                logger.error(f"❌ USERBOT: {message}")
                return False, message
            
            if not self.client:
                error_msg = "No client available"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info("📱 USERBOT: Authenticating with code...")
            
            # Create new client with code
            temp_client = Client(
                name=f"{self.session_name}_temp",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir=self.session_dir
            )
            
            # Start with verification code
            await temp_client.start(phone_code=code)
            
            # Verify connection
            me = await temp_client.get_me()
            if me:
                # Stop temp client
                await temp_client.stop()
                
                # Start main client (should use saved session now)
                await self.client.start()
                
                self.is_connected = True
                self.is_authenticated = True
                logger.info(f"✅ USERBOT: Authenticated as @{me.username or me.first_name}")
                return True, "Authentication successful"
            else:
                await temp_client.stop()
                error_msg = "Authentication failed"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
        except PhoneCodeInvalid:
            error_msg = "Invalid verification code"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Authentication error: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def authenticate_with_2fa(self, password: str) -> Tuple[bool, str]:
        """Authenticate with 2FA password"""
        try:
            # Validate password
            is_valid, message = self._validate_2fa_password(password)
            if not is_valid:
                logger.error(f"❌ USERBOT: {message}")
                return False, message
            
            if not self.client:
                error_msg = "No client available"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info("🔐 USERBOT: Authenticating with 2FA...")
            
            # Create new client with 2FA password
            temp_client = Client(
                name=f"{self.session_name}_temp",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir=self.session_dir
            )
            
            # Start with 2FA password
            await temp_client.start(password=password)
            
            # Verify connection
            me = await temp_client.get_me()
            if me:
                # Stop temp client
                await temp_client.stop()
                
                # Start main client (should use saved session now)
                await self.client.start()
                
                self.is_connected = True
                self.is_authenticated = True
                logger.info(f"✅ USERBOT: Authenticated as @{me.username or me.first_name}")
                return True, "2FA authentication successful"
            else:
                await temp_client.stop()
                error_msg = "2FA authentication failed"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"2FA authentication error: {e}"
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
            
            # Get user entity with access_hash
            try:
                user_entity = await self.client.get_users(username)
                if not user_entity:
                    return None, f"User {username} not found"
                
                if not hasattr(user_entity, 'access_hash') or not user_entity.access_hash:
                    return None, f"Cannot get access hash for user {username}"
                
                return user_entity, "User entity retrieved successfully"
                
            except UsernameNotOccupied:
                return None, f"Username {username} is not occupied"
            except UsernameInvalid:
                return None, f"Invalid username format: {username}"
            except Exception as e:
                return None, f"Error getting user {username}: {e}"
                
        except Exception as e:
            return None, f"Database error: {e}"
    
    async def _create_secret_chat(self, user_entity) -> Tuple[Optional[int], str]:
        """Create secret chat with retry logic"""
        for attempt in range(self.max_retries):
            try:
                peer = InputPeerUser(user_id=user_entity.id, access_hash=user_entity.access_hash)
                result = await self.client.invoke(RequestEncryption(
                    user_id=peer,
                    random_id=random.randint(0, 2**63-1)
                ))
                
                if result and hasattr(result, 'chat_id'):
                    logger.info(f"✅ USERBOT: Secret chat created with ID: {result.chat_id}")
                    return result.chat_id, "Secret chat created successfully"
                else:
                    error_msg = "Failed to create secret chat - invalid response"
                    logger.warning(f"⚠️ USERBOT: {error_msg} (attempt {attempt + 1})")
                    
            except FloodWait as e:
                wait_time = e.value
                error_msg = f"Rate limited, waiting {wait_time} seconds"
                logger.warning(f"⚠️ USERBOT: {error_msg} (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                error_msg = f"Error creating secret chat: {e}"
                logger.warning(f"⚠️ USERBOT: {error_msg} (attempt {attempt + 1})")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return None, f"Failed to create secret chat after {self.max_retries} attempts"
    
    async def _send_media_files(self, secret_chat_id: int, media_files: List[str]) -> Tuple[bool, str]:
        """Send media files with proper error handling"""
        if not media_files:
            return True, "No media files to send"
        
        try:
            # Convert file paths to InputMedia objects
            media_objects = []
            for media_file in media_files:
                if os.path.exists(media_file):
                    if media_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        media_objects.append(InputMediaPhoto(media_file))
                    else:
                        media_objects.append(InputMediaDocument(media_file))
                else:
                    logger.warning(f"⚠️ USERBOT: Media file not found: {media_file}")
            
            if media_objects:
                await self.client.send_media_group(secret_chat_id, media_objects)
                logger.info(f"✅ USERBOT: Sent {len(media_objects)} media files to secret chat")
                return True, f"Sent {len(media_objects)} media files"
            else:
                return True, "No valid media files found"
                
        except Exception as e:
            error_msg = f"Error sending media: {e}"
            logger.error(f"❌ USERBOT: {error_msg}")
            return False, error_msg
    
    async def send_secret_message(self, user_id: int, message: str, media_files: List[str] = None) -> Tuple[bool, str]:
        """Send message through secret chat with comprehensive error handling"""
        try:
            if not self.is_connected or not self.client:
                error_msg = "Userbot not connected"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
            
            if not message or not message.strip():
                error_msg = "Message cannot be empty"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
                
            logger.info(f"📨 USERBOT: Sending secret message to user {user_id}")
            
            # Get user entity
            user_entity, user_msg = await self._get_user_entity(user_id)
            if not user_entity:
                logger.error(f"❌ USERBOT: {user_msg}")
                return False, user_msg
            
            # Create secret chat
            secret_chat_id, chat_msg = await self._create_secret_chat(user_entity)
            if not secret_chat_id:
                logger.error(f"❌ USERBOT: {chat_msg}")
                return False, chat_msg
            
            # Send media files if any
            if media_files:
                media_success, media_msg = await self._send_media_files(secret_chat_id, media_files)
                if not media_success:
                    logger.warning(f"⚠️ USERBOT: {media_msg} - continuing with text message")
            
            # Send text message
            try:
                await self.client.send_message(secret_chat_id, message)
                logger.info(f"✅ USERBOT: Sent secret message to user {user_id}")
                return True, "Message sent successfully"
            except Exception as e:
                error_msg = f"Error sending text message: {e}"
                logger.error(f"❌ USERBOT: {error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Error sending secret message: {e}"
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
        session_path = os.path.join(self.session_dir, f"{self.session_name}.session")
        return {
            'connected': self.is_connected,
            'authenticated': self.is_authenticated,
            'has_credentials': all([self.api_id, self.api_hash, self.phone_number]),
            'session_exists': os.path.exists(session_path),
            'session_dir': self.session_dir,
            'max_retries': self.max_retries
        }

# Global instance
secure_userbot = SecureUserbot()
