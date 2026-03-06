"""
Autoclaw — LLM Client
OpenAI API ile iletişimi soyutlayan modül.
Retry mantığı, hata yönetimi ve loglama içerir.
"""

import os
import time
import json
from openai import OpenAI, APIError, RateLimitError, APIConnectionError


class LLMClient:
    """
    OpenAI API üzerinden LLM çağrıları yapan istemci.

    Özellikler:
    - Otomatik retry (üstel geri çekilme)
    - Rate limit ve API hatalarını yönetme
    - Yapılandırılabilir model ve parametreler
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_RETRIES = 3
    BASE_DELAY = 1  # saniye

    def __init__(self, api_key: str = None, model: str = None):
        """
        Args:
            api_key: OpenAI API anahtarı. None ise .env'den okunur.
            model: Kullanılacak model adı. None ise DEFAULT_MODEL kullanılır.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ OPENAI_API_KEY bulunamadı!\n"
                "   .env dosyasına anahtarını ekle:\n"
                "   OPENAI_API_KEY=sk-..."
            )

        self.model = model or self.DEFAULT_MODEL
        self.client = OpenAI(api_key=self.api_key)

    def chat(self, user_prompt: str, system_prompt: str = None) -> str:
        """
        LLM'e mesaj gönderir ve yanıt döner.

        Args:
            user_prompt: Kullanıcı mesajı.
            system_prompt: Sistem talimatı (opsiyonel).

        Returns:
            LLM'in metin yanıtı.

        Raises:
            RuntimeError: Tüm retry denemeleri başarısız olursa.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return self._call_with_retry(messages)

    def chat_json(self, user_prompt: str, system_prompt: str = None) -> dict:
        """
        LLM'e mesaj gönderir ve JSON yanıt döner.

        Args:
            user_prompt: Kullanıcı mesajı.
            system_prompt: Sistem talimatı (opsiyonel).

        Returns:
            Parse edilmiş JSON dict.

        Raises:
            ValueError: Yanıt geçerli JSON değilse.
            RuntimeError: Tüm retry denemeleri başarısız olursa.
        """
        raw = self.chat(user_prompt, system_prompt)
        return self._parse_json(raw)

    def _call_with_retry(self, messages: list) -> str:
        """
        Üstel geri çekilme (exponential backoff) ile API çağrısı yapar.
        Max 3 deneme, her seferinde bekleme süresi 2x artar.
        """
        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()

            except RateLimitError as e:
                last_error = e
                wait = self.BASE_DELAY * (2 ** (attempt - 1))
                print(f"⏳ Rate limit aşıldı. {wait}s sonra tekrar denenecek... (Deneme {attempt}/{self.MAX_RETRIES})")
                time.sleep(wait)

            except APIConnectionError as e:
                last_error = e
                wait = self.BASE_DELAY * (2 ** (attempt - 1))
                print(f"🔌 Bağlantı hatası. {wait}s sonra tekrar denenecek... (Deneme {attempt}/{self.MAX_RETRIES})")
                time.sleep(wait)

            except APIError as e:
                last_error = e
                print(f"❌ API hatası (HTTP {e.status_code}): {e.message}")
                if e.status_code and e.status_code >= 500:
                    wait = self.BASE_DELAY * (2 ** (attempt - 1))
                    print(f"   Sunucu hatası — {wait}s sonra tekrar denenecek...")
                    time.sleep(wait)
                else:
                    break  # 4xx hataları için retry yapma

        raise RuntimeError(
            f"❌ LLM çağrısı {self.MAX_RETRIES} denemeden sonra başarısız oldu.\n"
            f"   Son hata: {last_error}"
        )

    def _parse_json(self, raw: str) -> dict:
        """
        LLM yanıtından JSON bloğunu çıkarır ve parse eder.
        Markdown fence (```json ... ```) içinde gelebilecek JSON'ı da destekler.
        """
        text = raw.strip()

        # ```json ... ``` fence'ini temizle
        if text.startswith("```"):
            lines = text.split("\n")
            # İlk satırdaki ```json veya ``` 'yi atla
            start = 1
            # Son satırdaki ``` 'yi atla
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            text = "\n".join(lines[start:end]).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"❌ LLM geçerli JSON döndürmedi.\n"
                f"   Parse hatası: {e}\n"
                f"   Ham yanıt:\n{raw[:500]}"
            )
