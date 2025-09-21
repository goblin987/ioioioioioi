import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from simple_userbot import simple_userbot

logger = logging.getLogger(__name__)

async def handle_simple_userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show simple userbot status"""
    try:
        status = simple_userbot.get_status()
        
        # Build status message
        status_text = "🤖 **SIMPLE USERBOT STATUS**\n\n"
        
        # Connection status
        if status['connected']:
            status_text += "🟢 **Status**: Connected & Ready\n"
        else:
            status_text += "🔴 **Status**: Disconnected\n"
        
        # Credentials status
        if status['has_credentials']:
            status_text += "✅ **Credentials**: Configured\n"
        else:
            status_text += "❌ **Credentials**: Not Set\n"
        
        # Session status
        if status['session_exists']:
            status_text += "📁 **Session**: File exists\n"
        else:
            status_text += "📁 **Session**: No file (needs authentication)\n"
        
        # Create buttons
        keyboard = []
        
        if not status['has_credentials']:
            keyboard.append([InlineKeyboardButton("⚙️ Set Credentials", callback_data="simple_userbot_set_credentials")])
        elif not status['connected']:
            if status['session_exists']:
                keyboard.append([InlineKeyboardButton("🔌 Connect", callback_data="simple_userbot_connect")])
            else:
                keyboard.append([InlineKeyboardButton("🔐 Authenticate", callback_data="simple_userbot_authenticate")])
        else:
            keyboard.append([InlineKeyboardButton("🔌 Disconnect", callback_data="simple_userbot_disconnect")])
            keyboard.append([InlineKeyboardButton("🧪 Test Secret Chat", callback_data="simple_userbot_test")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")])
        
        await update.callback_query.edit_message_text(
            status_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error showing status: {e}")
        await update.callback_query.answer("Error showing status", show_alert=True)

async def handle_simple_userbot_set_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Set userbot credentials"""
    try:
        await update.callback_query.answer("Setting up credentials...")
        
        # Set user state to await API ID
        context.user_data['awaiting_simple_api_id'] = True
        
        await update.callback_query.edit_message_text(
            "⚙️ **SET USERBOT CREDENTIALS**\n\n"
            "Please send the API ID (number only):\n\n"
            "Example: 12345678",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="simple_userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error setting up credentials: {e}")
        await update.callback_query.answer("Error setting up credentials", show_alert=True)

