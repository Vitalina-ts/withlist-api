# 🎁 Wish List API

A modern REST API for creating and managing birthday wish lists, with the ability for friends to mark gifts they plan to give.

---

## ✨ Features

- 🔐 **JWT Authentication** – secure user authorization  
- 👥 **Public access** – non-logged-in users can view wish lists  
- ✅ **Gift marking** – friends can indicate which gift they will give  
- 📝 **Change history** – the owner can see who and when marked a gift  
- ⚡ **Redis caching** – fast data access  
- 🐘 **PostgreSQL** – reliable data storage  
- 🚀 **FastAPI** – a fast and modern Python framework  

---

## 🛠️ Quick Start

### Option 1: Docker (recommended)

See the [Docker Compose guide](docs/containers.md) to launch the API, UI, PostgreSQL, and Redis.

### Option 2: Run locally

```bash
# Install dependencies
make install

# Start PostgreSQL and Redis locally
# Then start the API
make run

# Or
python run.py
```

---

## 📖 API Documentation

Once the API is running, documentation will be available at:

- **Swagger UI**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc  

---

## 🔧 Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Main variables:

- `DATABASE_URL` – PostgreSQL connection  
- `REDIS_URL` – Redis connection  
- `SECRET_KEY` – secret key for JWT (must be changed!)  

---

## 📊 Database structure

- **users** – system users  
- **wishlists** – wish lists  
- **wish_items** – items in wish lists  
- **wish_item_statuses** – marking history  

---

## 🎯 Main Endpoints

### Authentication
- `POST /register` – register a new user  
- `POST /token` – get JWT token  

### Wish lists
- `GET /wishlists` – all wish lists (publicly available)  
- `POST /wishlists` – create a new list  
- `GET /wishlists/{id}` – specific list  

### List items
- `POST /wishlists/{id}/items` – add an item  
- `GET /wishlists/{id}/items` – all items in the list  
- `POST /wishlists/{id}/items/{item_id}/mark` – mark an item  

### Monitoring
- `GET /health` – service health check  

---

## 🔄 Useful Commands

```bash
make install     # Install dependencies
make run         # Run locally
make docker-up   # Start Docker
make docker-down # Stop Docker
make logs        # View logs
make health      # Check API health
make clean       # Clean Docker resources
```

---

## 🚀 Production Readiness

For production environment:

1. Change `SECRET_KEY` to a cryptographically secure one  
2. Configure HTTPS  
3. Set up CORS restrictions  
4. Configure monitoring and logging  
5. Use database replication  
6. Set up a backup strategy  

---

## 🧪 Testing

The API is ready for integration with a Vue.js frontend.  
All endpoints return standardized JSON responses.  

---

**Author**: Nataliia Romanenko  
**Technologies**: FastAPI, PostgreSQL, Redis, Docker  

---

## 🛠️ Makefile Commands Reference

```makefile
# Install dependencies
install:
	pip install -r requirements.txt

# Run locally
run:
	python run.py

# Run with Docker
docker-up:
	docker-compose up -d

# Stop Docker
docker-down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f api

# Create migration
migration:
	alembic revision --autogenerate -m "$(name)"

# Apply migrations
migrate:
	alembic upgrade head

# Check API health
health:
	curl http://localhost:8000/health
```
