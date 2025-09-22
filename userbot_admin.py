"""
Simple Userbot Admin Interface
Clean and focused on the core workflow
"""
import logging
import asyncio
import os
import base64
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from userbot_telethon import telethon_userbot as userbot
from utils import is_any_admin

logger = logging.getLogger(__name__)

# Session storage for userbot authentication
user_sessions = {}

async def handle_userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show userbot status"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        status = userbot.get_status()
        
        # Build status message
        status_text = "🤖 **TELETHON SECRET CHAT USERBOT STATUS**\n\n"
        
        if userbot.has_session:
            if userbot.is_connected:
                status_text += f"🟢 **CONNECTED & READY**\n"
                status_text += f"📱 Phone: {userbot.phone_number}\n"
                status_text += f"🔐 Session: Active (Telethon)\n"
                status_text += f"🎯 Mode: SECRET CHAT DELIVERY\n\n"
                status_text += f"✅ Products will be delivered via ENCRYPTED SECRET CHATS\n"
                status_text += f"🔒 Maximum security and privacy for customers"
            else:
                status_text += f"🟡 **CONFIGURED BUT DISCONNECTED**\n"
                status_text += f"📱 Phone: {userbot.phone_number}\n"
                status_text += f"🔐 Session: Available (Telethon)\n"
                status_text += f"⚠️ Connection: Not active\n\n"
                status_text += f"🔄 Use 'Connect Userbot' to establish connection"
        else:
            status_text += f"🔴 **NOT CONFIGURED**\n"
            status_text += f"❌ No session available\n"
            status_text += f"🔧 Authentication required\n\n"
            status_text += f"👆 Use 'Set Credentials' to authenticate with Telegram"
        
        # Build keyboard based on status
        keyboard = []
        
        if userbot.has_session:
            if userbot.is_connected:
                keyboard.extend([
                    [InlineKeyboardButton("🔄 Disconnect", callback_data="userbot_disconnect")],
                    [InlineKeyboardButton("🧪 Test Delivery", callback_data="userbot_test")]
                ])
            else:
                keyboard.extend([
                    [InlineKeyboardButton("🔌 Connect Userbot", callback_data="userbot_connect")],
                    [InlineKeyboardButton("🔧 Set New Credentials", callback_data="userbot_set_credentials")]
                ])
        else:
            keyboard.append([InlineKeyboardButton("🔧 Set Credentials", callback_data="userbot_set_credentials")])
        
        # Always show clear config option
        keyboard.append([InlineKeyboardButton("🗑️ Clear Configuration", callback_data="userbot_clear_config")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")])
        
        await update.callback_query.edit_message_text(
            text=status_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=None
        )
        
    except Exception as e:
        logger.error(f"Error showing userbot status: {e}")
        await update.callback_query.answer("❌ Error loading status")

async def handle_userbot_set_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start userbot credential setup"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        user_id = update.effective_user.id
        
        # Initialize session for this user
        user_sessions[user_id] = {
            'step': 'api_id',
            'account_data': {}
        }
        
        await update.callback_query.edit_message_text(
            "🔧 **TELETHON SECRET CHAT USERBOT SETUP**\n\n"
            "Let's configure your userbot for ENCRYPTED SECRET CHAT delivery!\n\n"
            "📋 **Step 1: API ID**\n\n"
            "Please enter your Telegram API ID:\n"
            "• Get it from: https://my.telegram.org/apps\n"
            "• Create a new application if needed\n"
            "• Copy the 'App api_id' number",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
            ]]),
            parse_mode=None
        )
        
        logger.info(f"✅ USERBOT ADMIN: Started credential setup for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error starting credential setup: {e}")
        await update.callback_query.answer("❌ Error starting setup")

