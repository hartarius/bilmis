# 🔮 BİLMİŞ — Her Şeyi Bilen Tahmin Oyunu

*Akinator benzeri, Gemini destekli, her şeyi tahmin edebilen web oyunu.*

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fhartarius%2Fbilmis&env=OPENROUTER_API_KEY&envDescription=OpenRouter%20API%20Key%20-%20gemini%20i%C3%A7in%20kotan%C4%B1z%20kullan%C4%B1r)

## Nasıl Çalışır?

1. Aklından bir şey tut (eşya, hayvan, ünlü, yer, film, karakter...)
2. BİLMİŞ'e söyle (gizli — sadece ikiniz biliyorsunuz)
3. BİLMİŞ 15-20 soru sorarak aklındakini "tahmin eder"
4. Her seferinde %100 doğru bilir! 🎯

## Başlatma

### 1. Gereksinimler

- Python 3.10+
- Google Gemini API key ([ai.google.dev](https://ai.google.dev)'den al)

### 2. Backend

```bash
cd backend

# Sanal ortam kur (ilk sefer)
python3 -m venv venv
source venv/bin/activate

# Paketleri yükle
pip install -r requirements.txt

# .env dosyasına Gemini API key'ini ekle
echo "GEMINI_API_KEY=your-key-here" > .env

# Backend'i başlat
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend

# Basit HTTP sunucu
python3 -m http.server 3000
```

### 4. Oyna!

Tarayıcıdan **http://localhost:3000** aç.

## API Endpoint'leri

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/api/health` | Sağlık kontrolü |
| POST | `/api/new-game` | Yeni oyun başlat `{secret: "..."}` |
| POST | `/api/answer` | Soruya cevap ver `{session_id, answer}` |

## Teknoloji

- **Backend:** Python FastAPI + Google Gemini 2.0 Flash
- **Frontend:** Vanilla HTML/CSS/JS (zero framework)
- **Tema:** Koyu mistik mor-altın

## Proje Yapısı

```
bilmis/
├── backend/
│   ├── main.py          # FastAPI app + endpoint'ler
│   ├── game.py           # GameEngine (Gemini entegrasyonu)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html        # Oyun arayüzü
│   ├── style.css         # Koyu tema + animasyonlar
│   └── app.js            # Oyun mantığı + API çağrıları
└── README.md
```
