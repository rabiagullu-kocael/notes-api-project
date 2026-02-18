
# 📝 Notes API – FastAPI & MongoDB

FastAPI ve MongoDB Atlas kullanılarak geliştirilmiş, etiket destekli, referans modeli kullanan RESTful bir Not Yönetim API’sidir.

Bu proje, NoSQL veri modelleme prensipleri ve modern backend mimarisi esas alınarak tasarlanmıştır.

---

## 📌 Projenin Amacı

Bu sistem kullanıcıların:

* Not oluşturabilmesini
* Her nota birden fazla etiket ekleyebilmesini
* Mevcut olmayan etiketlerin otomatik oluşturulmasını
* Etikete göre not filtreleyebilmesini
* Etiketlerin kaç notta kullanıldığını görebilmesini

sağlayan ölçeklenebilir bir backend servisi sunar.

---

## 🏗 Kullanılan Teknolojiler

| Teknoloji     | Açıklama                                           |
| ------------- | -------------------------------------------------- |
| FastAPI       | Modern ve yüksek performanslı Python web framework |
| MongoDB Atlas | Cloud tabanlı NoSQL veritabanı                     |
| PyMongo       | MongoDB resmi Python driver                        |
| Uvicorn       | ASGI server                                        |
| python-dotenv | Environment değişken yönetimi                      |

---

## 🗂 Veritabanı Mimarisi

Sistem relational bir veritabanı kullanmaz. Bunun yerine MongoDB referans modeli uygulanmıştır.

### Koleksiyonlar

---

### 1️⃣ `users`

```json
{
  "_id": ObjectId,
  "name": "Rabia"
}
```
<img width="1839" height="574" alt="mongodb_kullanicilar" src="https://github.com/user-attachments/assets/70cc3943-b127-4819-ac55-e5dc4b782751" />




Her not bir kullanıcıya aittir.
`notes.userId` alanı bu koleksiyona referans verir.

---

### 2️⃣ `labels`

```json
{
  "_id": ObjectId,
  "name": "finans"
}
```

<img width="1901" height="742" alt="mongodb_labels" src="https://github.com/user-attachments/assets/ba68c052-7236-4b3c-b242-ed29824816ef" />


Etiketler ayrı bir koleksiyonda tutulur.
Aynı etiket birden fazla notta kullanılabilir.

---

### 3️⃣ `notes`

```json
{
  "_id": ObjectId,
  "title": "Yatırım Planı",
  "content": "Uzun vadeli strateji",
  "userId": ObjectId,
  "labels": [ObjectId],
  "createdAt": ISODate
}
```
<img width="1908" height="719" alt="mongodb_notlar" src="https://github.com/user-attachments/assets/e1a684b7-29e5-4e46-813e-c85a61c685ee" />


### Veri Modeli Özellikleri

* `userId` → users koleksiyonuna referans
* `labels` → labels koleksiyonuna referans (many-to-many)
* `createdAt` → otomatik zaman damgası

Bu yapı NoSQL ortamında referans bazlı many-to-many ilişki modelini uygular.

---

## 🔗 İlişki Modeli

* Bir kullanıcı → Birden fazla nota sahip olabilir
* Bir not → Birden fazla etikete sahip olabilir
* Bir etiket → Birden fazla notta kullanılabilir

Bu tasarım veri tekrarını önler ve ölçeklenebilirliği artırır.

---

##  API Endpoint'leri
<img width="1919" height="841" alt="genel" src="https://github.com/user-attachments/assets/5b69b27b-ae99-4f1a-a9f3-d69c4fdc0d40" />

---

### 🟢 POST /notes

Yeni bir not oluşturur.

<img width="1870" height="811" alt="not_ekleme" src="https://github.com/user-attachments/assets/c09ff6e6-d293-457e-b061-248e3ebd2551" />

<img width="1765" height="219" alt="not_ekleme_sonucu" src="https://github.com/user-attachments/assets/ba749d9b-d0c6-4985-bed8-214eccfdb943" />


#### Özellikler:

* Gönderilen etiketler kontrol edilir
* Mevcut değilse otomatik oluşturulur
* Mevcutsa tekrar oluşturulmaz
* createdAt alanı otomatik atanır

#### Örnek Request

```json
{
  "title": "Yapay Zeka Giriş Görevlerim",
  "content": "LLM araştırması tamamlandı.",
  "userId": "69962451a2a86c29d2968808",
  "labels": ["llm araştırması", "rag mimarisi"]
}
```

---

### 🟢 GET /notes

Tüm notları listeler.

<img width="1883" height="820" alt="userid_ve_label_filreleme" src="https://github.com/user-attachments/assets/bd4f66fb-668d-42c4-b99f-8c5314f00dd1" />


<img width="1809" height="485" alt="filtreleme_sonucu" src="https://github.com/user-attachments/assets/f850da3a-a26e-41ea-b198-83193b407450" />


---

### 🟢 GET /notes?label=Finans

Belirli bir etikete sahip notları filtreler.

<img width="1918" height="674" alt="label_filtreleme" src="https://github.com/user-attachments/assets/4a579216-9635-4949-8711-6a1942edfcc6" />

<img width="1772" height="345" alt="label_filtreleme_sonucu" src="https://github.com/user-attachments/assets/32d3d30b-ca28-4a60-86c8-c6c198fb047b" />




#### Çalışma Mantığı:

1. Label adı labels koleksiyonunda aranır
2. İlgili ObjectId alınır
3. notes koleksiyonunda filtre uygulanır

---

### 🟢 GET /labels

Tüm etiketleri ve kullanım sayılarını listeler.

<img width="1800" height="413" alt="labels_goruntuleme" src="https://github.com/user-attachments/assets/05ce3bb3-f323-4520-a057-e1aba57662c4" />

<img width="1769" height="513" alt="labels_ve_toplam_etiket_sayisi" src="https://github.com/user-attachments/assets/2225c650-4aa2-4cbd-8d0e-6418a0af936b" />



---

##  Aggregation Kullanımı

Etiketlerin kaç notta kullanıldığını hesaplamak için MongoDB Aggregation Pipeline kullanılmıştır.

### İşleyiş:

* `$lookup` ile notes koleksiyonu bağlanır
* `$size` ile not sayısı hesaplanır
* `noteCount` alanı oluşturulur

Bu yapı MongoDB join benzeri işlem sağlar.

---

## ⚙️ Kurulum

### 1️⃣ Projeyi klonlayın

```bash
git clone <repo-url>
cd note-project-api
```

### 2️⃣ Sanal ortam oluşturun

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Gereksinimleri yükleyin

```bash
pip install -r requirements.txt
```

### 4️⃣ .env dosyası oluşturun

```env
MONGO_URI=your_connection_string
DB_NAME=note_app_db
```

### 5️⃣ Uygulamayı başlatın

```bash
uvicorn main:app --reload
```

Swagger arayüzü:

```
http://127.0.0.1:8000/docs
```

---

## 📐 Tasarım Kararları

* Etiketler ayrı koleksiyonda tutulmuştur (veri tekrarını önlemek için)
* Referans modeli tercih edilmiştir (embed yerine)
* Aggregation kullanılarak analitik veri üretilmiştir
* Environment değişkenleri ile güvenli bağlantı sağlanmıştır
* REST prensiplerine uygun endpoint tasarımı yapılmıştır

---



---

##  Sonuç

Bu proje:

* NoSQL veri modelleme
* FastAPI ile REST servis geliştirme
* MongoDB referans ilişkileri
* Aggregation pipeline kullanımı

konularında uygulamalı bir backend çalışmasıdır.



