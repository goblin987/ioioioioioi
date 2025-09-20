# 🤖 Userbot Integration Setup Guide

This guide will help you set up the Telegram userbot integration for secret chat product delivery.

## 📋 Prerequisites

1. **Separate Telegram Account**: You need a separate Telegram account for the userbot (not your main bot account)
2. **API Credentials**: Get API ID and API Hash from https://my.telegram.org
3. **Phone Number**: The phone number associated with the userbot account

## 🔧 Environment Variables

Add these environment variables to your deployment platform (Render, Heroku, etc.):

```bash
# Userbot Configuration
USERBOT_ENABLED=true
USERBOT_API_ID=your_api_id_here
USERBOT_API_HASH=your_api_hash_here
USERBOT_PHONE_NUMBER=+1234567890

# Optional Settings
USERBOT_SESSION_NAME=userbot_session
USERBOT_AUTO_RECONNECT=true
USERBOT_MAX_RETRIES=3
USERBOT_RETRY_DELAY=5
USERBOT_SECRET_CHAT_TTL=86400
USERBOT_DELIVERY_KEYWORDS=hello,hi,start,product,delivery
```

## 🚀 Setup Steps

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your userbot account
3. Go to "API development tools"
4. Create a new application:
   - App title: "Your Bot Name Userbot"
   - Short name: "yourbot_userbot"
   - Platform: "Desktop"
5. Note down your `api_id` and `api_hash`

### 2. Configure Environment Variables

Add the environment variables to your deployment platform:

```bash
USERBOT_ENABLED=true
USERBOT_API_ID=12345678
USERBOT_API_HASH=abcdef1234567890abcdef1234567890
USERBOT_PHONE_NUMBER=+1234567890
```

### 3. Deploy the Bot

Deploy your bot with the new userbot functionality. The userbot will automatically initialize when the bot starts.

### 4. First-Time Authentication

On first run, the userbot will need to authenticate:

1. The bot will log a message about needing authentication
2. Check your userbot account's Telegram app for a verification code
3. The userbot will automatically complete the authentication process
4. A session file will be created for future use

## 🎛️ Admin Controls

Access userbot controls through the admin panel:

1. Go to Admin Menu
2. Click "🤖 Userbot Control"
3. Available options:
   - **Status**: View connection status and statistics
   - **Connect/Disconnect**: Manual connection control
   - **Settings**: Configure userbot behavior
   - **Keywords**: Manage delivery trigger keywords
   - **Statistics**: View delivery statistics

## 🔄 How It Works

### Purchase Flow Integration

1. **User completes purchase** → Bot processes payment
2. **Payment confirmed** → Bot triggers userbot delivery
3. **Userbot creates secret chat** → With the buyer
4. **Userbot sends notification** → "Your product is ready!"
5. **User sends keyword** → "hello", "product", etc.
6. **Userbot delivers product** → Photos, details, instructions

### Secret Chat Features

- **Self-destructing messages**: All messages auto-delete after 24 hours
- **Secure delivery**: Only the buyer can see the product details
- **Keyword triggers**: Users can request delivery anytime
- **Media support**: Photos, documents, and other files

## ⚙️ Configuration Options

### Delivery Keywords

Users can trigger product delivery by sending any of these keywords:
- `hello`, `hi`, `start`
- `product`, `delivery`, `ready`
- `get` (and any custom keywords you add)

### Message TTL (Time To Live)

- **Default**: 24 hours (86400 seconds)
- **Configurable**: Set via `USERBOT_SECRET_CHAT_TTL`
- **Range**: 1 second to 1 week

### Auto-Reconnect

- **Enabled by default**: Automatically reconnects if connection drops
- **Max retries**: 3 attempts with 5-second delay
- **Configurable**: Via environment variables

## 🛡️ Security Features

### Account Safety

- **Separate account**: Uses dedicated userbot account
- **Session management**: Secure session file storage
- **Rate limiting**: Built-in Telegram rate limit handling
- **Error recovery**: Automatic reconnection and retry logic

### Data Protection

- **Encrypted transmission**: All data encrypted in transit
- **Self-destructing messages**: Automatic message deletion
- **No data storage**: Userbot doesn't store sensitive data
- **Secure logging**: Sensitive data excluded from logs

## 📊 Monitoring

### Admin Dashboard

View real-time userbot status:
- Connection status
- Active secret chats
- Pending deliveries
- Delivery statistics
- Error logs

### Logs

Monitor userbot activity:
```bash
# Connection status
✅ USERBOT: Successfully connected as @your_userbot

# Delivery events
📦 USERBOT: Delivery scheduled for user 123456789
✅ USERBOT: Product delivered to user 123456789

# Error handling
❌ USERBOT: Connection error: Network timeout
🔄 USERBOT: Attempting reconnection (attempt 1/3)
```

## 🔧 Troubleshooting

### Common Issues

**1. Authentication Failed**
```
❌ USERBOT: Invalid phone code
```
- **Solution**: Check phone number format (+1234567890)
- **Solution**: Verify API credentials

**2. Connection Drops**
```
❌ USERBOT: Connection error: Network timeout
```
- **Solution**: Check internet connection
- **Solution**: Verify API credentials are still valid

**3. Secret Chat Creation Failed**
```
❌ USERBOT: User @username not found
```
- **Solution**: Ensure user has a username set
- **Solution**: Check if user blocked the userbot account

**4. Delivery Not Triggered**
```
⚠️ USERBOT: No delivery data for user 123456789
```
- **Solution**: Check if userbot is connected
- **Solution**: Verify purchase completion

### Debug Mode

Enable detailed logging:
```python
# In userbot_config.py
logging.getLogger('userbot').setLevel(logging.DEBUG)
```

## 📱 User Experience

### For Buyers

1. **Complete purchase** → Normal bot flow
2. **Receive notification** → "Your product is ready for delivery!"
3. **Join secret chat** → Automatic secret chat creation
4. **Send keyword** → "hello" or "product"
5. **Receive product** → Photos, details, instructions
6. **Messages auto-delete** → After 24 hours

### For Admins

1. **Monitor status** → Admin panel userbot controls
2. **View statistics** → Delivery counts and success rates
3. **Manage settings** → Keywords, TTL, auto-reconnect
4. **Troubleshoot issues** → Connection status and error logs

## 🚨 Important Notes

### Account Safety

- **Use a separate account** for the userbot
- **Don't use your main bot account** as userbot
- **Keep credentials secure** and never share them
- **Monitor for suspicious activity** in the userbot account

### Legal Considerations

- **Check local laws** regarding automated messaging
- **Respect Telegram ToS** and rate limits
- **Monitor usage** to avoid abuse
- **Have backup plans** if userbot gets restricted

### Backup Plans

- **Regular bot delivery**: Still works if userbot fails
- **Manual delivery**: Admin can manually send products
- **Error notifications**: Admins get notified of failures
- **Fallback systems**: Multiple delivery methods available

## 🎯 Best Practices

1. **Test thoroughly** before production use
2. **Monitor logs** regularly for issues
3. **Keep credentials updated** and secure
4. **Have backup delivery methods** ready
5. **Train users** on how to use secret chat delivery
6. **Monitor user feedback** and adjust settings accordingly

## 📞 Support

If you encounter issues:

1. **Check logs** for error messages
2. **Verify configuration** and credentials
3. **Test with a small purchase** first
4. **Contact support** with specific error messages
5. **Check Telegram status** for service issues

---

**Happy delivering! 🚀**
