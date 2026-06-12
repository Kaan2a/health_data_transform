# Deployment Kılavuzu

## Gereksinimler

- Docker & Docker Compose
- PostgreSQL 16+
- Python 3.12+ (backend)
- Node.js 22+ (frontend)

## Environment Değişkenleri

Production ortamında `.env.production.example` dosyasını `.env` olarak kopyalayın ve tüm değişkenleri doğru şekilde ayarlayın.

```bash
cp backend/.env.production.example backend/.env
```

### Zorunlu Değişkenler

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı URL'i |
| `SECRET_KEY` | JWT imzalama için güçlü rastgele anahtar |
| `CORS_ORIGINS` | İzin verilen frontend URL'leri |
| `APP_ENV` | `production` olmalı |
| `DEBUG` | `false` olmalı |

## Database Migration

```bash
cd backend
alembic current          # Mevcut migration durumunu kontrol et
alembic heads            # Bekleyen migration'ları göster
alembic check            # Migration tutarlılığını doğrula
alembic upgrade head     # Tüm migration'ları uygula
```

## Docker ile Deployment

```bash
docker-compose up --build -d
```

## Rollback

```bash
# Son migration'ı geri al
alembic downgrade -1

# Belirli bir revision'a dön
alembic downgrade <revision_id>
```

## Health Check

```bash
curl http://localhost:8000/health
# Beklenen yanıt: {"status": "ok"}
```
