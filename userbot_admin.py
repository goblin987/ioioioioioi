"""
Simple Userbot Admin Interface
Clean and focused on the core workflow
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from userbot import userbot

logger = logging.getLogger(__name__)

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
        
        context.user_data['awaiting_userbot_api_id'] = True
        
        await update.callback_query.edit_message_text(
            "⚙️ **SET USERBOT CREDENTIALS**\n\n"
            "Step 1/3: Send your API ID (number only)\n\n"
            "Get it from: https://my.telegram.org\n"
            "Example: 12345678",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="userbot_status")
            ]])
        )
        
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
        api_id_text = update.message.text.strip()
        
        try:
            api_id = int(api_id_text)
            context.user_data['temp_api_id'] = api_id
            context.user_data.pop('awaiting_userbot_api_id', None)
            context.user_data['awaiting_userbot_api_hash'] = True
            
            await update.message.reply_text(
                "✅ API ID saved!\n\n"
                "Step 2/3: Send your API Hash:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="userbot_status")
                ]])
            )
        except ValueError:
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
