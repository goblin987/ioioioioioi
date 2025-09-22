"""
Session String Generator for Pyrogram Userbot
Generates session strings for authentication without manual intervention
"""
import asyncio
import logging
import os
from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneNumberInvalid,
    AuthKeyUnregistered
)

logger = logging.getLogger(__name__)

class SessionGenerator:
    def __init__(self):
        self.temp_session_name = "temp_session_gen"
        
    async def generate_session_string(self, api_id: int, api_hash: str, phone_number: str, phone_code: str, password: str = None) -> tuple[bool, str]:
        """
        Generate session string using API credentials and verification code
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone_number: Phone number with country code (e.g., +1234567890)
            phone_code: Verification code from Telegram
            password: 2FA password (optional)
            
        Returns:
            tuple: (success: bool, result: str) - result is session string if success, error message if not
        """
        client = None
        try:
            logger.info("🔑 SESSION: Generating session string...")
            
            # Create temporary client
            client = Client(
                name=self.temp_session_name,
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone_number,
                workdir="temp_sessions"
            )
            
            # Ensure temp directory exists
            os.makedirs("temp_sessions", exist_ok=True)
            
            # Start client with phone code
            await client.start(phone_code=phone_code, password=password)
            
            # Get session string
            session_string = await client.export_session_string()
            
            # Verify the session works
            me = await client.get_me()
            if me:
                logger.info(f"✅ SESSION: Generated for @{me.username or me.first_name}")
                await client.stop()
                
                # Clean up temp files
                self._cleanup_temp_files()
                
                return True, session_string
            else:
                await client.stop()
                self._cleanup_temp_files()
                return False, "Failed to verify session"
                
        except PhoneCodeInvalid:
            error_msg = "Invalid verification code"
            logger.error(f"❌ SESSION: {error_msg}")
            if client:
                await client.stop()
            self._cleanup_temp_files()
            return False, error_msg
            
        except SessionPasswordNeeded:
            error_msg = "2FA password required but not provided"
            logger.error(f"❌ SESSION: {error_msg}")
            if client:
                await client.stop()
            self._cleanup_temp_files()
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Session generation error: {e}"
            logger.error(f"❌ SESSION: {error_msg}")
            if client:
                try:
                    await client.stop()
                except:
                    pass
            self._cleanup_temp_files()
            return False, error_msg
    
    async def generate_session_string_with_2fa(self, api_id: int, api_hash: str, phone_number: str, phone_code: str, password: str) -> tuple[bool, str]:
        """
        Generate session string with 2FA password
        """
        return await self.generate_session_string(api_id, api_hash, phone_number, phone_code, password)
    
    def _cleanup_temp_files(self):
        """Clean up temporary session files"""
        try:
            temp_dir = "temp_sessions"
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        os.remove(file_path)
                        logger.debug(f"🧹 SESSION: Cleaned up {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ SESSION: Could not clean up {file_path}: {e}")
                try:
                    os.rmdir(temp_dir)
                    logger.debug(f"🧹 SESSION: Removed temp directory {temp_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ SESSION: Could not remove temp directory: {e}")
        except Exception as e:
            logger.warning(f"⚠️ SESSION: Cleanup error: {e}")

# Global instance
session_generator = SessionGenerator()
