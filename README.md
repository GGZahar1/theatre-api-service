
# Theatre API Service

## Technologies
- Python
- Django
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose
- JWT Authentication

## Features
- User authentication and permissions
- Filtering and pagination
- API documentation
- Automated tests

## Requirements
- Python 3.10+
- Docker Desktop

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

Start the database:

```bash
docker compose up -d db
```

Apply migrations and run the server:

```bash
python manage.py migrate
python manage.py runserver
```

## Run with Docker Compose

```bash
docker compose up --build
```

## Run Tests

```bash
python manage.py test
```
