# FHIR Transformer — CSV/API → FHIR R4

Web uygulaması; CSV dosyasından veya JSON REST API kaynağından alınan kayıtları kullanıcı tarafından tanımlanan eşleştirme kurallarıyla FHIR R4 kaynaklarına dönüştürür, doğrular, hataları raporlar ve çıktıyı FHIR JSON ya da Bundle olarak indirilmesini sağlar.

## Mimari

```
React + TypeScript + Tailwind
         │ REST / JSON
         ▼
FastAPI API Katmanı
 ├── Auth / Project / Source / Mapping API
 ├── Preview ve Senkron Validasyon
 │
 ├──▶ PostgreSQL (metadata, mapping, job, issue)
 ├──▶ Object Storage (geçici CSV ve çıktı dosyaları)
 ├──▶ Worker (dönüşüm ve toplu validasyon)
 └──▶ FHIR Validator Servisi
```

## Hızlı Başlangıç

### Gereksinimler

- Docker & Docker Compose
- Node.js 22+ (frontend geliştirme için)
- Python 3.12+ (backend geliştirme için)

### Kurulum

```bash
# 1. Repoyu klonlayın
git clone <repo-url>
cd health_data_transform

# 2. Ortam değişkenlerini ayarlayın
cp .env.example .env

# 3. Docker ile başlatın
docker compose up --build

# Veya bağımsız geliştirme:

# Backend
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Endpoints

| URL | Açıklama |
|-----|----------|
| http://localhost:5173 | Frontend |
| http://localhost:8000/docs | API Docs (Swagger) |
| http://localhost:8000/health | Health Check |

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 |
| Backend | FastAPI + Pydantic v2 |
| Veritabanı | PostgreSQL 16 + SQLAlchemy 2 + Alembic |
| Auth | JWT (python-jose) + bcrypt |
| HTTP İstemcisi | HTTPX |
| Test | Pytest + Vitest |
| Deploy | Docker + Cloud Run |

## Proje Yapısı

```
health_data_transform/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # HTTP endpoints ve schemas
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # Models, session, repository
│   │   ├── ingestion/      # CSV/API okuma (Hafta 2-6)
│   │   ├── mapping/        # Transform motoru (Hafta 3)
│   │   ├── fhir/           # FHIR builder (Hafta 3-4)
│   │   ├── jobs/           # İş orkestrasyon (Hafta 4)
│   │   ├── storage/        # Dosya adaptör (Hafta 2)
│   │   └── security/       # SSRF, maskeleme (Hafta 6-8)
│   ├── alembic/            # DB migration
│   ├── tests/              # Pytest
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/     # UI bileşenleri
│   │   ├── pages/          # Sayfa bileşenleri
│   │   ├── lib/            # API client, auth context
│   │   └── types/          # TypeScript arayüzleri
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## FHIR Kaynakları

MVP aşamasında desteklenen kaynaklar:

- **Patient** — Hasta demografik bilgileri
- **Observation** — Laboratuvar sonuçları ve ölçümler

FHIR sürümü: **R4 (4.0.1)**

## Lisans

Bu proje özel kullanım içindir.