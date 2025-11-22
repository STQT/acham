# OCTO Payment Gateway Integration

Интеграция платежной системы OCTO для обработки платежей без перенаправления на форму оплаты OCTO.

## Настройка

Добавьте следующие переменные окружения в `.env`:

```env
# OCTO Payment Gateway
OCTO_API_URL=https://secure.octo.uz
OCTO_SHOP_ID=your_shop_id
OCTO_SECRET=your_secret_key
OCTO_TEST_MODE=true  # для тестовых транзакций

# Frontend URL для редиректов после оплаты
FRONTEND_URL=https://yourdomain.com
```

## API Endpoints

### 1. Инициация платежа

**POST** `/api/orders/{order_id}/payment/initiate/`

Инициирует платежную транзакцию для заказа.

**Параметры запроса:**
- `language` (query, optional): Язык интерфейса (`uz`, `ru`, `en`). По умолчанию `uz`.

**Ответ:**
```json
{
  "transaction_id": "octo_transaction_id",
  "status": "prepared"
}
```

### 2. Подтверждение платежа (ввод данных карты)

**POST** `/api/orders/{order_id}/payment/confirm/`

Подтверждает платеж с данными банковской карты.

**Тело запроса:**
```json
{
  "transaction_id": "octo_transaction_id",
  "card_number": "8600123456789012",
  "expire": "1225",
  "cardholder_name": "JOHN DOE"
}
```

**Ответ:**
```json
{
  "payment_id": "octo_payment_id",
  "verification_url": "https://...",
  "seconds_left": 300,
  "status": "verification_required"
}
```

### 3. Проверка OTP кода

**POST** `/api/orders/{order_id}/payment/verify-otp/`

Проверяет OTP код, отправленный на телефон клиента.

**Тело запроса:**
```json
{
  "transaction_id": "octo_transaction_id",
  "sms_key": "123456"
}
```

**Ответ:**
```json
{
  "status": "processing",
  "message": "OTP verified. Payment is being processed."
}
```

### 4. Статус платежа

**GET** `/api/orders/{order_id}/payment/status/`

Получает текущий статус платежа для заказа.

**Ответ:**
```json
{
  "transaction_id": "octo_transaction_id",
  "payment_id": "octo_payment_id",
  "status": "success",
  "verification_url": null,
  "seconds_left": null,
  "error_code": null,
  "error_message": null
}
```

### 5. Webhook для уведомлений от OCTO

**POST** `/api/payments/notify/`

Эндпоинт для получения уведомлений от OCTO о статусе платежа. Не требует аутентификации.

## Процесс оплаты

1. **Создание заказа**: Создайте заказ через `/api/orders/`
2. **Инициация платежа**: Вызовите `/api/orders/{order_id}/payment/initiate/`
3. **Ввод данных карты**: Вызовите `/api/orders/{order_id}/payment/confirm/` с данными карты
4. **Проверка OTP**: После получения OTP кода, вызовите `/api/orders/{order_id}/payment/verify-otp/`
5. **Ожидание подтверждения**: OCTO отправит уведомление на webhook, статус заказа обновится автоматически

## Статусы платежных транзакций

- `pending` - Ожидает инициации
- `prepared` - Платеж подготовлен
- `verification_required` - Требуется верификация OTP
- `processing` - Платеж обрабатывается
- `success` - Платеж успешно завершен
- `failed` - Платеж не удался
- `cancelled` - Платеж отменен

## Модели данных

### PaymentTransaction

Хранит информацию о платежных транзакциях OCTO:
- `order` - Связанный заказ
- `shop_transaction_id` - Уникальный ID транзакции на нашей стороне
- `octo_transaction_id` - ID транзакции от OCTO
- `octo_payment_id` - ID платежа от OCTO
- `status` - Статус транзакции
- `amount` - Сумма платежа
- `currency` - Валюта (обычно UZS)
- `request_payload` - Данные запроса к OCTO
- `response_payload` - Ответ от OCTO

## Тестирование

Для тестовых транзакций установите `OCTO_TEST_MODE=true` в настройках.

## Примечания

- Все платежи обрабатываются в одностадийном режиме (`auto_capture: true`)
- Поддерживаются методы оплаты: `bank_card`, `uzcard`, `humo`
- Webhook автоматически обновляет статус заказа при успешной/неуспешной оплате
- Все запросы к платежным эндпоинтам требуют аутентификации (кроме webhook)

