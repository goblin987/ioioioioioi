import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaDocument

from userbot_config import userbot_config
from utils import get_db_connection

logger = logging.getLogger(__name__)

class ProductDeliveryHandler:
    """Handles product delivery through secret chats"""
    
    def __init__(self, userbot_client: Client):
        self.client = userbot_client
        self.delivery_templates = {
            'default': self._get_default_delivery_template(),
            'digital': self._get_digital_delivery_template(),
            'physical': self._get_physical_delivery_template()
        }
    
    async def deliver_product(self, user_id: int, product_data: Dict[str, Any]) -> bool:
        """Deliver product to user through secret chat"""
        try:
            # Get secret chat ID
            secret_chat_id = await self._get_secret_chat_id(user_id)
            if not secret_chat_id:
                logger.error(f"❌ DELIVERY: No secret chat found for user {user_id}")
                return False
            
            # Determine delivery type
            delivery_type = product_data.get('delivery_type', 'default')
            template = self.delivery_templates.get(delivery_type, self.delivery_templates['default'])
            
            # Send delivery message
            success = await self._send_delivery_message(secret_chat_id, product_data, template)
            if not success:
                return False
            
            # Send product details
            success = await self._send_product_details(secret_chat_id, product_data)
            if not success:
                return False
            
            # Send product media if available
            if product_data.get('has_media'):
                success = await self._send_product_media(secret_chat_id, product_data)
                if not success:
                    logger.warning(f"⚠️ DELIVERY: Failed to send media for user {user_id}")
            
            # Log delivery
            await self._log_delivery(user_id, product_data)
            
            logger.info(f"✅ DELIVERY: Product delivered to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error delivering product to user {user_id}: {e}")
            return False
    
    async def _get_secret_chat_id(self, user_id: int) -> Optional[int]:
        """Get secret chat ID for user from database"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                SELECT secret_chat_id FROM userbot_secret_chats 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            result = c.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error getting secret chat ID: {e}")
            return None
    
    async def _send_delivery_message(self, secret_chat_id: int, product_data: Dict[str, Any], template: str) -> bool:
        """Send the main delivery message"""
        try:
            # Format template with product data
            message = self._format_delivery_template(template, product_data)
            
            # Send message with TTL
            await self.client.send_message(
                secret_chat_id,
                message,
                ttl=userbot_config.secret_chat_ttl
            )
            
            logger.info(f"📨 DELIVERY: Delivery message sent to chat {secret_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error sending delivery message: {e}")
            return False
    
    async def _send_product_details(self, secret_chat_id: int, product_data: Dict[str, Any]) -> bool:
        """Send detailed product information"""
        try:
            details = self._format_product_details(product_data)
            
            await self.client.send_message(
                secret_chat_id,
                details,
                ttl=userbot_config.secret_chat_ttl
            )
            
            logger.info(f"📋 DELIVERY: Product details sent to chat {secret_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error sending product details: {e}")
            return False
    
    async def _send_product_media(self, secret_chat_id: int, product_data: Dict[str, Any]) -> bool:
        """Send product media (photos, documents, etc.)"""
        try:
            media_files = product_data.get('media_files', [])
            if not media_files:
                return True
            
            # Group media by type
            photos = [f for f in media_files if f.get('type') == 'photo']
            documents = [f for f in media_files if f.get('type') == 'document']
            
            # Send photos as album if multiple
            if len(photos) > 1:
                media_group = []
                for photo in photos:
                    media_group.append(InputMediaPhoto(photo['file_path']))
                
                await self.client.send_media_group(
                    secret_chat_id,
                    media_group,
                    ttl=userbot_config.secret_chat_ttl
                )
            elif len(photos) == 1:
                await self.client.send_photo(
                    secret_chat_id,
                    photos[0]['file_path'],
                    ttl=userbot_config.secret_chat_ttl
                )
            
            # Send documents
            for doc in documents:
                await self.client.send_document(
                    secret_chat_id,
                    doc['file_path'],
                    ttl=userbot_config.secret_chat_ttl
                )
            
            logger.info(f"📸 DELIVERY: Media sent to chat {secret_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error sending product media: {e}")
            return False
    
    def _format_delivery_template(self, template: str, product_data: Dict[str, Any]) -> str:
        """Format delivery template with product data"""
        try:
            # Replace placeholders in template
            formatted = template.format(
                product_name=product_data.get('product_name', 'Product'),
                product_type=product_data.get('product_type', 'Item'),
                city=product_data.get('city', 'Unknown'),
                district=product_data.get('district', 'Unknown'),
                price=product_data.get('price', '0.00'),
                size=product_data.get('size', 'N/A'),
                order_id=product_data.get('order_id', 'Unknown'),
                delivery_time=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            return formatted
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error formatting template: {e}")
            return template
    
    def _format_product_details(self, product_data: Dict[str, Any]) -> str:
        """Format detailed product information"""
        details = f"""
