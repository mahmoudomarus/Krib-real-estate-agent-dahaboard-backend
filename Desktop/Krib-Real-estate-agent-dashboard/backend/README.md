# Krib AI FastAPI Backend

A modern, AI-powered backend for the Krib AI property management platform.

## 🚀 Features

- **FastAPI Backend** - High-performance async API
- **Supabase Integration** - Database, authentication, and storage
- **AI-Powered Listings** - Automated description and amenities generation
- **S3 Storage** - Scalable image and media storage
- **Real Analytics** - Comprehensive property and booking analytics
- **JWT Authentication** - Secure user authentication
- **RESTful API** - Clean, documented API endpoints

## 🏗️ Architecture

```
Frontend (React) → FastAPI Backend → Supabase (DB + Auth) + S3 (Storage) + AI Services
```

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- AWS S3 bucket (optional, for image storage)
- OpenAI or Anthropic API key (optional, for AI features)

## 🛠️ Quick Setup

1. **Clone and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```

3. **Update environment variables:**
   Edit the generated `.env` file with your API keys:
   ```env
   # AI Services (at least one required for AI features)
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   
   # AWS S3 (required for image uploads)
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   S3_BUCKET_NAME=your-rental-ai-bucket
   ```

4. **Start the server:**
   ```bash
   # Unix/macOS
   ./run.sh
   
   # Windows
   run.bat
   
   # Manual
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Manual Setup

If you prefer manual setup:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   # or
   venv\\Scripts\\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file:**
   ```bash
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

4. **Initialize database:**
   ```bash
   python -c "
   import asyncio
   from app.core.database import init_db
   asyncio.run(init_db())
   "
   ```

## 🗃️ Database Schema

The backend automatically creates these tables in Supabase:

- **users** - User profiles (extends Supabase auth.users)
- **properties** - Property listings
- **bookings** - Property reservations
- **reviews** - Guest reviews
- **property_analytics** - Analytics data

## 🤖 AI Features

### Property Description Generation
```python
POST /api/properties/ai/generate-description
{
  "property_data": {
    "property_type": "apartment",
    "city": "New York",
    "bedrooms": 2,
    "amenities": ["WiFi", "Kitchen"]
  },
  "use_anthropic": false
}
```

### Amenities Suggestions
```python
POST /api/properties/ai/suggest-amenities
{
  "property_data": {...},
  "existing_amenities": ["WiFi", "Kitchen"]
}
```

### Pricing Strategy
```python
POST /api/properties/ai/pricing-strategy
{
  "property_data": {...},
  "market_data": {...}
}
```

## 📁 File Upload (S3)

### Direct Upload
```python
POST /api/upload/property/{property_id}/images
# Multipart form data with image files
```

### Presigned URLs
```python
POST /api/upload/property/{property_id}/presigned-upload
{
  "filename": "image.jpg",
  "content_type": "image/jpeg",
  "property_id": "uuid"
}
```

## 📊 Analytics Endpoints

- `GET /api/analytics/` - Comprehensive analytics
- `GET /api/analytics/property/{id}` - Property-specific analytics  
- `GET /api/analytics/dashboard-overview` - Dashboard overview stats

## 🔐 Authentication

All endpoints (except auth) require Bearer token:

```javascript
headers: {
  'Authorization': 'Bearer <supabase_access_token>'
}
```

### Auth Endpoints
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/signin` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/signout` - Logout user

## 🏠 Property Management

### Create Property
```python
POST /api/properties/
{
  "title": "Beautiful Apartment",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY", 
  "country": "USA",
  "property_type": "apartment",
  "bedrooms": 2,
  "bathrooms": 1.5,
  "max_guests": 4,
  "price_per_night": 150.00,
  "amenities": ["WiFi", "Kitchen", "AC"],
  "description": "Optional - AI will generate if not provided"
}
```

### AI Enhancement
```python
POST /api/properties/{id}/enhance-with-ai
# Automatically improves listings with AI-generated content
```

## 📅 Booking Management

### Create Booking
```python
POST /api/bookings/
{
  "property_id": "uuid",
  "guest_name": "John Doe",
  "guest_email": "john@example.com",
  "guest_phone": "+1234567890",
  "check_in": "2024-06-01",
  "check_out": "2024-06-05",
  "guests": 2,
  "special_requests": "Late check-in"
}
```

### Manage Bookings
- `GET /api/bookings/` - List bookings
- `PUT /api/bookings/{id}` - Update booking
- `POST /api/bookings/{id}/confirm` - Confirm booking
- `POST /api/bookings/{id}/cancel` - Cancel booking

## 🔧 Configuration

### Environment Variables

```env
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AWS S3 (Required for image uploads)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# AI Services (Optional - at least one recommended)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

## 🚀 Deployment

### Local Development
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production (Render, Railway, etc.)
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔍 Development Tips

### Adding New Features
1. Create models in `app/models/schemas.py`
2. Add routes in `app/api/routes/`
3. Implement business logic in `app/services/`
4. Update database schema in `app/core/database.py`

### Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Debugging
- Enable debug mode: `DEBUG=True` in .env
- Check logs in console
- Use `/docs` for interactive API testing
- Monitor Supabase dashboard for database issues

## 📈 Performance

- **Async/Await** - Non-blocking I/O operations
- **Connection Pooling** - Efficient database connections
- **Caching** - Redis support for background tasks
- **Image Optimization** - Automatic image processing
- **Rate Limiting** - Built-in request limiting

## 🛡️ Security

- **JWT Authentication** - Secure token-based auth
- **Row Level Security** - Database-level security
- **Input Validation** - Pydantic model validation
- **CORS Configuration** - Secure cross-origin requests
- **File Upload Validation** - Secure file handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - Check API docs at `/docs`
- **Supabase Docs** - https://supabase.com/docs
- **FastAPI Docs** - https://fastapi.tiangolo.com/

---

**Happy coding! 🚀**
