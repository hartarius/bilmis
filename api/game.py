"""
BİLMİŞ — Game Engine
OpenRouter API (OpenAI-uyumlu) ile soru üreten ve tahmin yapan oyun motoru.
MiniMax M2.5 (ücretsiz) modelini kullanır.
"""

import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# .env dosyasını mutlak path ile yükle
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

SYSTEM_PROMPT = """Sen BİLMİŞ'sin — mistik, esprili, her şeyi bilen bir varlıksın. 
İnsanların aklından tuttuğu şeyi sorular sorarak tahmin ediyorsun.
GİZLİ KELİME'yi biliyorsun ama oyuncuya bilmediğini hissettirmelisin.

KURALLAR:
- SADECE bir sonraki soruyu veya tahmini yaz, başka hiçbir şey yazma
- Sorular EVET/HAYIR/BİLMİYORUM şeklinde cevaplanabilir olmalı
- Genelden özele doğru ilerle, her soruda yeni ipucu yakala
- Samimi, eğlenceli Türkçe kullan (🤔 🧐 🔍 emojileri serbest)
- 15-20 soru aralığında tahminini yap
- Tahmin mesajına '🎯 TAHMİN:' ile başla
- ASLA GİZLİ KELİME'yi soru olarak sorma
- Sadece soruyu/tahmini yaz, açıklama ekleme"""

MODEL = "minimax/minimax-m2.5:free"
API_BASE = "https://openrouter.ai/api/v1"
APP_NAME = "BILMIS"


class GameEngine:
    """OpenRouter destekli tahmin oyunu motoru."""

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY .env dosyasında tanımlı değil!")
        self.client = OpenAI(
            base_url=API_BASE,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": APP_NAME,
            },
        )

    def start_game(self, secret: str) -> str:
        """İlk soruyu üret."""
        return self._chat(
            secret=secret,
            history=[],
            instruction="Oyuna yeni başlıyoruz. İlk soruyu sor — genel ve merak uyandırıcı olsun. Kısa ve öz."
        )

    def ask_next(self, secret: str, history: list, question_count: int) -> tuple[str, bool]:
        """Bir sonraki soruyu veya tahmini üret."""
        if question_count >= 15:
            instruction = (
                "Artık yeterince ipucun var. Tahminini yap! "
                "Mesajına '🎯 TAHMİN:' ile başla. Eğlenceli ve dramatik açıkla. "
                "Emin değilsen bir soru daha sor."
            )
        else:
            instruction = "Kullanıcının cevabına göre bir sonraki soruyu sor. Cevaplardan mantıklı çıkarımlar yap."

        response = self._chat(secret, history, instruction)
        is_final = "TAHMİN:" in response
        return response, is_final

    def _chat(self, secret: str, history: list, instruction: str) -> str:
        """Chat mesajlarını oluştur ve API'yi çağır."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"GİZLİ KELİME: {secret}"},
        ]

        # Geçmişteki soru-cevapları ekle
        for h in history:
            if h["role"] == "assistant":
                messages.append({"role": "assistant", "content": h["content"]})
            else:
                # Kullanıcı cevabını role:user olarak ekle
                messages.append({"role": "user", "content": f"Cevap: {h['content']}"})

        # Şimdiki instruction'ı ekle
        messages.append({"role": "user", "content": instruction})

        return self._generate(messages)

    def _generate(self, messages: list, max_retries: int = 3) -> str:
        """API çağrısı, retry mekanizmalı."""
        for attempt in range(max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=300,
                    top_p=0.9,
                )
                text = resp.choices[0].message.content
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"API hatası ({attempt + 1}/{max_retries} deneme): {e}")
                time.sleep(1.5 ** attempt)

        raise RuntimeError("API boş yanıt döndü")
