# FHIR Sunucusuna Gönderim

## Gönderim Akışı

1. Kullanıcı tamamlanmış bir dönüşüm job'undan gönderim başlatır
2. Sistem FHIR sunucusunun `/metadata` endpoint'inden `CapabilityStatement` alır
3. NDJSON dosyası okunarak FHIR kaynakları çıkarılır
4. Kaynaklar chunk'lara (parçalara) bölünür
5. Her chunk bir FHIR Bundle olarak gönderilir
6. Sonuçlar `fhir_submission_entries` tablosuna kaydedilir

## Bundle Türleri

### Batch
- Bağımsız kayıtlar için kullanılır
- Kısmi başarı mümkündür
- Bir kaydın başarısızlığı diğerlerini etkilemez

### Transaction
- Birbirine referans veren kaynaklar için kullanılır
- Atomik işlem (ya hep ya hiç)
- Tek bir kayıt başarısız olursa tüm gönderim başarısız olur

## Bundle Parçalama (Chunking)

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `FHIR_BUNDLE_MAX_ENTRIES` | 100 | Chunk başına maksimum kaynak |
| `FHIR_BUNDLE_MAX_SIZE_MB` | 10 | Chunk başına maksimum boyut (MB) |

## Retry Politikası

### Retry Uygulanacak Durumlar
- `429 Too Many Requests`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`
- Connection timeout
- Read timeout

### Retry Uygulanmayacak Durumlar
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- FHIR Validation hataları

### Bekleme Süreleri (Exponential Backoff)
| Deneme | Bekleme |
|--------|---------|
| 1      | 1 saniye |
| 2      | 2 saniye |
| 3      | 4 saniye |

## OperationOutcome

FHIR sunucusu hatalı kayıtlar için `OperationOutcome` kaynağı döner. Bu kaynak:
- `issue[].severity`: Hata seviyesi (error, warning, information)
- `issue[].code`: Hata kodu
- `issue[].diagnostics`: Detaylı hata mesajı

Hata detayları `fhir_submission_entries.operation_outcome` alanında JSON olarak saklanır.
