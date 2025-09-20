import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from userbot_manager import userbot_manager
from userbot_database import (
    get_userbot_setting, set_userbot_setting, 
    get_delivery_keywords, add_delivery_keyword, remove_delivery_keyword,
    get_userbot_stats, log_userbot_activity
)
from userbot_config import userbot_config

logger = logging.getLogger(__name__)

async def handle_userbot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_toggle_reconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_userbot_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    ]
