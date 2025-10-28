# User Registration API Documentation

## Overview
This API provides endpoints for user registration with country selection and OTP verification specifically for Uzbekistan users.

## Base URL
```
/api/users/
```

## Endpoints

### 1. Get Available Countries
**GET** `/api/users/countries/`

Returns a list of all available countries for registration.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Uzbekistan",
    "code": "UZ",
    "phone_code": "+998",
    "requires_phone_verification": "Y"
  },
  {
    "id": 2,
    "name": "United States",
    "code": "US",
    "phone_code": "+1",
    "requires_phone_verification": "N"
  }
]
```

### 2. User Registration
**POST** `/api/users/register/`

Register a new user with country selection.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password1": "securepassword123",
  "password2": "securepassword123",
  "name": "John Doe",
  "phone": "+998901234567",
  "country_id": 1
}
```

**Response (Non-Uzbekistan):**
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "",
    "country": {
      "id": 2,
      "name": "United States",
      "code": "US",
      "phone_code": "+1",
      "requires_phone_verification": "N"
    },
    "phone_verified": "N",
    "url": "http://localhost:8000/api/users/1/"
  },
  "message": "User registered successfully",
  "requires_otp": false
}
```

**Response (Uzbekistan):**
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+998901234567",
    "country": {
      "id": 1,
      "name": "Uzbekistan",
      "code": "UZ",
      "phone_code": "+998",
      "requires_phone_verification": "Y"
    },
    "phone_verified": "N",
    "url": "http://localhost:8000/api/users/1/"
  },
  "message": "User registered successfully. OTP sent to your phone number.",
  "requires_otp": true,
  "otp_verification_url": "/api/users/verify-otp/1/"
}
```

### 3. OTP Verification
**POST** `/api/users/verify-otp/{user_id}/`

Verify OTP code for Uzbekistan users.

**Request Body:**
```json
{
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+998901234567",
    "country": {
      "id": 1,
      "name": "Uzbekistan",
      "code": "UZ",
      "phone_code": "+998",
      "requires_phone_verification": "Y"
    },
    "phone_verified": "Y",
    "url": "http://localhost:8000/api/users/1/"
  },
  "message": "Phone number verified successfully",
  "token": "user_logged_in"
}
```

### 4. Resend OTP
**POST** `/api/users/resend-otp/`

Resend OTP code to user's phone number.

**Request Body:**
```json
{
  "user_id": 1
}
```

**Response:**
```json
{
  "message": "OTP sent successfully to your phone number"
}
```

### 5. Get User Profile
**GET** `/api/users/me/`

Get current user's profile information.

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "user@example.com",
  "phone": "+998901234567",
  "country": {
    "id": 1,
    "name": "Uzbekistan",
    "code": "UZ",
    "phone_code": "+998",
    "requires_phone_verification": "Y"
  },
  "phone_verified": "Y",
  "url": "http://localhost:8000/api/users/1/"
}
```

## Registration Flow

### For Non-Uzbekistan Users:
1. **GET** `/api/users/countries/` - Get available countries
2. **POST** `/api/users/register/` - Register with country_id (non-UZ)
3. User is registered and can login normally

### For Uzbekistan Users:
1. **GET** `/api/users/countries/` - Get available countries
2. **POST** `/api/users/register/` - Register with country_id=1 (UZ) and phone number
3. **POST** `/api/users/verify-otp/{user_id}/` - Verify OTP code
4. User is registered and logged in

## Error Responses

### Validation Errors (400 Bad Request):
```json
{
  "email": ["This field is required."],
  "password1": ["This password is too short."],
  "phone": ["Phone number is required for Uzbekistan"]
}
```

### OTP Errors (400 Bad Request):
```json
{
  "otp_code": ["Invalid or expired OTP code"]
}
```

## Notes

- Phone number is only required for Uzbekistan users
- OTP verification is only available for Uzbekistan users
- OTP codes expire after 10 minutes
- OTP codes are 6-digit numeric codes
- For development, OTP codes are logged to console and sent via email to admin
- In production, integrate with SMS service in `OTPService.send_otp_to_phone()`