🔍 **PRODUCT DETAILS**

📦 **Product**: {product_data.get('product_name', 'N/A')}
🏷️ **Type**: {product_data.get('product_type', 'N/A')}
📍 **Location**: {product_data.get('city', 'N/A')}, {product_data.get('district', 'N/A')}
💰 **Price**: €{product_data.get('price', '0.00')}
📏 **Size**: {product_data.get('size', 'N/A')}
🆔 **Order ID**: {product_data.get('order_id', 'N/A')}
⏰ **Delivered**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

🔒 **This message will self-destruct in {userbot_config.secret_chat_ttl // 3600} hours**
        """.strip()
        
        return details
    
    def _get_default_delivery_template(self) -> str:
        """Get default delivery message template"""
        return """
🎉 **YOUR PRODUCT IS READY!**

📦 **{product_name}** has been delivered to your secret chat.

📍 **Location**: {city}, {district}
💰 **Price**: €{price}
🆔 **Order**: {order_id}
⏰ **Delivered**: {delivery_time}

🔒 **This is a secure delivery channel**
⏰ **Message expires in {ttl} hours**

Thank you for your purchase! 🛍️
        """.strip()
    
    def _get_digital_delivery_template(self) -> str:
        """Get digital product delivery template"""
        return """
💻 **DIGITAL PRODUCT DELIVERY**

Your digital product is ready for download!

📦 **{product_name}**
🏷️ **Type**: {product_type}
💰 **Price**: €{price}
🆔 **Order**: {order_id}

🔗 **Download links and access codes will be sent separately**

🔒 **Secure delivery channel**
⏰ **Message expires in {ttl} hours**
        """.strip()
    
    def _get_physical_delivery_template(self) -> str:
        """Get physical product delivery template"""
        return """
📦 **PHYSICAL PRODUCT DELIVERY**

Your physical product is ready for pickup!

📦 **{product_name}**
📍 **Pickup Location**: {city}, {district}
💰 **Price**: €{price}
🆔 **Order**: {order_id}

📍 **Pickup instructions will be sent separately**

🔒 **Secure delivery channel**
⏰ **Message expires in {ttl} hours**
        """.strip()
    
    async def _log_delivery(self, user_id: int, product_data: Dict[str, Any]):
        """Log delivery in database"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO userbot_deliveries 
                (user_id, order_id, product_name, delivery_type, delivered_at, status) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                product_data.get('order_id', ''),
                product_data.get('product_name', ''),
                product_data.get('delivery_type', 'default'),
                datetime.now(timezone.utc).isoformat(),
                'delivered'
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error logging delivery: {e}")
    
    async def get_delivery_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get delivery history for a user"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                SELECT order_id, product_name, delivery_type, delivered_at, status
                FROM userbot_deliveries 
                WHERE user_id = ?
                ORDER BY delivered_at DESC
            """, (user_id,))
            
            results = []
            for row in c.fetchall():
                results.append({
                    'order_id': row[0],
                    'product_name': row[1],
                    'delivery_type': row[2],
                    'delivered_at': row[3],
                    'status': row[4]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ DELIVERY: Error getting delivery history: {e}")
            return []