async def handle_simple_userbot_authenticate(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start authentication process"""
    try:
        await update.callback_query.answer("Starting authentication...")
        
        # Try to initialize
        success, message = await simple_userbot.initialize()
        
        if success:
            await update.callback_query.edit_message_text(
                "✅ **USERBOT CONNECTED!**\n\n"
                "The userbot is now ready to send secret messages.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        else:
            # Check if we need verification code
            await update.callback_query.edit_message_text(
                "📱 **AUTHENTICATION REQUIRED**\n\n"
                "Please check your phone for a verification code.\n\n"
                "Send the code as a message to this bot.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
            
            # Set state to await verification code
            context.user_data['awaiting_simple_verification_code'] = True
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error starting authentication: {e}")
        await update.callback_query.answer("Error starting authentication", show_alert=True)

async def handle_simple_userbot_connect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Connect userbot"""
    try:
        await update.callback_query.answer("Connecting...")
        
        success, message = await simple_userbot.initialize()
        
        if success:
            await update.callback_query.edit_message_text(
                "✅ **USERBOT CONNECTED!**\n\n"
                "The userbot is now ready to send secret messages.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ **CONNECTION FAILED**\n\n"
                "Please try authenticating again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔐 Authenticate", callback_data="simple_userbot_authenticate"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error connecting: {e}")
        await update.callback_query.answer("Error connecting", show_alert=True)

async def handle_simple_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Disconnect userbot"""
    try:
        await update.callback_query.answer("Disconnecting...")
        
        await simple_userbot.disconnect()
        
        await update.callback_query.edit_message_text(
            "✅ **USERBOT DISCONNECTED**\n\n"
            "The userbot has been disconnected.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error disconnecting: {e}")
        await update.callback_query.answer("Error disconnecting", show_alert=True)

async def handle_simple_userbot_test(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Test secret chat"""
    try:
        await update.callback_query.answer("Testing secret chat...")
        
        # Send test message to admin
        admin_id = update.effective_user.id
        success, message = await simple_userbot.send_secret_message(
            admin_id, 
            "🧪 **TEST MESSAGE**\n\nThis is a test message from the userbot via secret chat!"
        )
        
        if success:
            await update.callback_query.edit_message_text(
                "✅ **TEST SENT!**\n\n"
                "Check your secret chats for the test message.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ **TEST FAILED**\n\n"
                "Could not send test message. Check logs for details.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error testing: {e}")
        await update.callback_query.answer("Error testing", show_alert=True)

# Message handlers
async def handle_simple_api_id_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API ID input"""
    try:
        api_id_text = update.message.text.strip()
        
        try:
            api_id = int(api_id_text)
            context.user_data['simple_api_id'] = api_id
            context.user_data.pop('awaiting_simple_api_id', None)
            context.user_data['awaiting_simple_api_hash'] = True
            
            await update.message.reply_text(
                "✅ API ID saved!\n\n"
                "Now send the API Hash:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="simple_userbot_status")
                ]])
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid API ID. Please send a number only.")
            
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error handling API ID: {e}")
        await update.message.reply_text("❌ Error processing API ID. Please try again.")

async def handle_simple_api_hash_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API Hash input"""
    try:
        api_hash = update.message.text.strip()
        context.user_data['simple_api_hash'] = api_hash
        context.user_data.pop('awaiting_simple_api_hash', None)
        context.user_data['awaiting_simple_phone'] = True
        
        await update.message.reply_text(
            "✅ API Hash saved!\n\n"
            "Now send the phone number (with country code):\n\n"
            "Example: +1234567890",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="simple_userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error handling API Hash: {e}")
        await update.message.reply_text("❌ Error processing API Hash. Please try again.")

async def handle_simple_phone_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    try:
        phone = update.message.text.strip()
        context.user_data['simple_phone'] = phone
        context.user_data.pop('awaiting_simple_phone', None)
        
        # Set credentials
        api_id = context.user_data.get('simple_api_id')
        api_hash = context.user_data.get('simple_api_hash')
        
        success, message = simple_userbot.set_credentials(api_id, api_hash, phone)
        if not success:
            await update.message.reply_text(f"❌ **ERROR**: {message}")
            return
        
        await update.message.reply_text(
            "✅ **CREDENTIALS SAVED!**\n\n"
            "Now you can authenticate the userbot.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔐 Authenticate", callback_data="simple_userbot_authenticate"),
                InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
            ]])
        )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error handling phone: {e}")
        await update.message.reply_text("❌ Error processing phone number. Please try again.")

async def handle_simple_verification_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification code input"""
    try:
        code = update.message.text.strip()
        context.user_data.pop('awaiting_simple_verification_code', None)
        
        # Try to authenticate with code
        success, message = await simple_userbot.authenticate_with_code(code)
        
        if success:
            await update.message.reply_text(
                "✅ **AUTHENTICATION SUCCESSFUL!**\n\n"
                "The userbot is now connected and ready to send secret messages.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        else:
            await update.message.reply_text(
                "❌ **AUTHENTICATION FAILED**\n\n"
                "Invalid verification code. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="simple_userbot_authenticate"),
                    InlineKeyboardButton("🔙 Back to Status", callback_data="simple_userbot_status")
                ]])
            )
        
    except Exception as e:
        logger.error(f"❌ SIMPLE USERBOT ADMIN: Error handling verification code: {e}")
        await update.message.reply_text("❌ Error processing verification code. Please try again.")

def get_simple_userbot_handlers():
    """Get simple userbot handlers"""
    return [
        ("simple_userbot_status", handle_simple_userbot_status),
        ("simple_userbot_set_credentials", handle_simple_userbot_set_credentials),
        ("simple_userbot_authenticate", handle_simple_userbot_authenticate),
        ("simple_userbot_connect", handle_simple_userbot_connect),
        ("simple_userbot_disconnect", handle_simple_userbot_disconnect),
        ("simple_userbot_test", handle_simple_userbot_test),
    ]
