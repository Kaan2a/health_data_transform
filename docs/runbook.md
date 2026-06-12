# Runbook — Sorun Giderme Rehberi

## Backend Çalışmıyorsa

1. **Logları kontrol edin:**
   ```bash
   docker-compose logs backend
   # veya
   uvicorn app.main:app --reload 2>&1 | tail -50
   ```

2. **Health check yapın:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Veritabanı bağlantısını test edin:**
   ```bash
   psql -U fhir_user -d fhir_transformer -c "SELECT 1"
   ```

4. **Migration durumunu kontrol edin:**
   ```bash
   cd backend && alembic current
   ```

5. **Sorun devam ederse:**
   - `.env` dosyasını kontrol edin
   - `DATABASE_URL` formatını doğrulayın
   - Port çakışmasını kontrol edin (`netstat -an | grep 8000`)

## Worker Kuyruğu Takıldıysa

1. **Aktif job'ları kontrol edin:**
   ```sql
   SELECT id, status, progress, error_message 
   FROM transformation_jobs 
   WHERE status IN ('pending', 'running') 
   ORDER BY created_at DESC;
   ```

2. **Takılı job'ları iptal edin:**
   ```sql
   UPDATE transformation_jobs 
   SET status = 'failed', error_message = 'Manually cancelled' 
   WHERE status IN ('pending', 'running') 
   AND created_at < NOW() - INTERVAL '1 hour';
   ```

## FHIR Sunucusu Erişilemiyorsa

1. **Sunucu erişilebilirliğini test edin:**
   ```bash
   curl -f https://your-fhir-server/metadata
   ```

2. **SSRF ayarlarını kontrol edin:**
   - Production'da yalnızca HTTPS kabul edilir
   - Dahili IP'ler engellenir

3. **Timeout değerlerini gözden geçirin:**
   ```
   FHIR_CONNECT_TIMEOUT_SECONDS=10
   FHIR_READ_TIMEOUT_SECONDS=60
   ```

## Migration Başarısız Olursa

1. **Mevcut durumu kontrol edin:**
   ```bash
   alembic current
   alembic history --verbose
   ```

2. **Son migration'ı geri alın:**
   ```bash
   alembic downgrade -1
   ```

3. **Migration dosyasını kontrol edin ve düzeltin**

4. **Yeniden deneyin:**
   ```bash
   alembic upgrade head
   ```
