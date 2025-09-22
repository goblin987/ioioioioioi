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
from userbot import userbot

logger = logging.getLogger(__name__)

# Session storage for userbot authentication
user_sessions = {}

async def handle_userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show userbot status"""
    try:
        status = userbot.get_status()
        
        # Build status message
        status_text = "🤖 **USERBOT STATUS**\n\n"
        
        # Connection status
        if status['connected']:
            status_text += "🟢 **Status**: Connected & Ready\n"
        else:
            status_text += "🔴 **Status**: Disconnected\n"
        
        # Credentials status
        if status['has_credentials']:
            status_text += f"✅ **Phone**: {status['phone_number']}\n"
        else:
            status_text += "❌ **Credentials**: Not Set\n"
        
        # Session status
        if status['has_session']:
            status_text += "📱 **Session**: Active\n"
        else:
            status_text += "📱 **Session**: Not Available\n"
        
        # Create buttons based on status
        keyboard = []
        
        if not status['has_credentials']:
            keyboard.append([InlineKeyboardButton("⚙️ Set Credentials", callback_data="userbot_set_credentials")])
        elif not status['connected']:
            if status['has_session']:
                keyboard.append([InlineKeyboardButton("🔌 Connect", callback_data="userbot_connect")])
            else:
                keyboard.append([InlineKeyboardButton("🔐 Authenticate", callback_data="userbot_authenticate")])
                keyboard.append([InlineKeyboardButton("🔐 Authenticate with 2FA", callback_data="userbot_authenticate_2fa")])
        else:
            keyboard.append([InlineKeyboardButton("🔌 Disconnect", callback_data="userbot_disconnect")])
            keyboard.append([InlineKeyboardButton("🧪 Test Delivery", callback_data="userbot_test")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")])
        
        await update.callback_query.edit_message_text(
            status_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing status: {e}")
        await update.callback_query.answer("Error showing status", show_alert=True)

async def handle_userbot_set_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start credential setup process"""
    try:
        await update.callback_query.answer("Setting up credentials...")
        
        user_id = update.effective_user.id
        
        # Initialize session for this user
        user_sessions[user_id] = {
            "step": "api_id",
            "account_data": {}
        }
        
        await update.callback_query.edit_message_text(
            "⚙️ **SET USERBOT CREDENTIALS**\n\n"
            "**Step 1/3: Send your API ID**\n\n"
            "Get it from: https://my.telegram.org\n"
            "• Go to 'API development tools'\n"
            "• Create a new application\n"
            "• Copy your API ID\n\n"
            "Example: 12345678",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="userbot_status")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"✅ USERBOT ADMIN: Started credential setup for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error setting credentials: {e}")
        await update.callback_query.answer("Error setting credentials", show_alert=True)

async def handle_userbot_authenticate(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start authentication process"""
    try:
        await update.callback_query.answer("Starting authentication...")
        
        await update.callback_query.edit_message_text(
            "🔐 **AUTHENTICATION**\n\n"
            "Check your phone for a verification code from Telegram.\n\n"
            "Send the code as a message to this bot.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
            ]])
        )
        
        context.user_data['awaiting_userbot_verification_code'] = True
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error starting authentication: {e}")
        await update.callback_query.answer("Error starting authentication", show_alert=True)

async def handle_userbot_authenticate_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start 2FA authentication process"""
    try:
        await update.callback_query.answer("Starting 2FA authentication...")
        
        await update.callback_query.edit_message_text(
            "🔐 **2FA AUTHENTICATION**\n\n"
            "Step 1: Check your phone for a verification code.\n\n"
            "Send the verification code as a message to this bot.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
            ]])
        )
        
        context.user_data['awaiting_userbot_2fa_code'] = True
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error starting 2FA authentication: {e}")
        await update.callback_query.answer("Error starting 2FA authentication", show_alert=True)

