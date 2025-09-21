import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from userbot_manager import userbot_manager
from userbot_database import (
    get_userbot_setting, set_userbot_setting, 
    get_delivery_keywords, add_delivery_keyword, remove_delivery_keyword,
    get_userbot_stats, log_userbot_activity,
    get_userbot_credentials, set_userbot_credentials, clear_userbot_credentials,
    set_userbot_auth_state, get_userbot_auth_state, clear_userbot_auth_state
)
from userbot_config import userbot_config

logger = logging.getLogger(__name__)

async def handle_userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show userbot status and controls"""
    try:
        # Get current status
        status = userbot_manager.get_status()
        config_summary = userbot_config.get_config_summary()
        stats = get_userbot_stats()
        
        # Build status message
        status_text = "🤖 **USERBOT STATUS**\n\n"
        
        # Configuration status
        if config_summary['enabled']:
            if config_summary['configured']:
                status_text += "✅ **Status**: Enabled & Configured\n"
            else:
                status_text += "⚠️ **Status**: Enabled but Not Configured\n"
        else:
            status_text += "❌ **Status**: Disabled\n"
        
        # Credentials status
        credentials = get_userbot_credentials()
        if credentials:
            status_text += f"🔐 **Credentials**: Configured (API ID: {credentials.get('api_id', 'N/A')})\n"
        else:
            status_text += "🔐 **Credentials**: Not Set\n"
        
        # Connection status
        if status['connected']:
            status_text += "🟢 **Connection**: Connected\n"
        else:
            status_text += "🔴 **Connection**: Disconnected\n"
        
        # Statistics
        status_text += f"\n📊 **Statistics**\n"
        status_text += f"• Active Secret Chats: {stats.get('active_secret_chats', 0)}\n"
        status_text += f"• Total Deliveries: {stats.get('total_deliveries', 0)}\n"
        status_text += f"• Recent Deliveries (24h): {stats.get('recent_deliveries', 0)}\n"
        status_text += f"• Pending Deliveries: {status['pending_deliveries']}\n"
        
        # Retry information
        if status['retries'] > 0:
            status_text += f"\n🔄 **Retries**: {status['retries']}/{status['max_retries']}\n"
        
        # Create control buttons
        keyboard = []
        
        if config_summary['enabled']:
            if status['connected']:
                keyboard.append([InlineKeyboardButton("🔌 Disconnect", callback_data="userbot_disconnect")])
            else:
                keyboard.append([InlineKeyboardButton("🔌 Connect", callback_data="userbot_connect")])
            
            keyboard.append([InlineKeyboardButton("⚙️ Settings", callback_data="userbot_settings")])
            keyboard.append([InlineKeyboardButton("📋 Keywords", callback_data="userbot_keywords")])
            keyboard.append([InlineKeyboardButton("📊 Statistics", callback_data="userbot_stats")])
        else:
            keyboard.append([InlineKeyboardButton("⚙️ Configure", callback_data="userbot_configure")])
        
        # Add credentials management button
        keyboard.append([InlineKeyboardButton("🔐 Manage Credentials", callback_data="userbot_credentials")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            status_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Log activity
        log_userbot_activity("status_viewed", update.effective_user.id, "Admin viewed userbot status")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing status: {e}")
        await update.callback_query.answer("Error showing userbot status", show_alert=True)

async def handle_userbot_connect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Connect userbot"""
    try:
        await update.callback_query.answer("Connecting userbot...")
        
        # Initialize userbot
        success = await userbot_manager.initialize()
        
        if success:
            await update.callback_query.answer("✅ Userbot connected successfully!")
            log_userbot_activity("connected", update.effective_user.id, "Admin connected userbot")
        else:
            await update.callback_query.answer("❌ Failed to connect userbot", show_alert=True)
            log_userbot_activity("connect_failed", update.effective_user.id, "Admin failed to connect userbot")
        
        # Refresh status
        await handle_userbot_status(update, context)
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error connecting: {e}")
        await update.callback_query.answer("Error connecting userbot", show_alert=True)

