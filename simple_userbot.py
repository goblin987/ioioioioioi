import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneNumberInvalid,
    FloodWait,
    AuthKeyUnregistered
)

logger = logging.getLogger(__name__)

class SimpleUserbot:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.is_authenticated = False
        self.session_name = "simple_userbot"
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        
    def set_credentials(self, api_id: int, api_hash: str, phone_number: str):
        """Set userbot credentials"""
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        logger.info(f"✅ USERBOT: Credentials set - API ID: {api_id}, Phone: {phone_number}")
        
    async def initialize(self):
        """Initialize the userbot"""
        if not all([self.api_id, self.api_hash, self.phone_number]):
            logger.error("❌ USERBOT: Credentials not set")
            return False
            
        try:
            logger.info("🚀 USERBOT: Initializing...")
            
            # Create client
            self.client = Client(
                name=self.session_name,
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir="."
            )
            
            # Try to start with existing session
            try:
                await self.client.start()
                me = await self.client.get_me()
                if me:
                    self.is_connected = True
                    self.is_authenticated = True
                    logger.info(f"✅ USERBOT: Connected with existing session as @{me.username or me.first_name}")
                    return True
            except Exception as e:
                logger.info(f"🔄 USERBOT: No existing session, need authentication: {e}")
                
            # If no session, we need to authenticate
            logger.info("🔐 USERBOT: Authentication required - please authenticate manually")
            return False
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Initialization error: {e}")
            return False
    
    async def authenticate_with_code(self, code: str):
        """Authenticate with verification code"""
        try:
            if not self.client:
                logger.error("❌ USERBOT: No client available")
                return False
                
            logger.info("📱 USERBOT: Authenticating with code...")
            
            # Create new client with code
            temp_client = Client(
                name=f"{self.session_name}_temp",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir="."
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
                return True
            else:
                await temp_client.stop()
                logger.error("❌ USERBOT: Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ USERBOT: Authentication error: {e}")
            return False
    
    async def authenticate_with_2fa(self, password: str):
        """Authenticate with 2FA password"""
        try:
            if not self.client:
                logger.error("❌ USERBOT: No client available")
                return False
                
            logger.info("🔐 USERBOT: Authenticating with 2FA...")
            
            # Create new client with 2FA password
            temp_client = Client(
                name=f"{self.session_name}_temp",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number,
                workdir="."
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
                return True
            else:
                await temp_client.stop()
                logger.error("❌ USERBOT: 2FA authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ USERBOT: 2FA authentication error: {e}")
            return False
    
    async def send_secret_message(self, user_id: int, message: str, media_files: List[str] = None):
        """Send message through secret chat"""
        try:
            if not self.is_connected or not self.client:
                logger.error("❌ USERBOT: Not connected")
                return False
                
            logger.info(f"📨 USERBOT: Sending secret message to user {user_id}")
            
            # Get user info from database
            from utils import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT telegram_username FROM users WHERE user_id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if not user_data or not user_data[0]:
                logger.error(f"❌ USERBOT: No username found for user {user_id}")
                return False
            
            username = user_data[0]
            if not username.startswith('@'):
                username = f"@{username}"
            
            # Get user entity
            user_entity = await self.client.get_users(username)
            if not user_entity:
                logger.error(f"❌ USERBOT: User {username} not found")
                return False
            
            # Create secret chat
            secret_chat = await self.client.create_secret_chat(user_entity.id)
            if not secret_chat:
                logger.error(f"❌ USERBOT: Failed to create secret chat with user {user_id}")
                return False
            
            # Send message
            if media_files:
                # Send media group
                media_group = []
                for media_file in media_files:
                    if os.path.exists(media_file):
                        media_group.append(media_file)
                
                if media_group:
                    await self.client.send_media_group(secret_chat.id, media_group)
                    logger.info(f"✅ USERBOT: Sent {len(media_group)} media files to secret chat")
            
            # Send text message
            await self.client.send_message(secret_chat.id, message)
            logger.info(f"✅ USERBOT: Sent secret message to user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ USERBOT: Error sending secret message: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect the userbot"""
        if self.client and self.is_connected:
            try:
                await self.client.stop()
                self.is_connected = False
                self.is_authenticated = False
                logger.info("✅ USERBOT: Disconnected")
            except Exception as e:
                logger.error(f"❌ USERBOT: Error disconnecting: {e}")
    
    def get_status(self):
        """Get userbot status"""
        return {
            'connected': self.is_connected,
            'authenticated': self.is_authenticated,
            'has_credentials': all([self.api_id, self.api_hash, self.phone_number]),
            'session_exists': os.path.exists(f"{self.session_name}.session")
        }

# Global instance
simple_userbot = SimpleUserbot()
