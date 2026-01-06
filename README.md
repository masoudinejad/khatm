# Collective Recitation Platform

[![Backend CI](https://github.com/yourusername/your-repo/workflows/Backend%20CI/badge.svg)](https://github.com/yourusername/your-repo/actions)
[![codecov](https://codecov.io/gh/yourusername/your-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/your-repo)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive platform for organizing collective recitation of the Holy Quran and Islamic texts, enabling communities to coordinate and track their spiritual practices together.

## 🏗️ Project Structure

This is a monorepo containing:

- **Backend**: FastAPI REST API (Python 3.12+)
- **Mobile**: React Native app (iOS & Android)
- **Web**: Next.js web application

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- UV (Python package manager)
- Expo CLI (for mobile development)

### Running the Backend

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

API will be available at http://localhost:8000

### Running the Mobile App

```bash
cd mobile
npm install
npm start
```

Press `i` for iOS simulator or `a` for Android emulator.

### Running the Web App

```bash
cd web
npm install
npm run dev
```

Web app will be available at http://localhost:3000

## 📚 Documentation

- [Architecture Overview](./docs/ARCHITECTURE.md)
- [API Documentation](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Contributing Guidelines](./docs/CONTRIBUTING.md)

Each component also has its own README:
- [Backend README](./backend/README.md)
- [Mobile README](./mobile/README.md)
- [Web README](./web/README.md)

## 🌟 Features

### Backend
- User authentication (email/phone)
- Dynamic content type management
- Progress tracking with history
- Multi-language support
- Admin capabilities

### Mobile App
- Native iOS and Android apps
- Offline-first architecture
- Push notifications
- Real-time progress updates
- Beautiful, intuitive UI

### Web App
- Responsive design
- Real-time dashboard
- Admin panel
- Statistics and analytics
- Multi-language support

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: JWT
- **Package Manager**: UV

### Apps
- **Framework**: React Native with Expo
- **Navigation**: React Navigation
- **State Management**: React Query
- **Storage**: AsyncStorage
- **Language**: TypeScript

### Web
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI
- **State Management**: React Query
- **Language**: TypeScript

## 🌍 Multi-language Support

- Arabic (العربية)
- Farsi (فارسی)
- Urdu (اردو)
- English
- Turkish (Türkçe)
- Azerbaijani (Azərbaycan)

## 📱 Supported Platforms

- **Web**: All modern browsers
- **Mobile**: iOS 13+, Android 8+

## 🔒 Security

- JWT-based authentication
- Password hashing (SHA-256)
- Environment-based configuration
- Secure API endpoints

## 🤝 Contributing

Please read [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

This project is created to facilitate spiritual practices and strengthen community bonds through collective worship.

**Ya Ali (AS) Madad** 🤲

---

For detailed setup and development instructions, see the README in each component directory.


## 📦 Shared Types (Optional)

If you want to share types between frontend and backend:
```bash
cd shared
npm init -y

# Create TypeScript config
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "declaration": true,
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["types/**/*", "constants/**/*", "utils/**/*"]
}
EOF

# Create types
mkdir -p types

cat > types/index.ts << 'EOF'
export interface User {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  preferred_language: string;
}

export interface Recitation {
  id: number;
  title: string;
  description?: string;
  content_type: string;
  portion_type: string;
  total_portions: number;
  status: 'active' | 'completed';
  language: string;
  creator_id: number;
  created_at: string;
}

export interface Portion {
  id: number;
  recitation_id: number;
  portion_number: number;
  user_id?: number;
  progress_percentage: number;
  is_completed: boolean;
  assigned_at?: string;
  completed_at?: string;
}

export interface ContentType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  default_portion_types: Record<string, number>;
  is_active: boolean;
}
EOF
```

## 🐳 Docker Compose (Optional)

For local development with all services:
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://user:password@db:5432/recitations
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uv run uvicorn src.main:app --host 0.0.0.0 --reload

  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./web:/app
      - /app/node_modules
    command: npm run dev

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=recitations
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Run everything with:
```bash
docker-compose up
```

## 📊 Development Workflow

### 1. Start Backend
```bash
cd backend && uv run uvicorn src.main:app --reload
```

### 2. Start Web
```bash
cd web && npm run dev
```

### 3. Start Mobile
```bash
cd mobile && npm start
```

### 4. Access Services
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- Web App: http://localhost:3000
- Mobile: Expo Dev Client

## 🔄 CI/CD

GitHub Actions workflows are set up for each component:
- `backend-ci.yml`: Runs tests and linting for backend
- `mobile-ci.yml`: Builds mobile app
- `web-ci.yml`: Builds and tests web app

## 📈 Future Enhancements

- [ ] GraphQL API option
- [ ] Real-time updates with WebSockets
- [ ] Social features (friends, groups)
- [ ] Gamification (achievements, leaderboards)
- [ ] Audio recitation playback
- [ ] Offline mode for mobile
- [ ] Admin dashboard in web app
- [ ] Email/SMS notifications
- [ ] Analytics and reporting

---

Each directory (`backend/`, `apps/`, `web/`) will have its own detailed README with specific setup instructions.