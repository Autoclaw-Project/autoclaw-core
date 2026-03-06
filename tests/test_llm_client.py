"""
Autoclaw — LLMClient Testleri
API bağlantısı ve yanıt formatını doğrular.
"""

import os
import sys
import pytest

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from core.llm_client import LLMClient


class TestLLMClientInit:
    """LLMClient yapılandırma testleri."""

    def test_init_with_valid_key(self):
        """Geçerli API anahtarı ile client oluşturulabilmeli."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "buraya_anahtarini_yaz":
            pytest.skip("Geçerli OPENAI_API_KEY bulunamadı, bu test atlanıyor.")

        client = LLMClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.model == LLMClient.DEFAULT_MODEL

    def test_init_without_key_raises(self):
        """API anahtarı yoksa ValueError fırlatmalı."""
        # Geçici olarak env var'ı kaldır
        original = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY bulunamadı"):
                LLMClient(api_key=None)
        finally:
            if original:
                os.environ["OPENAI_API_KEY"] = original

    def test_custom_model(self):
        """Özel model adı doğru ayarlanmalı."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "buraya_anahtarini_yaz":
            pytest.skip("Geçerli OPENAI_API_KEY bulunamadı.")

        client = LLMClient(api_key=api_key, model="gpt-4o")
        assert client.model == "gpt-4o"


class TestLLMClientJsonParsing:
    """JSON parse testleri (API çağrısı yapmadan)."""

    def setup_method(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "buraya_anahtarini_yaz":
            pytest.skip("Geçerli OPENAI_API_KEY bulunamadı.")
        self.client = LLMClient(api_key=api_key)

    def test_parse_clean_json(self):
        """Temiz JSON string'i başarıyla parse edilmeli."""
        raw = '{"name": "test", "value": 42}'
        result = self.client._parse_json(raw)
        assert result == {"name": "test", "value": 42}

    def test_parse_json_with_markdown_fence(self):
        """Markdown fence içindeki JSON da parse edilmeli."""
        raw = '```json\n{"name": "test"}\n```'
        result = self.client._parse_json(raw)
        assert result == {"name": "test"}

    def test_parse_invalid_json_raises(self):
        """Geçersiz JSON ValueError fırlatmalı."""
        raw = "Bu geçerli JSON değil!"
        with pytest.raises(ValueError, match="geçerli JSON döndürmedi"):
            self.client._parse_json(raw)


class TestLLMClientChat:
    """Gerçek API çağrısı testleri (API anahtarı gerektirir)."""

    def setup_method(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "buraya_anahtarini_yaz":
            pytest.skip("Geçerli OPENAI_API_KEY bulunamadı — API testleri atlanıyor.")
        self.client = LLMClient(api_key=api_key)

    def test_simple_chat(self):
        """Basit bir mesaja yanıt gelmeli."""
        response = self.client.chat("Merhaba, 2+2 kaç eder? Sadece sayıyı yaz.")
        assert response is not None
        assert len(response) > 0
        assert "4" in response

    def test_chat_json(self):
        """JSON formatında yanıt alınmalı."""
        result = self.client.chat_json(
            user_prompt='{"test": true} — bu JSON\'ı aynen döndür.',
            system_prompt="Sadece geçerli JSON döndür, başka hiçbir şey yazma.",
        )
        assert isinstance(result, dict)