async def handle_userbot_connect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Connect userbot"""
    try:
        await update.callback_query.answer("Connecting...")
        
        success, message = await userbot.connect()
        
        if success:
            await update.callback_query.edit_message_text(
                f"✅ **USERBOT CONNECTED!**\n\n{message}\n\nThe userbot is ready to deliver products.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        else:
            await update.callback_query.edit_message_text(
                f"❌ **CONNECTION FAILED**\n\n{message}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="userbot_connect"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error connecting: {e}")
        await update.callback_query.answer("Error connecting", show_alert=True)

async def handle_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Disconnect userbot"""
    try:
        await update.callback_query.answer("Disconnecting...")
        
        success, message = await userbot.disconnect()
        
        await update.callback_query.edit_message_text(
            f"✅ **USERBOT DISCONNECTED**\n\n{message}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error disconnecting: {e}")
        await update.callback_query.answer("Error disconnecting", show_alert=True)

async def handle_userbot_test(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Test userbot delivery"""
    try:
        await update.callback_query.answer("Testing delivery...")
        
        # Test product data
        test_product = {
            'product_name': 'Test Product',
            'product_type': 'Test Type',
            'city': 'Test City',
            'district': 'Test District',
            'size': 'Medium',
            'price': '10.00'
        }
        
        admin_id = update.effective_user.id
        success, message = await userbot.send_product_to_user(admin_id, test_product)
        
        if success:
            await update.callback_query.edit_message_text(
                "✅ **TEST SUCCESSFUL!**\n\nCheck your messages for the test product delivery.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        else:
            await update.callback_query.edit_message_text(
                f"❌ **TEST FAILED**\n\n{message}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error testing: {e}")
        await update.callback_query.answer("Error testing", show_alert=True)

# Message handlers for credential setup
async def handle_userbot_api_id_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API ID input"""
    try:
        logger.info(f"🔍 USERBOT ADMIN: Processing API ID from user {update.effective_user.id}")
        api_id_text = update.message.text.strip()
        logger.info(f"🔍 USERBOT ADMIN: Received API ID text: {api_id_text}")
        
        try:
            api_id = int(api_id_text)
            context.user_data['temp_api_id'] = api_id
            context.user_data.pop('awaiting_userbot_api_id', None)
            context.user_data['awaiting_userbot_api_hash'] = True
            
            logger.info(f"✅ USERBOT ADMIN: API ID {api_id} saved, awaiting API Hash")
            
            await update.message.reply_text(
                "✅ API ID saved!\n\n"
                "Step 2/3: Send your API Hash:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="userbot_status")
                ]])
            )
        except ValueError:
            logger.warning(f"❌ USERBOT ADMIN: Invalid API ID format: {api_id_text}")
            await update.message.reply_text("❌ Invalid API ID. Please send a number only.")
            
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling API ID: {e}")
        await update.message.reply_text("❌ Error processing API ID. Please try again.")

