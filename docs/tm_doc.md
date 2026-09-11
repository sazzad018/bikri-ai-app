## Available Custom Events

### 1. `signup`
Fires immediately after a user successfully registers a new account.

**DataLayer Payload:**
```json
{
  "event": "signup",
  "id": 123,
  "email": "user@example.com",
  "first_name": "Mohin",
  "last_name": "Uddin",
  "phone": "01712345678",
  "timestamp": 1718203845.123
}
```

### 2. `payment_success`
Fires when a user successfully purchases a credit package (either via automated bKash checkout or manual admin approval).

**DataLayer Payload:**
```json
{
  "event": "payment_success",
  "id": "550e8400-e29b-41d4-a716-446655440000", // uuid4
  "user_id": 123,
  "amount": 500,
  "package_id": 2,
  "package_title": "Business",
  "credits": 1000,
  "payment_method": "manual",           // Enum: "bkash" | "manual"
  "manual_transaction_id": "BIX12345", // Will be null if payment_method is "bkash"
  "currency": "BDT",
  "timestamp": 1718203900.567
}
```