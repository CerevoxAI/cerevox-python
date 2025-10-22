# Account API Reference

## Table of Contents

- [AsyncAccount](#asyncaccount)
  - [Constructor](#constructor)
  - [Methods](#methods)
    - [get\_account\_info()](#get_account_info)
    - [get\_account\_plan(account\_id)](#get_account_planaccount_id)
    - [get\_account\_usage(account\_id)](#get_account_usageaccount_id)
    - [create\_user(email, name)](#create_useremail-name)
    - [get\_users()](#get_users)
    - [get\_user\_me()](#get_user_me)
    - [update\_user\_me(name)](#update_user_mename)
    - [get\_user\_by\_id(user\_id)](#get_user_by_iduser_id)
    - [update\_user\_by\_id(user\_id, name)](#update_user_by_iduser_id-name)
    - [delete\_user\_by\_id(user\_id, email)](#delete_user_by_iduser_id-email)
- [Account](#account)
  - [Constructor](#constructor-1)
  - [Methods](#methods-1)
    - [get\_account\_info()](#get_account_info-1)
    - [get\_account\_plan(account\_id)](#get_account_planaccount_id-1)
    - [get\_account\_usage(account\_id)](#get_account_usageaccount_id-1)
    - [create\_user(email, name)](#create_useremail-name-1)
    - [get\_users()](#get_users-1)
    - [get\_user\_me()](#get_user_me-1)
    - [update\_user\_me(name)](#update_user_mename-1)
    - [get\_user\_by\_id(user\_id)](#get_user_by_iduser_id-1)
    - [update\_user\_by\_id(user\_id, name)](#update_user_by_iduser_id-name-1)
    - [delete\_user\_by\_id(user\_id, email)](#delete_user_by_iduser_id-email-1)

---

## AsyncAccount

The async client for managing Accounts & Users in Cerevox.

### Constructor

```python
AsyncAccount(email: str, api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | str | Yes | - | User email address for authentication |
| `api_key` | str | Yes | - | Your Cerevox API key for above email |
| `base_url` | str | No | (Cerevox Base Url) | Base URL for the Cerevox Account API |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### Methods

#### get_account_info()

Get current account information

```python
account = await client.get_account_info()
```

**Parameters:** (None)

**Returns:** `AccountInfo` - with account_id and account_name

#### get_account_plan(account_id)

Get account plan and limits information

```python
plan = await client.get_account_plan("ACCOUNT_ID")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `account_id` | str | Yes | - | The account identifier |

**Returns:** `AccountPlan` - with plan details and limits

#### get_account_usage(account_id)

Get account usage metrics

```python
usage = await client.get_account_usage("ACCOUNT_ID")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `account_id` | str | Yes | - | The account identifier |

**Returns:** `UsageMetrics` - with current usage statistics

#### create_user(email, name)

Create a new user in the account

```python
created = await client.create_user("users_email", "users_name")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | str | Yes | - | User email address |
| `name` | str | Yes | - | User display name |

**Returns:** `CreatedResponse` - with creation status

#### get_users()

Get list of all users in the account

```python
users = await client.get_users()
```

**Parameters:** (None)

**Returns:** `List[User]` - List of User objects

#### get_user_me()

Get current user information

```python
user = await client.get_user_me()
```

**Parameters:** (None)

**Returns:** `User` - object with current user details

#### update_user_me(name)

Update current user information

```python
updated = await client.update_user_me("name")
```

**Parameters:** 

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | - | User display name |

**Returns:** `UpdatedResponse` - with update status

#### get_user_by_id(user_id)

Get user information by ID (Admin only)

```python
user = await client.get_user_by_id()
```

**Parameters:** 

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | str | Yes | - | The user identifier |

**Returns:** `User` - object with user details


#### update_user_by_id(user_id, name)

Update user information by ID (Admin only)

```python
updated = await client.update_user_by_id("user_id", "name")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | str | Yes | - | The user identifier |
| `name` | str | Yes | - | User display name |

**Returns:** `UpdatedResponse` - with update status


#### delete_user_by_id(user_id, email)

Delete user by ID (Admin only)

```python
deleted = await client.delete_user_by_id("user_id", "users_email")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | str | Yes | - | The user identifier |
| `email` | str | Yes | - | Email confirmation for deletion |

**Returns:** `DeletedResponse` - with deletion status

---

## Account

Synchronous client for managing Accounts & Users in Cerevox (legacy/compatibility).

### Constructor

```python
Account(email: str, api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | str | Yes | - | User email address for authentication |
| `api_key` | str | Yes | - | Your Cerevox API key for above email |
| `base_url` | str | No | (Cerevox Base Url) | Base URL for the Cerevox Account API |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### Methods

#### get_account_info()

Get current account information (synchronous)

**Parameters:** (None)

**Returns:** `AccountInfo` - with account_id and account_name

#### get_account_plan(account_id)

Get account plan and limits information (synchronous)

**Parameters:** Same as AsyncAccount.get_account_plan()

**Returns:** `AccountPlan` - with plan details and limits

#### get_account_usage(account_id)

Get account usage metrics (synchronous)

**Parameters:** Same as AsyncAccount.get_account_usage()

**Returns:** `UsageMetrics` - with current usage statistics

#### create_user(email, name)

Create a new user in the account (synchronous)

**Parameters:** Same as AsyncAccount.create_user()

**Returns:** `CreatedResponse` - with creation status

#### get_users()

Get list of all users in the account (synchronous)

**Parameters:** (None)

**Returns:** `List[User]` - List of User objects

#### get_user_me()

Get current user information (synchronous)

**Parameters:** (None)

**Returns:** `User` - object with current user details

#### update_user_me(name)

Update current user information (synchronous)

**Parameters:** Same as AsyncAccount.update_user_me()

**Returns:** `UpdatedResponse` - with update status

#### get_user_by_id(user_id)

Get user information by ID (Admin only; synchronous)

**Parameters:** Same as AsyncAccount.get_user_by_id()

**Returns:** `User` - object with user details


#### update_user_by_id(user_id, name)

Update user information by ID (Admin only; synchronous)

**Parameters:** Same as AsyncAccount.update_user_by_id()

**Returns:** `UpdatedResponse` - with update status


#### delete_user_by_id(user_id, email)

Delete user by ID (Admin only; synchronous)

**Parameters:** Same as AsyncAccount.delete_user_by_id()

**Returns:** `DeletedResponse` - with deletion status