async def handle_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Disconnect userbot"""
    try:
        await update.callback_query.answer("Disconnecting userbot...")
        
        await userbot_manager.disconnect()
        
        await update.callback_query.answer("✅ Userbot disconnected")
        log_userbot_activity("disconnected", update.effective_user.id, "Admin disconnected userbot")
        
        # Refresh status
        await handle_userbot_status(update, context)
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error disconnecting: {e}")
        await update.callback_query.answer("Error disconnecting userbot", show_alert=True)

async def handle_userbot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show userbot settings"""
    try:
        # Get current settings
        auto_reconnect = get_userbot_setting('auto_reconnect', 'true')
        max_retries = get_userbot_setting('max_retries', '3')
        retry_delay = get_userbot_setting('retry_delay', '5')
        secret_chat_ttl = get_userbot_setting('secret_chat_ttl', '86400')
        delivery_notification = get_userbot_setting('delivery_notification', 'true')
        
        settings_text = "⚙️ **USERBOT SETTINGS**\n\n"
        settings_text += f"🔄 **Auto Reconnect**: {'✅' if auto_reconnect == 'true' else '❌'}\n"
        settings_text += f"🔁 **Max Retries**: {max_retries}\n"
        settings_text += f"⏱️ **Retry Delay**: {retry_delay}s\n"
        settings_text += f"⏰ **Secret Chat TTL**: {int(secret_chat_ttl) // 3600}h\n"
        settings_text += f"📨 **Delivery Notifications**: {'✅' if delivery_notification == 'true' else '❌'}\n"
        
        # Create settings buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Toggle Auto Reconnect", callback_data="userbot_toggle_reconnect")],
            [InlineKeyboardButton("🔁 Set Max Retries", callback_data="userbot_set_retries")],
            [InlineKeyboardButton("⏱️ Set Retry Delay", callback_data="userbot_set_delay")],
            [InlineKeyboardButton("⏰ Set Chat TTL", callback_data="userbot_set_ttl")],
            [InlineKeyboardButton("📨 Toggle Notifications", callback_data="userbot_toggle_notifications")],
            [InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing settings: {e}")
        await update.callback_query.answer("Error showing settings", show_alert=True)

async def handle_userbot_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show and manage delivery keywords"""
    try:
        keywords = get_delivery_keywords()
        
        keywords_text = "🔑 **DELIVERY KEYWORDS**\n\n"
        keywords_text += "Users can trigger product delivery by sending any of these keywords:\n\n"
        
        for i, keyword in enumerate(keywords, 1):
            keywords_text += f"{i}. `{keyword}`\n"
        
        if not keywords:
            keywords_text += "No keywords configured.\n"
        
        keywords_text += f"\nTotal: {len(keywords)} keywords"
        
        # Create keyword management buttons
        keyboard = [
            [InlineKeyboardButton("➕ Add Keyword", callback_data="userbot_add_keyword")],
            [InlineKeyboardButton("➖ Remove Keyword", callback_data="userbot_remove_keyword")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="userbot_keywords")],
            [InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            keywords_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing keywords: {e}")
        await update.callback_query.answer("Error showing keywords", show_alert=True)

async def handle_userbot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show detailed userbot statistics"""
    try:
        stats = get_userbot_stats()
        status = userbot_manager.get_status()
        
        stats_text = "📊 **USERBOT STATISTICS**\n\n"
        
        # Connection stats
        stats_text += "🔌 **Connection**\n"
        stats_text += f"• Status: {'🟢 Connected' if status['connected'] else '🔴 Disconnected'}\n"
        stats_text += f"• Retries: {status['retries']}/{status['max_retries']}\n"
        if status['last_connection_attempt']:
            stats_text += f"• Last Attempt: {status['last_connection_attempt']}\n"
        
        # Activity stats
        stats_text += f"\n📈 **Activity**\n"
        stats_text += f"• Active Secret Chats: {stats.get('active_secret_chats', 0)}\n"
        stats_text += f"• Pending Deliveries: {status['pending_deliveries']}\n"
        stats_text += f"• Total Deliveries: {stats.get('total_deliveries', 0)}\n"
        stats_text += f"• Recent Deliveries (24h): {stats.get('recent_deliveries', 0)}\n"
        
        # Create stats buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="userbot_stats")],
            [InlineKeyboardButton("📋 Delivery History", callback_data="userbot_delivery_history")],
            [InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing stats: {e}")
        await update.callback_query.answer("Error showing statistics", show_alert=True)

async def handle_userbot_toggle_reconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Toggle auto reconnect setting"""
    try:
        current = get_userbot_setting('auto_reconnect', 'true')
        new_value = 'false' if current == 'true' else 'true'
        
        set_userbot_setting('auto_reconnect', new_value)
        
        status = "enabled" if new_value == 'true' else "disabled"
        await update.callback_query.answer(f"Auto reconnect {status}")
        
        log_userbot_activity("setting_changed", update.effective_user.id, f"Auto reconnect {status}")
        
        # Refresh settings
        await handle_userbot_settings(update, context)
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error toggling reconnect: {e}")
        await update.callback_query.answer("Error updating setting", show_alert=True)

async def handle_userbot_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Toggle delivery notifications"""
    try:
        current = get_userbot_setting('delivery_notification', 'true')
        new_value = 'false' if current == 'true' else 'true'
        
        set_userbot_setting('delivery_notification', new_value)
        
        status = "enabled" if new_value == 'true' else "disabled"
        await update.callback_query.answer(f"Delivery notifications {status}")
        
        log_userbot_activity("setting_changed", update.effective_user.id, f"Notifications {status}")
        
        # Refresh settings
        await handle_userbot_settings(update, context)
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error toggling notifications: {e}")
        await update.callback_query.answer("Error updating setting", show_alert=True)

async def handle_userbot_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Show userbot credentials management"""
    try:
        credentials = get_userbot_credentials()
        
        credentials_text = "🔐 **USERBOT CREDENTIALS**\n\n"
        
        if credentials:
            credentials_text += f"✅ **Status**: Configured\n"
            credentials_text += f"📱 **API ID**: `{credentials.get('api_id', 'N/A')}`\n"
            credentials_text += f"🔑 **API Hash**: `{credentials.get('api_hash', 'N/A')[:8]}...`\n"
            credentials_text += f"📞 **Phone**: `{credentials.get('phone_number', 'N/A')}`\n"
            credentials_text += f"💾 **Session**: `{credentials.get('session_name', 'N/A')}`\n"
        else:
            credentials_text += "❌ **Status**: Not Configured\n"
            credentials_text += "Please set up your userbot credentials to enable the userbot.\n"
        
        # Create credentials management buttons
        keyboard = []
        
        if credentials:
            keyboard.append([InlineKeyboardButton("✏️ Update Credentials", callback_data="userbot_update_credentials")])
            keyboard.append([InlineKeyboardButton("🗑️ Clear Credentials", callback_data="userbot_clear_credentials")])
            keyboard.append([InlineKeyboardButton("🔄 Test Connection", callback_data="userbot_test_connection")])
        else:
            keyboard.append([InlineKeyboardButton("➕ Add Credentials", callback_data="userbot_add_credentials")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Status", callback_data="userbot_status")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            credentials_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error showing credentials: {e}")
        await update.callback_query.answer("Error showing credentials", show_alert=True)

async def handle_userbot_add_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start adding userbot credentials"""
    try:
        await update.callback_query.answer("Starting credentials setup...")
        
        # Set user state for API ID input
        context.user_data['state'] = 'awaiting_userbot_api_id'
        set_userbot_auth_state(update.effective_user.id, 'api_id')
        
        text = "🔐 **USERBOT CREDENTIALS SETUP**\n\n"
        text += "Please provide your Telegram API credentials:\n\n"
        text += "**Step 1/3**: Enter your API ID\n"
        text += "• Go to https://my.telegram.org\n"
        text += "• Log in with your userbot account\n"
        text += "• Go to 'API development tools'\n"
        text += "• Create a new application\n"
        text += "• Enter the API ID here:\n\n"
        text += "Type your API ID (numbers only):"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="userbot_credentials")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error starting credentials setup: {e}")
        await update.callback_query.answer("Error starting setup", show_alert=True)

async def handle_userbot_update_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Start updating userbot credentials"""
    try:
        await update.callback_query.answer("Starting credentials update...")
        
        # Set user state for API ID input
        context.user_data['state'] = 'awaiting_userbot_api_id'
        set_userbot_auth_state(update.effective_user.id, 'api_id')
        
        text = "🔐 **UPDATE USERBOT CREDENTIALS**\n\n"
        text += "**Step 1/3**: Enter your new API ID\n"
        text += "Type your API ID (numbers only):"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="userbot_credentials")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error starting credentials update: {e}")
        await update.callback_query.answer("Error starting update", show_alert=True)

async def handle_userbot_clear_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Clear userbot credentials"""
    try:
        await update.callback_query.answer("Clearing credentials...")
        
        success = clear_userbot_credentials()
        if success:
            # Reload userbot config
            userbot_config.reload_from_database()
            
            await update.callback_query.answer("✅ Credentials cleared successfully!")
            log_userbot_activity("credentials_cleared", update.effective_user.id, "Admin cleared userbot credentials")
        else:
            await update.callback_query.answer("❌ Failed to clear credentials", show_alert=True)
        
        # Refresh credentials view
        await handle_userbot_credentials(update, context)
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error clearing credentials: {e}")
        await update.callback_query.answer("Error clearing credentials", show_alert=True)

async def handle_userbot_test_connection(update: Update, context: ContextTypes.DEFAULT_TYPE, params=None):
    """Test userbot connection"""
    try:
        await update.callback_query.answer("Testing connection...")
        
        # Reload config first
        userbot_config.reload_from_database()
        
        if not userbot_config.is_configured():
            await update.callback_query.answer("❌ Userbot not configured", show_alert=True)
            return
        
        # Show testing message
        await update.callback_query.edit_message_text(
            "🔄 USERBOT: Testing connection...\n\n"
            "Please wait while we check the userbot status.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏳ Testing...", callback_data="userbot_test_connection")
            ]])
        )
        
        # Test connection
        logger.info("🔍 USERBOT: Admin testing connection...")
        success = await userbot_manager.initialize()
        
        if success:
            # Perform additional health check
            health_ok = await userbot_manager.health_check()
            
            if health_ok:
                status_text = "✅ USERBOT: Connection test successful!\n\n"
                status_text += "The userbot is working properly and can deliver products.\n"
                status_text += "Secret chat creation and product delivery should work correctly."
            else:
                status_text = "⚠️ USERBOT: Connection established but health check failed!\n\n"
                status_text += "The userbot connected but may not be fully functional.\n"
                status_text += "Please check the logs for more details."
            
            await update.callback_query.edit_message_text(
                status_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="userbot_status")
                ]])
            )
            log_userbot_activity("connection_tested", update.effective_user.id, "Admin tested userbot connection - success")
        else:
            await update.callback_query.edit_message_text(
                "❌ USERBOT: Connection test failed!\n\n"
                "The userbot could not connect to Telegram.\n"
                "Please check the credentials and try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="userbot_status")
                ]])
            )
            log_userbot_activity("connection_test_failed", update.effective_user.id, "Admin connection test failed")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error testing connection: {e}")
        await update.callback_query.edit_message_text(
            f"❌ Error testing connection: {str(e)}\n\n"
            "Please check the logs for more details.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="userbot_status")
            ]])
        )