async def handle_userbot_api_hash_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API Hash input"""
    try:
        api_hash = update.message.text.strip()
        context.user_data['temp_api_hash'] = api_hash
        context.user_data.pop('awaiting_userbot_api_hash', None)
        context.user_data['awaiting_userbot_phone'] = True
        
        await update.message.reply_text(
            "✅ API Hash saved!\n\n"
            "Step 3/3: Send your phone number with country code:\n\n"
            "Example: +1234567890",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling API Hash: {e}")
        await update.message.reply_text("❌ Error processing API Hash. Please try again.")

async def handle_userbot_phone_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    try:
        phone = update.message.text.strip()
        
        # Set credentials
        api_id = context.user_data.get('temp_api_id')
        api_hash = context.user_data.get('temp_api_hash')
        
        success, message = userbot.set_credentials(api_id, api_hash, phone)
        
        # Clean up temp data
        context.user_data.pop('awaiting_userbot_phone', None)
        context.user_data.pop('temp_api_id', None)
        context.user_data.pop('temp_api_hash', None)
        
        if success:
            await update.message.reply_text(
                "✅ **CREDENTIALS SAVED!**\n\nNow you can authenticate the userbot.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔐 Authenticate", callback_data="userbot_authenticate"),
                    InlineKeyboardButton("🔐 Authenticate with 2FA", callback_data="userbot_authenticate_2fa"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        else:
            await update.message.reply_text(f"❌ **ERROR**: {message}")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling phone: {e}")
        await update.message.reply_text("❌ Error processing phone number. Please try again.")

async def handle_userbot_verification_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification code input"""
    try:
        code = update.message.text.strip()
        context.user_data.pop('awaiting_userbot_verification_code', None)
        
        success, message = await userbot.authenticate_with_code(code)
        
        if success:
            await update.message.reply_text(
                f"✅ **AUTHENTICATION SUCCESSFUL!**\n\n{message}\n\nThe userbot is ready to deliver products.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        else:
            await update.message.reply_text(
                f"❌ **AUTHENTICATION FAILED**\n\n{message}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="userbot_authenticate"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling verification code: {e}")
        await update.message.reply_text("❌ Error processing verification code. Please try again.")

async def handle_userbot_2fa_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 2FA verification code input"""
    try:
        code = update.message.text.strip()
        context.user_data.pop('awaiting_userbot_2fa_code', None)
        context.user_data['awaiting_userbot_2fa_password'] = True
        context.user_data['temp_2fa_code'] = code
        
        await update.message.reply_text(
            "📱 **CODE RECEIVED!**\n\n"
            "Step 2: Now send your 2FA password (Cloud Password):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling 2FA code: {e}")
        await update.message.reply_text("❌ Error processing 2FA code. Please try again.")

async def handle_userbot_2fa_password_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 2FA password input"""
    try:
        password = update.message.text.strip()
        code = context.user_data.get('temp_2fa_code')
        
        context.user_data.pop('awaiting_userbot_2fa_password', None)
        context.user_data.pop('temp_2fa_code', None)
        
        if not code:
            await update.message.reply_text("❌ Session expired. Please start authentication again.")
            return
        
        success, message = await userbot.authenticate_with_2fa(code, password)
        
        if success:
            await update.message.reply_text(
                f"✅ **2FA AUTHENTICATION SUCCESSFUL!**\n\n{message}\n\nThe userbot is ready to deliver products.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        else:
            await update.message.reply_text(
                f"❌ **2FA AUTHENTICATION FAILED**\n\n{message}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="userbot_authenticate_2fa"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling 2FA password: {e}")
        await update.message.reply_text("❌ Error processing 2FA password. Please try again.")

async def handle_userbot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages for userbot authentication (session-based)"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    message_text = update.message.text.strip() if update.message.text else ""
    
    logger.info(f"🔍 USERBOT SESSION: User {user_id}, step: {session.get('step', 'unknown')}, message: {message_text}")
    
    try:
        # Handle account authentication steps
        if session['step'] == 'api_id':
            # Validate API ID (should be numeric)
            if not message_text.isdigit():
                await update.message.reply_text(
                    "❌ **Invalid API ID**\n\nAPI ID must be a number. Please enter a valid API ID.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            try:
                api_id = int(message_text)
                if api_id <= 0:
                    raise ValueError("API ID must be positive")
                
                session['account_data']['api_id'] = str(api_id)
                session['step'] = 'api_hash'
                
                await update.message.reply_text(
                    "✅ **API ID set!**\n\n**Step 2/3: API Hash**\n\nPlease send me the API Hash for this account.\n\n**Get it from:** https://my.telegram.org (same page as API ID)",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid API ID!**\n\nPlease send a valid numeric API ID from https://my.telegram.org",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif session['step'] == 'api_hash':
            # Validate API Hash format (should be alphanumeric, 32 characters)
            if not re.match(r'^[a-f0-9]{32}$', message_text.lower()):
                await update.message.reply_text(
                    "❌ **Invalid API Hash**\n\nAPI Hash must be 32 characters long and contain only letters and numbers.\n\nPlease enter a valid API Hash from https://my.telegram.org",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            session['account_data']['api_hash'] = message_text
            session['step'] = 'phone_number'
            
            await update.message.reply_text(
                "✅ **API Hash set!**\n\n**Step 3/3: Phone Number**\n\nPlease send me your phone number with country code.\n\n**Example:** +1234567890",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif session['step'] == 'phone_number':
            # Validate phone number format
            phone_pattern = r'^\+?[1-9]\d{1,14}$'
            if not re.match(phone_pattern, message_text.replace(' ', '').replace('-', '')):
                await update.message.reply_text(
                    "❌ **Invalid Phone Number**\n\nPlease enter a valid phone number with country code (e.g., +1234567890).",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            session['account_data']['phone_number'] = message_text
            session['step'] = 'authenticating'
            
            # Now authenticate with Telegram to create a session
            await update.message.reply_text(
                "🔐 **Authenticating with Telegram...**\n\n"
                "Please wait while I connect to your account...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Create session for this account using Pyrogram (compatible with our userbot)
            from pyrogram import Client
            
            try:
                api_id = int(session['account_data']['api_id'])
                api_hash = session['account_data']['api_hash']
                phone = session['account_data']['phone_number']
                
                # Create a unique session name
                session_name = f"userbot_{user_id}_{int(asyncio.get_event_loop().time())}"
                client = Client(session_name, api_id=api_id, api_hash=api_hash)
                
                await client.connect()
                
                # Request verification code
                sent_code = await client.send_code(phone)
                session['phone_code_hash'] = sent_code.phone_code_hash
                
                session['client'] = client
                session['session_name'] = session_name
                session['step'] = 'verification_code'
                
                await update.message.reply_text(
                    "📱 **Verification Code Sent!**\n\n"
                    f"A verification code has been sent to **{phone}**\n\n"
                    "Please enter the verification code you received:",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                logger.error(f"Failed to start authentication: {e}")
                if user_id in user_sessions:
                    del user_sessions[user_id]
                await update.message.reply_text(
                    f"❌ **Authentication Failed**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please check your API credentials and try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif session['step'] == 'verification_code':
            # Handle verification code
            code = message_text.strip()
            client = session.get('client')
            
            if not client:
                await update.message.reply_text("❌ Session expired. Please start over.")
                if user_id in user_sessions:
                    del user_sessions[user_id]
                return
            
            try:
                from pyrogram.errors import SessionPasswordNeeded
                
                # Sign in with the code using Pyrogram
                phone = session['account_data']['phone_number']
                phone_code_hash = session.get('phone_code_hash')
                
                # This is the correct way to handle Pyrogram sign_in
                signed_in = await client.sign_in(phone, phone_code_hash, code)
                
                # Get user info
                me = await client.get_me()
                logger.info(f"✅ Successfully authenticated as {me.first_name} ({me.phone_number})")
                
                # Export session string (Pyrogram format - compatible with our userbot!)
                session_string = await client.export_session_string()
                
                # Set credentials in our userbot
                api_id = int(session['account_data']['api_id'])
                api_hash = session['account_data']['api_hash']
                
                success, message = userbot.set_credentials(api_id, api_hash, phone)
                
                if success:
                    # Store session string in userbot
                    userbot.session_string = session_string
                    userbot.has_session = True
                    userbot._save_configuration()  # Persist the configuration
                    
                    # Connect the userbot for immediate use
                    connect_success, connect_message = await userbot.connect()
                    if connect_success:
                        await update.message.reply_text(
                            "✅ **AUTHENTICATION & CONNECTION SUCCESSFUL!**\n\n"
                            f"Authenticated as: **{me.first_name}**\n"
                            f"Phone: **{me.phone_number}**\n"
                            f"Status: **{connect_message}**\n\n"
                            "🎯 **Your userbot is ready!**\n"
                            "• Products will be delivered via direct message\n"
                            "• Automatic delivery after payment\n"
                            "• No manual intervention needed",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                            ]])
                        )
                    else:
                        await update.message.reply_text(
                            "✅ **AUTHENTICATION SUCCESSFUL!**\n"
                            "⚠️ **CONNECTION ISSUE**\n\n"
                            f"Authenticated as: **{me.first_name}**\n"
                            f"Connection error: **{connect_message}**\n\n"
                            "🔧 **Manual connection needed**\n"
                            "• Use 'Connect Userbot' button to retry\n"
                            "• Check userbot status in admin panel",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                            ]])
                        )
                else:
                    await update.message.reply_text(f"❌ Error setting credentials: {message}")
                
                # Disconnect client and cleanup
                await client.disconnect()
                
                # Clear session
                if user_id in user_sessions:
                    del user_sessions[user_id]
                
            except SessionPasswordNeeded:
                # 2FA required
                session['step'] = '2fa_password'
                await update.message.reply_text(
                    "🔐 **2FA Required**\n\n"
                    "Your account has Two-Factor Authentication enabled.\n\n"
                    "Please send your 2FA password (Cloud Password):",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to authenticate with code: {e}")
                await update.message.reply_text(
                    f"❌ **Authentication Failed**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please check your verification code and try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif session['step'] == '2fa_password':
            # Handle 2FA password
            password = message_text.strip()
            client = session.get('client')
            
            if not client:
                await update.message.reply_text("❌ Session expired. Please start over.")
                if user_id in user_sessions:
                    del user_sessions[user_id]
                return
            
            try:
                # Check password with Pyrogram
                await client.check_password(password)
                
                # Get user info
                me = await client.get_me()
                logger.info(f"✅ 2FA authentication successful for {me.first_name}")
                
                # Export session string (Pyrogram format - compatible with our userbot!)
                session_string = await client.export_session_string()
                
                # Set credentials in our userbot
                api_id = int(session['account_data']['api_id'])
                api_hash = session['account_data']['api_hash']
                phone = session['account_data']['phone_number']
                
                success, message = userbot.set_credentials(api_id, api_hash, phone)
                
                if success:
                    # Store session string in userbot
                    userbot.session_string = session_string
                    userbot.has_session = True
                    userbot._save_configuration()  # Persist the configuration
                    
                    # Connect the userbot for immediate use
                    connect_success, connect_message = await userbot.connect()
                    if connect_success:
                        await update.message.reply_text(
                            "✅ **2FA AUTHENTICATION & CONNECTION SUCCESSFUL!**\n\n"
                            f"Authenticated as: **{me.first_name}**\n"
                            f"Phone: **{me.phone_number}**\n"
                            f"Status: **{connect_message}**\n\n"
                            "🎯 **Your userbot is ready!**\n"
                            "• Products will be delivered via secret chat\n"
                            "• Direct messages to customers after payment\n"
                            "• No manual intervention needed",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                            ]])
                        )
                    else:
                        await update.message.reply_text(
                            "✅ **2FA AUTHENTICATION SUCCESSFUL!**\n"
                            "⚠️ **CONNECTION ISSUE**\n\n"
                            f"Authenticated as: **{me.first_name}**\n"
                            f"Connection error: **{connect_message}**\n\n"
                            "🔧 **Manual connection needed**\n"
                            "• Use 'Connect Userbot' button to retry\n"
                            "• Check userbot status in admin panel",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")
                            ]])
                        )
                else:
                    await update.message.reply_text(f"❌ Error setting credentials: {message}")
                
                # Disconnect client and cleanup
                await client.disconnect()
                
                # Clear session
                if user_id in user_sessions:
                    del user_sessions[user_id]
                
            except Exception as e:
                logger.error(f"2FA authentication failed: {e}")
                await update.message.reply_text(
                    f"❌ **2FA Authentication Failed**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please check your 2FA password and try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
    
    except Exception as e:
        logger.error(f"Error in userbot message handler: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ **Error processing your message**\n\nPlease try again or contact support.",
            parse_mode=ParseMode.MARKDOWN
        )

def get_userbot_handlers():
    """Get userbot admin handlers"""
    return [
        ("userbot_status", handle_userbot_status),
        ("userbot_set_credentials", handle_userbot_set_credentials),
        ("userbot_authenticate", handle_userbot_authenticate),
        ("userbot_authenticate_2fa", handle_userbot_authenticate_2fa),
        ("userbot_connect", handle_userbot_connect),
        ("userbot_disconnect", handle_userbot_disconnect),
        ("userbot_test", handle_userbot_test),
    ]
