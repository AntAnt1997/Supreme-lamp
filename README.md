# MediAI — 24/7 AI Medical Workers Platform

> 🚀 Now in Beta — Join 10,000+ users

A full-stack platform that gives everyone a personal AI health team — always on, always ready. Get instant symptom analysis, medication reminders, appointment scheduling, and continuous health monitoring around the clock.

[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-green)](#)
[![256-bit Encryption](https://img.shields.io/badge/Encryption-256--bit-blue)](#)
[![Rating](https://img.shields.io/badge/Rating-4.9%2F5-yellow)](#)
[![Availability](https://img.shields.io/badge/Availability-24%2F7-brightgreen)](#)

## Features

- **AI Symptom Analysis** — Advanced AI analyzes your symptoms and provides instant preliminary assessments based on medical knowledge.
- **Smart Scheduling** — Automatically schedule appointments with the right specialists based on your medical needs.
- **Medication Reminders** — Never miss a dose with intelligent medication tracking and personalized reminder systems.
- **Medical Records** — Securely store, organize, and share your medical records with healthcare providers instantly.
- **24/7 Health Chat** — Chat with AI medical workers any time of day or night for immediate health guidance.
- **Health Monitoring** — Continuous monitoring of your health metrics with proactive alerts and recommendations.

## Medical Specialties Covered

| Specialty | Coverage |
|-----------|----------|
| 🏥 General Medicine | 500+ conditions |
| 🧠 Mental Health | 200+ conditions |
| ❤️ Cardiology | 150+ conditions |
| 👶 Pediatrics | 300+ conditions |
| 🔬 Dermatology | 400+ conditions |
| 🥗 Nutrition | 100+ plans |
| 🦴 Orthopedics | 200+ conditions |
| ⚡ Neurology | 180+ conditions |

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/AntAnt1997/Supreme-lamp.git
cd Supreme-lamp
```

### 2. Backend Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python -m bot.main
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server starts at `http://localhost:5173` and the backend API at `http://localhost:8080`.

## Architecture

```
.
├── frontend/                    # React + TypeScript + Vite frontend
│   └── src/
│       ├── components/
│       │   ├── layout/          # Navbar, Footer
│       │   └── sections/        # Hero, Features, HowItWorks, Pricing,
│       │                        # Specialties, Testimonials, FAQ
│       └── pages/               # Home, NotFound
│
└── bot/                         # Python backend
    ├── main.py                  # Entry point
    ├── ai/                      # AI/ML pipeline
    ├── dashboard/               # FastAPI web API & dashboard
    ├── database/                # SQLAlchemy ORM models
    └── notifications/           # Notification services
```

## How It Works

1. **Create Your Profile** — Sign up and complete your medical profile including health history, current medications, and preferences.
2. **Connect with AI Workers** — AI medical workers are instantly assigned to your case, available around the clock for your needs.
3. **Get Continuous Care** — Receive ongoing support, monitoring, and guidance from your dedicated AI medical team 24/7.

## Pricing

| Plan | Price | Highlights |
|------|-------|------------|
| **Basic** | $9/month | AI symptom checker, medication reminders, basic health monitoring, 1 user profile |
| **Pro** | $29/month | Everything in Basic + 24/7 AI health chat, smart scheduling, medical records, up to 5 profiles |
| **Enterprise** | $99/month | Everything in Pro + unlimited profiles, custom AI workflows, EHR integration, HIPAA compliance tools |

All plans include a **14-day free trial**. No hidden fees. Cancel anytime.

## Configuration

All settings are configured via the `.env` file. See `.env.example` for all available options.

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

**Frontend**
- React 18 + TypeScript — UI framework
- Vite — Build tool
- Tailwind CSS — Styling
- shadcn/ui — Component library

**Backend**
- Python 3.10+ — Core language
- FastAPI — REST API
- SQLAlchemy — Database ORM (SQLite)
- scikit-learn — ML models
- APScheduler — Task scheduling
- cryptography — Data encryption

## Security & Compliance

- **HIPAA Compliant** — Designed to meet HIPAA requirements for healthcare data
- **256-bit Encryption** — All data encrypted at rest and in transit
- **Secure Records** — Medical records shared only with explicit user authorization

## Disclaimer

MediAI is an AI-assisted health information tool and is **not a substitute for professional medical advice, diagnosis, or treatment**. Always consult a qualified healthcare provider for medical decisions.
