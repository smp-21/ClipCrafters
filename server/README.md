# 🎬 ClipCrafters — AI Agentic Video Editing System

[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org)
[![Express](https://img.shields.io/badge/Express-4.x-blue)](https://expressjs.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.x-brightgreen)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> Upload research papers, lecture notes, or raw text — ClipCrafters' AI pipeline generates a full video with scenes, voiceovers, and visuals. Every scene is independently editable.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Node.js + Express.js |
| Database | MongoDB + Mongoose |
| AI Pipeline | FastAPI (Python) |
| Frontend | React (MERN) |
| Auth | JWT (jsonwebtoken) |
| File Uploads | Multer |
| AI HTTP Client | Axios |
| Security | Helmet + CORS + Rate Limiting |

---

## 📁 Folder Structure

```
server/
├── server.js               # Entry point (connects DB, starts server)
├── .env                    # Local secrets (git-ignored)
├── .env.example            # Template
└── src/
    ├── app.js              # Express app factory
    ├── config/
    │   ├── database.js     # Mongoose connection
    │   └── env.js          # Validated env config
    ├── constants/
    │   └── roles.js
    ├── controllers/        # HTTP layer — thin, delegates to services
    │   ├── auth.controller.js
    │   ├── project.controller.js
    │   ├── video.controller.js
    │   ├── scene.controller.js
    │   └── edit.controller.js
    ├── middlewares/
    │   ├── auth.middleware.js      # JWT protect + RBAC restrictTo
    │   ├── error.middleware.js     # Global error + 404 handler
    │   ├── upload.middleware.js    # Multer disk storage
    │   └── rateLimit.middleware.js # API + auth rate limits
    ├── models/             # Mongoose schemas
    │   ├── User.js
    │   ├── Project.js
    │   ├── Video.js
    │   ├── Scene.js
    │   ├── EditHistory.js
    │   └── AIGeneration.js
    ├── routes/
    │   ├── auth.routes.js
    │   ├── project.routes.js
    │   ├── video.routes.js
    │   ├── scene.routes.js
    │   └── edit.routes.js
    ├── services/           # Business logic
    │   ├── auth.service.js
    │   ├── project.service.js
    │   ├── video.service.js
    │   ├── scene.service.js
    │   └── ai.service.js   # FastAPI communication
    ├── utils/
    │   ├── asyncHandler.js
    │   ├── apiResponse.js
    │   └── logger.js
    └── validators/
        ├── auth.validator.js
        └── project.validator.js
```

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
cd server
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in MONGO_URI, JWT_SECRET, FASTAPI_URL, etc.
```

### 3. Start development server

```bash
npm run dev
```

### 4. Health check

```
GET http://localhost:5000/api/health
```

---

## 📡 API Reference

### Authentication — `/api/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ❌ | Create user account |
| POST | `/login` | ❌ | Login, returns JWT |
| GET | `/me` | ✅ | Get own profile |

**Register**
```json
POST /api/auth/register
{
  "name": "Fenil Chodvadiya",
  "email": "fenil@example.com",
  "password": "securePass123"
}
```

**Login**
```json
POST /api/auth/login
{
  "email": "fenil@example.com",
  "password": "securePass123"
}
// Response: { "token": "eyJ...", "user": { ... } }
```

---

### Projects — `/api/projects`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create` | Create a new project |
| GET | `/` | List user's projects (paginated) |
| GET | `/:id` | Get project with videos populated |
| PUT | `/:id` | Update project |
| DELETE | `/:id` | Delete project |

**Create Project**
```json
POST /api/projects/create
Authorization: Bearer <token>
{
  "title": "My Research Paper",
  "description": "Converts paper to video",
  "sourceType": "research-paper"
}
```

---

### Videos — `/api/videos`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Submit text → start AI generation |
| POST | `/upload` | Upload file → start AI generation |
| GET | `/:id` | Get video with scenes |

**Generate from text**
```json
POST /api/videos/generate
Authorization: Bearer <token>
{
  "text": "Attention is all you need...",
  "projectId": "64abc...",
  "title": "Attention Paper Video"
}
// Response: 202 Accepted — video stub returned, generation runs async
```

---

### Scenes — `/api/scenes`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/video/:videoId` | Get all scenes ordered by sceneNumber |
| PUT | `/:sceneId` | Edit a scene (auto-records EditHistory) |

**Update Scene**
```json
PUT /api/scenes/:sceneId
Authorization: Bearer <token>
{
  "editType": "script",
  "scriptText": "Updated narration text here."
}
```

---

### Edit History — `/api/edits`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create` | Manually log an edit |
| GET | `/scene/:sceneId` | Get full edit history for a scene |

---

## 🔐 Authentication

All protected routes require:
```
Authorization: Bearer <JWT_TOKEN>
```

Token is returned on `/api/auth/login` and `/api/auth/register`.

---

## 🛡️ Security Features

- **Helmet** — HTTP security headers
- **CORS** — Origin-whitelisted via `CORS_ORIGIN` env var
- **Rate Limiting** — 100 req/15min globally, 10 req/15min on auth routes
- **JWT** — Stateless auth, `select: false` on passwords
- **Input Validation** — Schema-based validators before controllers

---

## 🤖 AI Pipeline

```
User Input
  ↓
POST /api/videos/generate
  ↓
Video stub created (status: processing)
  ↓
[Background] FastAPI /generate-script
  ↓
[Background] FastAPI /generate-scenes
  ↓
Scenes saved to DB
  ↓
Video status → completed
  ↓
Every AI call logged in AIGeneration collection
```

---

## 📦 Environment Variables

See `.env.example` for the full list.

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | ✅ | MongoDB connection string |
| `JWT_SECRET` | ✅ | Secret for signing tokens |
| `FASTAPI_URL` | ✅ | AI service base URL |
| `PORT` | ❌ | Server port (default: 5000) |
| `CORS_ORIGIN` | ❌ | Allowed frontend origin |
| `MAX_FILE_SIZE` | ❌ | Upload size limit in bytes |