async def handle_userbot_verification_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification code input"""
    user_id = update.effective_user.id
    
    if not is_any_admin(user_id):
        return
    
    if user_id not in user_sessions or user_sessions[user_id].get('step') != 'verification_code':
        return
    
    message_text = update.message.text.strip()
    session = user_sessions[user_id]
    
    logger.info(f"🔍 USERBOT SESSION: User {user_id}, step: verification_code, message: {message_text}")
    
    try:
        client = session.get('client')
        if not client:
            await update.message.reply_text("❌ Session expired. Please start over.")
            if user_id in user_sessions:
                del user_sessions[user_id]
            return
        
        try:
            from telethon.errors import SessionPasswordNeededError
            
            # Sign in with the code using Telethon
            phone = session['account_data']['phone_number']
            
            # Sign in with Telethon (different API than Pyrogram)
            me = await client.sign_in(phone, message_text)
            
            logger.info(f"✅ Successfully authenticated as {me.first_name} ({me.phone})")
            
            # Export session string (Telethon format for SECRET CHAT support!)
            session_string = client.session.save()
            
            # Set credentials in our Telethon secret chat userbot
            api_id = int(session['account_data']['api_id'])
            api_hash = session['account_data']['api_hash']
            
            userbot.set_credentials(api_id, api_hash, phone, session_string)
            
            # Connect the userbot for immediate use
            connect_success, connect_message = await userbot.connect()
            if connect_success:
                await update.message.reply_text(
                    "✅ **AUTHENTICATION & CONNECTION SUCCESSFUL!**\n\n"
                    f"Authenticated as: {me.first_name}\n"
                    f"Phone: {me.phone}\n"
                    f"Status: {connect_message}\n\n"
                    "🔐 **TELETHON SECRET CHAT USERBOT READY!**\n"
                    "• Products delivered via ENCRYPTED SECRET CHATS\n"
                    "• Maximum security and privacy\n"
                    "• Automatic delivery after payment\n"
                    "• No manual intervention needed",
                    parse_mode=None,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                    ]])
                )
            else:
                await update.message.reply_text(
                    "✅ **AUTHENTICATION SUCCESSFUL!**\n"
                    "⚠️ **CONNECTION ISSUE**\n\n"
                    f"Authenticated as: {me.first_name}\n"
                    f"Connection error: {connect_message}\n\n"
                    "🔧 **Manual connection needed**\n"
                    "• Use 'Connect Userbot' button to retry\n"
                    "• Check userbot status in admin panel",
                    parse_mode=None,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                    ]])
                )
            
            # Disconnect client and cleanup
            await client.disconnect()
            
            # Clear session
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except SessionPasswordNeededError:
            # 2FA required
            session['step'] = '2fa_password'
            await update.message.reply_text(
                "🔐 **2FA Required**\n\n"
                "Your account has Two-Factor Authentication enabled.\n\n"
                "Please enter your 2FA password:",
                parse_mode=None
            )
            
    except Exception as e:
        logger.error(f"Failed to authenticate with code: {e}")
        if user_id in user_sessions:
            del user_sessions[user_id]
        await update.message.reply_text(
            f"❌ Authentication Failed\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check your verification code and try again.",
            parse_mode=None
        )

async def handle_userbot_2fa_password_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 2FA password input"""
    user_id = update.effective_user.id
    
    if not is_any_admin(user_id):
        return
    
    if user_id not in user_sessions or user_sessions[user_id].get('step') != '2fa_password':
        return
    
    password = update.message.text.strip()
    session = user_sessions[user_id]
    
    logger.info(f"🔍 USERBOT SESSION: User {user_id}, step: 2fa_password")
    
    try:
        client = session.get('client')
        if not client:
            await update.message.reply_text("❌ Session expired. Please start over.")
            if user_id in user_sessions:
                del user_sessions[user_id]
            return
        
        try:
            # Check password with Telethon
            me = await client.sign_in(password=password)
            
            logger.info(f"✅ 2FA authentication successful for {me.first_name}")
            
            # Export session string (Telethon format for SECRET CHAT support!)
            session_string = client.session.save()
            
            # Set credentials in our Telethon secret chat userbot
            api_id = int(session['account_data']['api_id'])
            api_hash = session['account_data']['api_hash']
            phone = session['account_data']['phone_number']
            
            userbot.set_credentials(api_id, api_hash, phone, session_string)
            
            # Connect the userbot for immediate use
            connect_success, connect_message = await userbot.connect()
            if connect_success:
                await update.message.reply_text(
                    "✅ **2FA AUTHENTICATION & CONNECTION SUCCESSFUL!**\n\n"
                    f"Authenticated as: {me.first_name}\n"
                    f"Phone: {me.phone}\n"
                    f"Status: {connect_message}\n\n"
                    "🔐 **TELETHON SECRET CHAT USERBOT READY!**\n"
                    "• Products delivered via ENCRYPTED SECRET CHATS\n"
                    "• Maximum security and privacy\n"
                    "• Automatic delivery after payment\n"
                    "• No manual intervention needed",
                    parse_mode=None,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                    ]])
                )
            else:
                await update.message.reply_text(
                    "✅ **2FA AUTHENTICATION SUCCESSFUL!**\n"
                    "⚠️ **CONNECTION ISSUE**\n\n"
                    f"Authenticated as: {me.first_name}\n"
                    f"Connection error: {connect_message}\n\n"
                    "🔧 **Manual connection needed**\n"
                    "• Use 'Connect Userbot' button to retry\n"
                    "• Check userbot status in admin panel",
                    parse_mode=None,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                    ]])
                )
            
            # Disconnect client and cleanup
            await client.disconnect()
            
            # Clear session
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as pwd_error:
            logger.error(f"2FA password error: {pwd_error}")
            await update.message.reply_text(
                f"❌ 2FA Authentication Failed\n\n"
                f"Error: {str(pwd_error)}\n\n"
                f"Please check your 2FA password and try again.",
                parse_mode=None
            )
            
            # Clear session on error
            if user_id in user_sessions:
                del user_sessions[user_id]
                
    except Exception as e:
        logger.error(f"Error processing 2FA password: {e}")
        await update.message.reply_text("Error processing your message.")

