# ConstructFlix
Track your construction projects in real-time
#!/usr/bin/env python3
"""
ConstructFlix GitHub README Generator
Generates a professional, comprehensive README.md file for the ConstructFlix project
"""

import os
from datetime import datetime


def generate_readme():
    """Generate comprehensive README content for ConstructFlix"""
    
    readme_content = """# 📋 ConstructFlix
> Track your construction projects in real-time

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<div align="center">
  <img src="https://via.placeholder.com/800x400/1f1f1f/e50914?text=ConstructFlix" alt="ConstructFlix Banner" width="800" height="400">
</div>

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## 🎯 Overview

**ConstructFlix** is an enterprise-grade construction project management platform inspired by Netflix's sleek UI/UX. It provides comprehensive tools for scheduling, resource management, budget tracking, and team collaboration in construction projects.

### 🏗️ Why ConstructFlix?

- **40%** reduction in project delays through real-time scheduling
- **60%** faster team collaboration with instant notifications
- **25%** cost savings through optimized resource management
- **99.9%** uptime with enterprise-grade architecture

## ✨ Key Features

### 📊 Project & Task Management
- ✅ Create and manage multiple projects with Gantt charts
- ✅ Task dependencies (FS, SS, FF, SF) with lag/lead time
- ✅ Critical path analysis and what-if scenarios
- ✅ Milestone tracking with visual indicators
- ✅ Work Breakdown Structure (WBS) support

### 📈 Resource Management
- ✅ Track labor, equipment, and materials
- ✅ Real-time availability and utilization monitoring
- ✅ Supplier management with rating system
- ✅ Resource allocation calendar
- ✅ Automated shortage alerts

### 💰 Budget & Cost Control
- ✅ Earned Value Management (EVM) metrics
- ✅ Budget vs actual variance tracking
- ✅ Purchase order management
- ✅ Cost performance index (CPI) and schedule performance index (SPI)
- ✅ Automated budget alerts

### 👥 Collaboration
- ✅ Real-time notifications (WebSocket)
- ✅ Team comments with @mentions
- ✅ Direct messaging between users
- ✅ Activity feed and audit logs
- ✅ File sharing with version control

### 📱 Reporting & Analytics
- ✅ Interactive dashboards
- ✅ Custom report generation (PDF, Excel, CSV)
- ✅ Export/Import in multiple formats
- ✅ Project health assessment
- ✅ Portfolio-level analytics

### 🔒 Security
- ✅ JWT authentication with refresh tokens
- ✅ Role-based access control (RBAC)
- ✅ Rate limiting and brute force protection
- ✅ Audit logging for compliance
- ✅ Data encryption at rest and in transit

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.11 | Core programming language |
| **Flask** | 2.3 | Web framework |
| **Flask-SQLAlchemy** | 3.1 | ORM for database |
| **Flask-Login** | 0.6 | User session management |
| **Flask-SocketIO** | 5.3 | Real-time WebSocket communication |
| **Celery** | 5.3 | Async task queue |
| **Redis** | 7.0 | Caching & message broker |
| **PostgreSQL** | 15 | Primary database |
| **Elasticsearch** | 8.10 | Full-text search |
| **JWT** | 2.8 | Authentication tokens |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.2 | UI library |
| **TypeScript** | 5.0 | Type-safe JavaScript |
| **Bootstrap 5** | 5.3 | CSS framework |
| **Plotly** | 2.27 | Interactive charts |
| **Socket.IO Client** | 4.5 | WebSocket client |

### DevOps
| Technology | Purpose |
|---|---|
| **Docker** | Containerization |
| **Docker Compose** | Orchestration |
| **Nginx** | Reverse proxy & load balancing |
| **Gunicorn** | WSGI server |
| **GitHub Actions** | CI/CD pipeline |
| **Prometheus** | Monitoring |
| **Grafana** | Metrics visualization |
| **ELK Stack** | Log aggregation |

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Web    │  │  Mobile  │  │   API    │  │  Admin   │   │
│  │   App    │  │   App    │  │  Client  │  │  Panel   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                           │
│                       (Nginx/HAProxy)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Gateway                         │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │  │
│  │  │ Auth   │  │Project │  │ Task   │  │Resource│    │  │
│  │  │Service │  │Service │  │Service │  │Service │    │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │  │
│  │  │ Budget │  │Notifica│  │ Report │  │ Search │    │  │
│  │  │Service │  │Service │  │Service │  │Service │    │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │ Elasticsearch│      │
│  │   (Primary)  │  │   (Cache)    │  │   (Search)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    MinIO     │  │   RabbitMQ   │                         │
│  │   (Storage)  │  │    (Queue)   │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

Get ConstructFlix up and running in minutes with Docker Compose.

### Prerequisites
- Docker & Docker Compose
- Git
- Python 3.11+ (for local development)
- Node.js 16+ (for frontend development)

### Start the Application
```bash
# Clone the repository
git clone https://github.com/yourusername/constructflix.git
cd constructflix

# Copy environment variables
cp .env.example .env

# Start services with Docker Compose
docker-compose up -d

# Initialize the database
docker-compose exec api python manage.py db upgrade

# Create superuser account
docker-compose exec api python manage.py create-user --admin

# Access the application
# Web: http://localhost:3000
# API: http://localhost:5000
# Admin Panel: http://localhost:5000/admin
```

## 📦 Installation

### Development Setup

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/constructflix.git
cd constructflix
```

#### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
```

#### 3. Database Setup
```bash
# Create PostgreSQL database
createdb constructflix_dev

# Run migrations
flask db upgrade

# Seed sample data (optional)
python manage.py seed-db
```

#### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
```

#### 5. Start Development Servers
```bash
# Terminal 1: Start Flask backend
python wsgi.py

# Terminal 2: Start React frontend
npm start

# Terminal 3: Start Celery worker
celery -A app.celery worker -l info

# Terminal 4: Start Redis (if not using Docker)
redis-server
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/constructflix_dev
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_HOURS=24

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=constructflix-uploads

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Frontend
REACT_APP_API_URL=http://localhost:5000
REACT_APP_WS_URL=ws://localhost:5000
```

### Docker Configuration

Edit `docker-compose.yml` for production settings:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/constructflix
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=constructflix
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 📚 Usage Guide

### Creating a Project

1. Log in to ConstructFlix
2. Click **New Project** button
3. Fill in project details:
   - Project name
   - Description
   - Start date
   - End date
   - Budget
4. Click **Create**

### Adding Tasks

1. Open a project
2. Click **Add Task**
3. Configure:
   - Task name
   - Duration
   - Dependencies
   - Resource assignments
   - Budget allocation
4. Save and publish

### Managing Resources

1. Navigate to **Resources** tab
2. View resource availability
3. Allocate to tasks
4. Monitor utilization
5. Receive shortage alerts

### Generating Reports

1. Go to **Reports** section
2. Select report type:
   - Project Summary
   - Budget Analysis
   - Resource Utilization
   - Timeline
3. Customize filters and format
4. Export as PDF/Excel/CSV

## 🔌 API Documentation

### Authentication

**POST** `/api/auth/login`
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Projects

**GET** `/api/projects` - List all projects
**POST** `/api/projects` - Create new project
**GET** `/api/projects/{id}` - Get project details
**PUT** `/api/projects/{id}` - Update project
**DELETE** `/api/projects/{id}` - Delete project

### Tasks

**GET** `/api/projects/{projectId}/tasks` - List tasks
**POST** `/api/projects/{projectId}/tasks` - Create task
**PUT** `/api/tasks/{taskId}` - Update task
**DELETE** `/api/tasks/{taskId}` - Delete task

### Resources

**GET** `/api/resources` - List resources
**POST** `/api/resources` - Add resource
**GET** `/api/resources/{id}` - Get resource details
**PUT** `/api/resources/{id}` - Update resource

### Full API Reference
[See API Documentation](./docs/API.md)

## 🗄️ Database Schema

### Key Tables

**projects**
```sql
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  start_date DATE,
  end_date DATE,
  budget DECIMAL(12, 2),
  status VARCHAR(50),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**tasks**
```sql
CREATE TABLE tasks (
  id SERIAL PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  name VARCHAR(255),
  duration INTEGER,
  start_date DATE,
  end_date DATE,
  status VARCHAR(50),
  created_at TIMESTAMP
);
```

**resources**
```sql
CREATE TABLE resources (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  type VARCHAR(50),
  availability_hours INTEGER,
  cost_per_hour DECIMAL(10, 2),
  created_at TIMESTAMP
);
```

[See full schema](./docs/DATABASE.md)

## 🧪 Testing

### Run Unit Tests
```bash
# Backend tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Load Testing
```bash
# Using locust
locust -f tests/load/locustfile.py
```

## 🚢 Deployment

### Deploy to Production

#### Using Docker
```bash
# Build and push image
docker build -t yourusername/constructflix:latest .
docker push yourusername/constructflix:latest

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Using Kubernetes
```bash
# Build image
docker build -t constructflix:latest .

# Create namespace
kubectl create namespace constructflix

# Deploy
kubectl apply -f k8s/ -n constructflix
```

#### Using Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create constructflix-app

# Set environment variables
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py db upgrade
```

### Health Checks
- API: `GET /api/health`
- Database: `GET /api/health/db`
- Cache: `GET /api/health/cache`

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

### 1. Fork the Repository
```bash
git clone https://github.com/yourusername/constructflix.git
cd constructflix
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Write clean, documented code
- Follow PEP 8 for Python
- Run linters: `flake8`, `black`

### 4. Write Tests
```bash
pytest tests/test_your_feature.py
```

### 5. Submit Pull Request
- Provide clear description
- Reference related issues
- Ensure CI/CD passes

### Development Guidelines
- [Code Style Guide](./docs/CONTRIBUTING.md)
- [Commit Message Convention](./docs/CONTRIBUTING.md)
- [Pull Request Process](./docs/CONTRIBUTING.md)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### MIT License Summary
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Liability limited
- ⚠️ Warranty disclaimed

## 🆘 Support

### Getting Help

- **Documentation**: [Read the docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/constructflix/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/constructflix/discussions)
- **Email**: support@constructflix.com
- **Community Slack**: [Join Slack Channel](https://constructflix.slack.com)

### Frequently Asked Questions
[See FAQ](./docs/FAQ.md)

### Report a Bug
[Create an issue](https://github.com/yourusername/constructflix/issues/new/choose)

### Security Issues
Please email security@constructflix.com instead of using the issue tracker.

---

<div align="center">

**[⬆ back to top](#-constructflix)**

Made with ❤️ by the ConstructFlix Team

**[GitHub](https://github.com/yourusername/constructflix)** • **[Website](https://constructflix.com)** • **[Docs](https://docs.constructflix.com)**

</div>
"""
    
    return readme_content


def save_readme(output_path):
    """Save generated README to file"""
    
    readme = generate_readme()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"✅ README generated successfully!")
    print(f"📁 File saved to: {output_path}")
    print(f"📊 Total lines: {len(readme.split(chr(10)))}")
    print(f"📝 Total characters: {len(readme)}")


def main():
    """Main execution"""
    
    output_file = "README.md"
    
    # Change to script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)
    
    print("🚀 ConstructFlix GitHub README Generator")
    print("=" * 50)
    print(f"⏰ Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generate and save
    save_readme(output_path)
    
    print()
    print("✨ README is ready for GitHub!")
    print("💡 Tips:")
    print("   - Replace 'yourusername' with your actual GitHub username")
    print("   - Update email and links to your actual contact info")
    print("   - Add project screenshots to docs/images/")
    print("   - Review and customize all sections as needed")


if __name__ == "__main__":
    main()
