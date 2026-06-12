# Güvenlik Politikası

## SSRF Koruması

Tüm harici API DataSource adresleri otomatik olarak SSRF kontrolünden geçirilir.

### Engellenen Adresler
- `localhost`, `127.0.0.1`, `::1` (Loopback)
- `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x` (Private)
- `169.254.x.x` (Link-local / Cloud Metadata)
- URL içinde kullanıcı adı/parola (örn: `http://admin:pass@host`)

### Ortam Farkları
- **Development:** `SSRF_DEV_ALLOWED_DESTINATIONS` listesindeki adresler hariç tutulur.
- **Production:** Hiçbir istisna yoktur.

## Authentication & Authorization

- JWT tabanlı oturum yönetimi
- Roller: `owner`, `admin`, `viewer`
- Organizasyon bazlı veri izolasyonu (Multi-tenant)
- Başarısız giriş denemeleri Rate Limiting ile sınırlandırılır (5/dakika)

## Secret Yönetimi

- `SECRET_KEY` varsayılan değerle production'da çalışamaz
- Tüm secret'lar `.env` dosyasında tutulur, kaynak koda eklenmez
- `.gitignore` dosyasında `.env` ve `*.sqlite` tanımlıdır

## Hassas Veri Loglama Kuralları

Audit log'a **asla** yazılmaması gereken bilgiler:
- Hasta adı, T.C. Kimlik numarası, doğum tarihi
- Observation sonuçları
- Authorization header, API token, FHIR parolası
- Tam CSV satır içeriği

## Rate Limiting

- Varsayılan limit: `100/minute`
- Login endpoint: `5/minute`
- Rate limit aşıldığında: `429 Too Many Requests`
