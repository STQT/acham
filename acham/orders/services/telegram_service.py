"""Service for sending notifications to Telegram bot."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramConfigurationError(RuntimeError):
    """Raised when Telegram bot credentials are not configured."""


class TelegramAPIError(RuntimeError):
    """Raised when Telegram API returns an unexpected response."""


class TelegramBotClient:
    """Client for sending messages to Telegram bot."""

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self) -> None:
        """Initialize Telegram bot client."""
        self._token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self._chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

        if not self._token:
            raise TelegramConfigurationError("TELEGRAM_BOT_TOKEN is not configured.")
        if not self._chat_id:
            raise TelegramConfigurationError("TELEGRAM_CHAT_ID is not configured.")

    def _make_request(self, method: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a request to Telegram API."""
        url = self.BASE_URL.format(token=self._token, method=method)
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                error_description = result.get("description", "Unknown error")
                raise TelegramAPIError(f"Telegram API error: {error_description}")
            
            return result
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to send Telegram message: {exc}")
            raise TelegramAPIError(f"Request failed: {exc}") from exc

    def send_message(
        self,
        text: str,
        parse_mode: str | None = "HTML",
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        """Send a text message to the configured chat.
        
        Args:
            text: Message text (supports HTML formatting if parse_mode='HTML')
            parse_mode: Parse mode ('HTML', 'Markdown', or None)
            disable_web_page_preview: Disable link previews
            
        Returns:
            API response dictionary
        """
        data = {
            "chat_id": self._chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        
        if parse_mode:
            data["parse_mode"] = parse_mode
        
        return self._make_request("sendMessage", data)

    def send_order_notification(self, order: Any, message_type: str = "new") -> dict[str, Any]:
        """Send formatted order notification.
        
        Args:
            order: Order instance
            message_type: Type of notification ('new', 'pending', 'status_update')
            
        Returns:
            API response dictionary
        """
        if message_type == "new":
            text = self._format_new_order_message(order)
        elif message_type == "pending":
            text = self._format_pending_order_message(order)
        elif message_type == "status_update":
            text = self._format_status_update_message(order)
        else:
            text = self._format_new_order_message(order)
        
        return self.send_message(text)

    def _format_new_order_message(self, order: Any) -> str:
        """Format message for new order."""
        items_list = list(order.items.all())
        if items_list:
            items_text = "\n".join([
                f"  • {item.product_name} ({item.size}) x{item.quantity} - {item.total_price} {order.currency}"
                for item in items_list
            ])
        else:
            items_text = "  (нет товаров)"
        
        # Получаем адрес доставки
        shipping_address = order.addresses.filter(address_type='shipping').first()
        
        # Формируем адрес
        address_parts = []
        if shipping_address:
            if shipping_address.address_line1:
                address_parts.append(shipping_address.address_line1)
            if shipping_address.address_line2:
                address_parts.append(shipping_address.address_line2)
            if shipping_address.city:
                address_parts.append(shipping_address.city)
            if shipping_address.region:
                address_parts.append(shipping_address.region)
            if shipping_address.postal_code:
                address_parts.append(shipping_address.postal_code)
            if shipping_address.country:
                address_parts.append(shipping_address.country)
        
        address_text = ", ".join(address_parts) if address_parts else "Адрес не указан"
        
        # Получаем имя пользователя
        user_name = None
        if shipping_address:
            # Сначала пробуем из адреса доставки
            if shipping_address.first_name or shipping_address.last_name:
                name_parts = []
                if shipping_address.first_name:
                    name_parts.append(shipping_address.first_name)
                if shipping_address.last_name:
                    name_parts.append(shipping_address.last_name)
                user_name = " ".join(name_parts)
        if not user_name and order.user:
            # Если нет в адресе, берем из пользователя
            user_name = order.user.name
        
        user_name_text = user_name if user_name else "Имя не указано"
        
        # Получаем номер телефона
        phone = order.customer_phone
        if not phone and shipping_address:
            phone = shipping_address.phone
        if not phone and order.user:
            phone = order.user.phone
        
        phone_text = phone if phone else "Не указан"
        
        customer_info = []
        customer_info.append(f"👤 Имя: {user_name_text}")
        customer_info.append(f"📱 Телефон: {phone_text}")
        if order.customer_email:
            customer_info.append(f"📧 Email: {order.customer_email}")
        if order.user:
            customer_info.append(f"🆔 User ID: {order.user.id}")
        
        customer_text = "\n".join(customer_info)
        
        return f"""
🛍️ <b>Новый заказ #{order.number}</b>

💰 Сумма: <b>{order.total_amount} {order.currency}</b>
📦 Товаров: {order.total_items}
📊 Статус: {order.get_status_display()}

{customer_text}

📍 <b>Адрес доставки:</b>
{address_text}

📋 <b>Товары:</b>
{items_text}

🔗 Order ID: {order.public_id}
⏰ Создан: {order.placed_at.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

    def _format_pending_order_message(self, order: Any) -> str:
        """Format message for pending order (not completed)."""
        items_list = list(order.items.all())
        if items_list:
            items_text = "\n".join([
                f"  • {item.product_name} ({item.size}) x{item.quantity} - {item.total_price} {order.currency}"
                for item in items_list
            ])
        else:
            items_text = "  (нет товаров)"
        
        customer_info = []
        if order.customer_email:
            customer_info.append(f"📧 Email: {order.customer_email}")
        if order.customer_phone:
            customer_info.append(f"📱 Phone: {order.customer_phone}")
        if order.user:
            customer_info.append(f"👤 User ID: {order.user.id}")
        
        customer_text = "\n".join(customer_info) if customer_info else "No contact info"
        
        # Calculate time since order creation
        from django.utils import timezone
        time_diff = timezone.now() - order.placed_at
        hours = int(time_diff.total_seconds() / 3600)
        minutes = int((time_diff.total_seconds() % 3600) / 60)
        time_ago = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
        
        return f"""
⚠️ <b>Заказ не оформлен #{order.number}</b>

⏱️ Прошло времени: <b>{time_ago}</b>
💰 Сумма: <b>{order.total_amount} {order.currency}</b>
📦 Товаров: {order.total_items}
📊 Статус: {order.get_status_display()}

{customer_text}

📋 <b>Товары:</b>
{items_text}

🔗 Order ID: {order.public_id}
⏰ Создан: {order.placed_at.strftime('%Y-%m-%d %H:%M:%S')}

💡 <i>Рекомендуется связаться с клиентом</i>
        """.strip()

    def _format_status_update_message(self, order: Any) -> str:
        """Format message for order status update."""
        return f"""
📊 <b>Обновление статуса заказа #{order.number}</b>

Статус: <b>{order.get_status_display()}</b>
💰 Сумма: {order.total_amount} {order.currency}

🔗 Order ID: {order.public_id}
        """.strip()