# Message handlers for credentials setup
async def handle_userbot_api_id_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API ID input"""
    try:
        api_id_text = update.message.text.strip()
        
        # Validate API ID
        try:
            api_id = int(api_id_text)
            if api_id <= 0:
                raise ValueError("Invalid API ID")
        except ValueError:
            await update.message.reply_text("❌ Invalid API ID. Please enter a valid number.")
            return
        
        # Store API ID and move to next step
        context.user_data['userbot_api_id'] = api_id
        context.user_data['state'] = 'awaiting_userbot_api_hash'
        set_userbot_auth_state(update.effective_user.id, 'api_hash', str(api_id))
        
        text = "🔐 **USERBOT CREDENTIALS SETUP**\n\n"
        text += f"✅ API ID: `{api_id}`\n\n"
        text += "**Step 2/3**: Enter your API Hash\n"
        text += "• Go back to https://my.telegram.org\n"
        text += "• Copy your API Hash\n"
        text += "• Paste it here:\n\n"
        text += "Type your API Hash:"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="userbot_credentials")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling API ID: {e}")
        await update.message.reply_text("❌ Error processing API ID. Please try again.")

async def handle_userbot_api_hash_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API Hash input"""
    try:
        api_hash = update.message.text.strip()
        
        # Validate API Hash
        if len(api_hash) < 10:
            await update.message.reply_text("❌ Invalid API Hash. Please enter a valid hash.")
            return
        
        # Store API Hash and move to next step
        context.user_data['userbot_api_hash'] = api_hash
        context.user_data['state'] = 'awaiting_userbot_phone'
        set_userbot_auth_state(update.effective_user.id, 'phone', f"{context.user_data.get('userbot_api_id')}|{api_hash}")
        
        text = "🔐 **USERBOT CREDENTIALS SETUP**\n\n"
        text += f"✅ API ID: `{context.user_data.get('userbot_api_id')}`\n"
        text += f"✅ API Hash: `{api_hash[:8]}...`\n\n"
        text += "**Step 3/3**: Enter your phone number\n"
        text += "• Enter the phone number for your userbot account\n"
        text += "• Include country code (e.g., +1234567890)\n\n"
        text += "Type your phone number:"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="userbot_credentials")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling API Hash: {e}")
        await update.message.reply_text("❌ Error processing API Hash. Please try again.")

