"""
Autoclaw — PlannerAgent Testleri
analyze() çıktısının geçerli bir ProjectSpec olduğunu doğrular.
"""

import os
import sys
import pytest

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from models.schemas import ProjectSpec, FileSpec


class TestFileSpec:
    """FileSpec validasyon testleri."""

    def test_valid_file_spec(self):
        """Geçerli FileSpec hatasız oluşturulmalı."""
        fs = FileSpec(path="app.py", purpose="Ana uygulama", language="python")
        fs.validate()  # Hata fırlatmamalı

    def test_empty_path_raises(self):
        """Boş path ValueError fırlatmalı."""
        fs = FileSpec(path="", purpose="Test", language="python")
        with pytest.raises(ValueError, match="path boş olamaz"):
            fs.validate()

    def test_empty_purpose_raises(self):
        """Boş purpose ValueError fırlatmalı."""
        fs = FileSpec(path="app.py", purpose="", language="python")
        with pytest.raises(ValueError, match="purpose boş olamaz"):
            fs.validate()


class TestProjectSpec:
    """ProjectSpec validasyon ve from_dict testleri."""

    VALID_DATA = {
        "project_name": "todo-app",
        "description": "Basit bir görev takip uygulaması",
        "tech_stack": ["python", "flask"],
        "architecture": "MVC pattern",
        "files": [
            {"path": "app.py", "purpose": "Ana uygulama giriş noktası", "language": "python"},
            {"path": "models.py", "purpose": "Veritabanı modelleri", "language": "python"},
            {"path": "requirements.txt", "purpose": "Bağımlılıklar", "language": "text"},
        ],
    }

    def test_from_dict_valid(self):
        """Geçerli dict'ten ProjectSpec oluşturulmalı."""
        spec = ProjectSpec.from_dict(self.VALID_DATA)
        assert spec.project_name == "todo-app"
        assert len(spec.files) == 3
        assert "flask" in spec.tech_stack

    def test_from_dict_missing_name_raises(self):
        """project_name eksikse ValueError fırlatmalı."""
        data = {**self.VALID_DATA, "project_name": ""}
        with pytest.raises(ValueError, match="project_name boş olamaz"):
            ProjectSpec.from_dict(data)

    def test_from_dict_empty_tech_stack_raises(self):
        """tech_stack boşsa ValueError fırlatmalı."""
        data = {**self.VALID_DATA, "tech_stack": []}
        with pytest.raises(ValueError, match="tech_stack en az 1"):
            ProjectSpec.from_dict(data)

    def test_from_dict_no_files_raises(self):
        """files boşsa ValueError fırlatmalı."""
        data = {**self.VALID_DATA, "files": []}
        with pytest.raises(ValueError, match="files en az 1"):
            ProjectSpec.from_dict(data)

    def test_file_spec_default_language(self):
        """language belirtilmezse 'python' varsayılan olmalı."""
        data = {
            **self.VALID_DATA,
            "files": [{"path": "app.py", "purpose": "Ana uygulama"}],
        }
        spec = ProjectSpec.from_dict(data)
        assert spec.files[0].language == "python"


class TestPlannerAgentIntegration:
    """PlannerAgent uçtan uca testi (API anahtarı gerektirir)."""

    def test_analyze_todo_app(self):
        """Gerçek bir fikir ile ProjectSpec üretilmeli."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "buraya_anahtarini_yaz":
            pytest.skip("Geçerli OPENAI_API_KEY bulunamadı — entegrasyon testi atlanıyor.")

        from core.llm_client import LLMClient
        from agents.planner_agent import PlannerAgent

        llm = LLMClient(api_key=api_key)
        planner = PlannerAgent(llm)
        spec = planner.analyze("Basit bir Todo uygulaması yap")

        # Temel alanlar dolu olmalı
        assert spec.project_name, "project_name boş döndü"
        assert spec.description, "description boş döndü"
        assert len(spec.tech_stack) >= 1, "tech_stack boş"
        assert len(spec.files) >= 3, "En az 3 dosya planlanmalı"

        # Her dosyanın path ve purpose alanı dolu olmalı
        for f in spec.files:
            assert f.path, f"Dosya path boş: {f}"
            assert f.purpose, f"Dosya purpose boş: {f.path}"
