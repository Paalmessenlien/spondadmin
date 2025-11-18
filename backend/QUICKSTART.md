# Quick Start Guide

Get the Spond Admin API up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- `python3-venv` package installed

## Setup Steps

### 1. Install Python venv (if not already installed)

```bash
sudo apt install python3-venv
```

### 2. Create and activate virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

The `.env` file has been created with default settings. You can edit it if needed:

```bash
nano .env  # or use your preferred editor
```

**Important**: Make sure to set a secure `SECRET_KEY` in production!

### 5. Create the first admin user

```bash
python3 create_admin.py
```

Follow the prompts:
- Username: Choose a username (e.g., `admin`)
- Email: Your email address
- Full Name: Your name (optional)
- Password: At least 8 characters
- Is superuser?: Type `y` for first admin

### 6. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test the API

Open your browser and visit:

- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

Or use the test script:

```bash
./test_auth.sh
```

## First Login

### Using the Swagger UI

1. Go to http://localhost:8000/api/v1/docs
2. Find the `/api/v1/auth/login` endpoint
3. Click "Try it out"
4. Enter your credentials:
   ```json
   {
     "username": "admin",
     "password": "your-password"
   }
   ```
5. Click "Execute"
6. Copy the `access_token` from the response
7. Click "Authorize" button at the top
8. Paste the token (it will add "Bearer" automatically)
9. Now you can test all protected endpoints!

### Using curl

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# This returns a token like:
# {"access_token":"eyJ0eXAiOiJKV1QiLC...","token_type":"bearer"}

# Use the token for authenticated requests
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Next Steps

### Add Spond Credentials

To use the Spond integration, edit `.env` and add:

```bash
SPOND_USERNAME=your-spond-email@example.com
SPOND_PASSWORD=your-spond-password
```

### Available Endpoints

Once authenticated, you can access:

- `GET /api/v1/auth/me` - Get your user info
- `PUT /api/v1/auth/me` - Update your info
- `POST /api/v1/auth/register` - Create new admin (superuser only)
- `GET /api/v1/auth/admins` - List all admins (superuser only)
- `GET /api/v1/auth/admins/{id}` - Get admin by ID (superuser only)
- `PUT /api/v1/auth/admins/{id}` - Update admin (superuser only)
- `DELETE /api/v1/auth/admins/{id}` - Delete admin (superuser only)

## Troubleshooting

### Port already in use

If port 8000 is already in use, change the port:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Virtual environment issues

If you get errors about `ensurepip`, install `python3-venv`:

```bash
sudo apt install python3.13-venv  # or your Python version
```

### Database errors

If you get database errors, delete the database and restart:

```bash
rm spond_admin.db
uvicorn app.main:app --reload
```

The database will be recreated automatically.

## Development

To enable debug mode, edit `.env`:

```bash
DEBUG=true
```

This will show detailed error messages and SQL queries in the logs.

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- View API docs at http://localhost:8000/api/v1/docs
- Check server logs for error messages