async def handle_userbot_phone_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input and save credentials"""
    try:
        phone_number = update.message.text.strip()
        
        # Validate phone number
        if not phone_number.startswith('+') or len(phone_number) < 10:
            await update.message.reply_text("❌ Invalid phone number. Please include country code (e.g., +1234567890).")
            return
        
        # Get stored credentials
        api_id = context.user_data.get('userbot_api_id')
        api_hash = context.user_data.get('userbot_api_hash')
        
        if not api_id or not api_hash:
            await update.message.reply_text("❌ Missing credentials. Please start over.")
            return
        
        # Save credentials to database
        success = set_userbot_credentials(api_id, api_hash, phone_number)
        
        if success:
            # Clear user data and state
            context.user_data.pop('userbot_api_id', None)
            context.user_data.pop('userbot_api_hash', None)
            context.user_data['state'] = None
            clear_userbot_auth_state(update.effective_user.id)
            
            # Reload userbot config
            userbot_config.reload_from_database()
            
            text = "✅ **CREDENTIALS SAVED SUCCESSFULLY!**\n\n"
            text += f"📱 API ID: `{api_id}`\n"
            text += f"🔑 API Hash: `{api_hash[:8]}...`\n"
            text += f"📞 Phone: `{phone_number}`\n\n"
            text += "The userbot is now configured and ready to use!\n"
            text += "You can test the connection from the credentials menu."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Test Connection", callback_data="userbot_test_connection")],
                [InlineKeyboardButton("🔙 Back to Credentials", callback_data="userbot_credentials")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            log_userbot_activity("credentials_saved", update.effective_user.id, f"Admin saved userbot credentials for {phone_number}")
        else:
            await update.message.reply_text("❌ Failed to save credentials. Please try again.")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling phone number: {e}")
        await update.message.reply_text("❌ Error processing phone number. Please try again.")

async def handle_userbot_photo_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo code confirmation for userbot authentication"""
    try:
        photo_code = update.message.text.strip()
        
        # Validate photo code
        if len(photo_code) < 4:
            await update.message.reply_text("❌ Invalid photo code. Please enter the code you received.")
            return
        
        # Get stored credentials from auth state
        auth_state = get_userbot_auth_state(update.effective_user.id)
        if not auth_state or auth_state.get('auth_step') != 'photo_code':
            await update.message.reply_text("❌ No active photo code verification. Please start over.")
            return
        
        # Parse stored credentials
        temp_data = auth_state.get('temp_data', '')
        if '|' not in temp_data:
            await update.message.reply_text("❌ Invalid stored data. Please start over.")
            return
        
        parts = temp_data.split('|')
        if len(parts) < 3:
            await update.message.reply_text("❌ Invalid stored data. Please start over.")
            return
        
        api_id = int(parts[0])
        api_hash = parts[1]
        phone_number = parts[2]
        
        # Save credentials to database
        success = set_userbot_credentials(api_id, api_hash, phone_number)
        
        if success:
            # Clear user data and state
            context.user_data['state'] = None
            clear_userbot_auth_state(update.effective_user.id)
            
            # Reload userbot config
            userbot_config.reload_from_database()
            
            text = "✅ **AUTHENTICATION COMPLETED!**\n\n"
            text += f"📱 API ID: `{api_id}`\n"
            text += f"🔑 API Hash: `{api_hash[:8]}...`\n"
            text += f"📞 Phone: `{phone_number}`\n\n"
            text += "The userbot is now fully configured and authenticated!\n"
            text += "You can test the connection from the credentials menu."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Test Connection", callback_data="userbot_test_connection")],
                [InlineKeyboardButton("🔙 Back to Credentials", callback_data="userbot_credentials")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            log_userbot_activity("photo_code_verified", update.effective_user.id, f"Admin completed userbot authentication for {phone_number}")
        else:
            await update.message.reply_text("❌ Failed to save credentials. Please try again.")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling photo code: {e}")
        await update.message.reply_text("❌ Error processing photo code. Please try again.")

async def handle_userbot_2fa_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 2FA code for userbot authentication"""
    try:
        twofa_code = update.message.text.strip()
        
        # Validate 2FA code
        if len(twofa_code) < 4:
            await update.message.reply_text("❌ Invalid 2FA code. Please enter the code from your authenticator app.")
            return
        
        # Get stored credentials from auth state
        auth_state = get_userbot_auth_state(update.effective_user.id)
        if not auth_state or auth_state.get('auth_step') != '2fa_code':
            await update.message.reply_text("❌ No active 2FA verification. Please start over.")
            return
        
        # Parse stored credentials
        temp_data = auth_state.get('temp_data', '')
        if '|' not in temp_data:
            await update.message.reply_text("❌ Invalid stored data. Please start over.")
            return
        
        parts = temp_data.split('|')
        if len(parts) < 3:
            await update.message.reply_text("❌ Invalid stored data. Please start over.")
            return
        
        api_id = int(parts[0])
        api_hash = parts[1]
        phone_number = parts[2]
        
        # Save credentials to database
        success = set_userbot_credentials(api_id, api_hash, phone_number)
        
        if success:
            # Clear user data and state
            context.user_data['state'] = None
            clear_userbot_auth_state(update.effective_user.id)
            
            # Reload userbot config
            userbot_config.reload_from_database()
            
            text = "✅ **2FA AUTHENTICATION COMPLETED!**\n\n"
            text += f"📱 API ID: `{api_id}`\n"
            text += f"🔑 API Hash: `{api_hash[:8]}...`\n"
            text += f"📞 Phone: `{phone_number}`\n\n"
            text += "The userbot is now fully configured and authenticated!\n"
            text += "You can test the connection from the credentials menu."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Test Connection", callback_data="userbot_test_connection")],
                [InlineKeyboardButton("🔙 Back to Credentials", callback_data="userbot_credentials")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            log_userbot_activity("2fa_verified", update.effective_user.id, f"Admin completed 2FA authentication for {phone_number}")
        else:
            await update.message.reply_text("❌ Failed to save credentials. Please try again.")
        
    except Exception as e:
        logger.error(f"❌ USERBOT ADMIN: Error handling 2FA code: {e}")
        await update.message.reply_text("❌ Error processing 2FA code. Please try again.")

# Add more handlers as needed for other settings...

def get_userbot_admin_handlers():
    """Get list of userbot admin handlers"""
    return [
        ("userbot_status", handle_userbot_status),
        ("userbot_connect", handle_userbot_connect),
        ("userbot_disconnect", handle_userbot_disconnect),
        ("userbot_settings", handle_userbot_settings),
        ("userbot_keywords", handle_userbot_keywords),
        ("userbot_stats", handle_userbot_stats),
        ("userbot_toggle_reconnect", handle_userbot_toggle_reconnect),
        ("userbot_toggle_notifications", handle_userbot_toggle_notifications),
        ("userbot_credentials", handle_userbot_credentials),
        ("userbot_add_credentials", handle_userbot_add_credentials),
        ("userbot_update_credentials", handle_userbot_update_credentials),
        ("userbot_clear_credentials", handle_userbot_clear_credentials),
        ("userbot_test_connection", handle_userbot_test_connection),
    ]
