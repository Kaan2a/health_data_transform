# Backup ve Recovery

## Backup Politikası

### PostgreSQL Backup
- Günlük otomatik yedekleme
- Backup dosyaları şifreli saklanır
- En az 7 günlük günlük backup tutulur
- Haftalık uzun süreli backup alınır

### Object Storage
- Versioning etkinleştirilir
- Lifecycle policy ile eski versiyonlar 30 gün sonra silinir

## Manuel Backup

```bash
# PostgreSQL dump
pg_dump -U fhir_user -d fhir_transformer -F c -f backup_$(date +%Y%m%d).dump

# Şifreli backup
pg_dump -U fhir_user -d fhir_transformer -F c | \
  gpg --symmetric --cipher-algo AES256 > backup_$(date +%Y%m%d).dump.gpg
```

## Recovery Prosedürü

```bash
# 1. Test veritabanı oluştur
createdb -U fhir_user fhir_transformer_restore

# 2. Backup'ı restore et
pg_restore -U fhir_user -d fhir_transformer_restore backup_20260613.dump

# 3. Migration durumunu kontrol et
cd backend
DATABASE_URL=postgresql+asyncpg://fhir_user:pass@localhost:5432/fhir_transformer_restore \
  alembic current

# 4. Eksik migration'ları uygula
DATABASE_URL=postgresql+asyncpg://fhir_user:pass@localhost:5432/fhir_transformer_restore \
  alembic upgrade head

# 5. Smoke test
curl http://localhost:8000/health
```

## Recovery Testi Kontrol Listesi

- [ ] Test veritabanı oluşturuldu
- [ ] Backup restore edildi
- [ ] Migration'lar kontrol edildi
- [ ] Uygulama başarıyla başlatıldı
- [ ] Health check geçti
- [ ] Temel CRUD işlemleri çalışıyor