# Handle other userbot session steps
async def handle_userbot_session_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle userbot authentication session messages"""
    user_id = update.effective_user.id
    
    if not is_any_admin(user_id):
        return
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    step = session.get('step')
    message_text = update.message.text.strip()
    
    logger.info(f"🔍 USERBOT SESSION: User {user_id}, step: {step}, message: {message_text}")
    
    try:
        if step == 'api_id':
            # Validate API ID
            try:
                api_id = int(message_text)
                session['account_data']['api_id'] = api_id
                session['step'] = 'api_hash'
                
                await update.message.reply_text(
                    "✅ **API ID Saved**\n\n"
                    "📋 **Step 2: API Hash**\n\n"
                    "Please enter your Telegram API Hash:\n"
                    "• Get it from: https://my.telegram.org/apps\n"
                    "• Copy the 'App api_hash' string\n"
                    "• It should be a long string of letters and numbers",
                    parse_mode=None
                )
                
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid API ID**\n\n"
                    "Please enter a valid numeric API ID.\n"
                    "Example: 12345678",
                    parse_mode=None
                )
        
        elif step == 'api_hash':
            # Validate API Hash
            if len(message_text) < 10 or not re.match(r'^[a-f0-9]+$', message_text):
                await update.message.reply_text(
                    "❌ **Invalid API Hash**\n\n"
                    "Please enter a valid API Hash.\n"
                    "It should be a long string of letters and numbers.",
                    parse_mode=None
                )
                return
            
            session['account_data']['api_hash'] = message_text
            session['step'] = 'phone_number'
            
            await update.message.reply_text(
                "✅ **API Hash Saved**\n\n"
                "📋 **Step 3: Phone Number**\n\n"
                "Please enter your phone number:\n"
                "• Include country code (e.g., +1234567890)\n"
                "• This must be the phone number of your Telegram account",
                parse_mode=None
            )
        
        elif step == 'phone_number':
            # Validate phone number
            if not message_text.startswith('+') or len(message_text) < 8:
                await update.message.reply_text(
                    "❌ **Invalid Phone Number**\n\n"
                    "Please enter a valid phone number with country code.\n"
                    "Example: +1234567890",
                    parse_mode=None
                )
                return
            
            session['account_data']['phone_number'] = message_text
            
            # Now authenticate with Telegram to create a session
            await update.message.reply_text(
                "🔐 **Authenticating with Telegram...**\n\n"
                "Please wait while I connect to your account...",
                parse_mode=None
            )
            
            # Create session for this account using Telethon (SECRET CHAT SUPPORT!)
            from telethon import TelegramClient
            
            try:
                api_id = int(session['account_data']['api_id'])
                api_hash = session['account_data']['api_hash']
                phone = session['account_data']['phone_number']
                
                # Create a unique session name for Telethon
                session_name = f"telethon_userbot_{user_id}_{int(asyncio.get_event_loop().time())}"
                client = TelegramClient(session_name, api_id, api_hash)
                
                await client.connect()
                
                # Request verification code using Telethon
                sent_code = await client.send_code_request(phone)
                session['phone_code_hash'] = sent_code.phone_code_hash
                
                session['client'] = client
                session['session_name'] = session_name
                session['step'] = 'verification_code'
                
                await update.message.reply_text(
                    "📱 **Verification Code Sent!**\n\n"
                    f"A verification code has been sent to **{phone}**\n\n"
                    "Please enter the verification code you received:",
                    parse_mode=None
                )
                
            except Exception as e:
                logger.error(f"Failed to start authentication: {e}")
                if user_id in user_sessions:
                    del user_sessions[user_id]
                await update.message.reply_text(
                    f"❌ Authentication Failed\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please check your API credentials and try again.",
                    parse_mode=None
                )
        
        elif step == 'verification_code':
            await handle_userbot_verification_code_message(update, context)
        
        elif step == '2fa_password':
            await handle_userbot_2fa_password_message(update, context)
            
    except Exception as e:
        logger.error(f"Error processing userbot session message: {e}")
        await update.message.reply_text("Error processing your message.")

async def handle_userbot_connect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Connect userbot"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        if not userbot.has_session:
            await update.callback_query.answer("❌ No session available - authenticate first")
            return
        
        success, message = await userbot.connect()
        
        if success:
            await update.callback_query.answer("✅ Userbot connected successfully!")
            await handle_userbot_status(update, context)
        else:
            await update.callback_query.answer(f"❌ Connection failed: {message}")
            
    except Exception as e:
        logger.error(f"Error connecting userbot: {e}")
        await update.callback_query.answer("❌ Error connecting userbot")

async def handle_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Disconnect userbot"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        await userbot.disconnect()
        await update.callback_query.answer("✅ Userbot disconnected")
        await handle_userbot_status(update, context)
        
    except Exception as e:
        logger.error(f"Error disconnecting userbot: {e}")
        await update.callback_query.answer("❌ Error disconnecting userbot")

async def handle_userbot_test(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Test userbot delivery"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        if not userbot.is_connected:
            await update.callback_query.answer("❌ Userbot not connected")
            return
        
        # Test with admin user
        admin_id = update.effective_user.id
        test_product = {
            'product_name': 'Test Product',
            'product_type': 'test',
            'city': 'Test City',
            'district': 'Test District',
            'size': '1g',
            'price': '0.01'
        }
        
        success, message = await userbot.send_product_to_user(admin_id, test_product)
        
        if success:
            await update.callback_query.answer("✅ Test delivery successful! Check your secret chat.")
        else:
            await update.callback_query.answer(f"❌ Test failed: {message}")
            
    except Exception as e:
        logger.error(f"Error testing userbot: {e}")
        await update.callback_query.answer("❌ Error testing userbot")

async def handle_userbot_clear_config(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Clear userbot configuration"""
    if not is_any_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Admin access required")
        return
    
    try:
        success, message = userbot.clear_configuration()
        
        if success:
            await update.callback_query.answer("✅ Configuration cleared successfully")
            await handle_userbot_status(update, context)
        else:
            await update.callback_query.answer(f"❌ Error clearing configuration: {message}")
            
    except Exception as e:
        logger.error(f"Error clearing userbot configuration: {e}")
        await update.callback_query.answer("❌ Error clearing configuration")
