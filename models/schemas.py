"""
Autoclaw — Veri Modelleri (Schemas)
Ajanlar arası veri alışverişinde kullanılan yapılar.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileSpec:
    """Üretilecek tek bir dosyanın spesifikasyonu."""
    path: str           # Örn: "app.py", "models/user.py"
    purpose: str        # Dosyanın amacı (1-2 cümle)
    language: str = "python"  # Programlama dili

    def validate(self) -> None:
        """Zorunlu alanları kontrol eder."""
        if not self.path or not self.path.strip():
            raise ValueError("FileSpec.path boş olamaz.")
        if not self.purpose or not self.purpose.strip():
            raise ValueError(f"FileSpec.purpose boş olamaz: {self.path}")


@dataclass
class ProjectSpec:
    """
    PlannerAgent'ın ürettiği proje spesifikasyonu.
    Bir uygulama fikrinin teknik planını temsil eder.
    """
    project_name: str           # Örn: "todo-app"
    description: str            # Proje açıklaması
    tech_stack: List[str]       # Örn: ["python", "flask", "sqlite"]
    files: List[FileSpec]       # Üretilecek dosyalar
    architecture: str = ""      # Mimari notlar (opsiyonel)

    def validate(self) -> None:
        """Tüm zorunlu alanları kontrol eder."""
        if not self.project_name or not self.project_name.strip():
            raise ValueError("ProjectSpec.project_name boş olamaz.")
        if not self.description or not self.description.strip():
            raise ValueError("ProjectSpec.description boş olamaz.")
        if not self.tech_stack:
            raise ValueError("ProjectSpec.tech_stack en az 1 eleman içermeli.")
        if not self.files:
            raise ValueError("ProjectSpec.files en az 1 dosya içermeli.")
        for f in self.files:
            f.validate()

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectSpec":
        """
        JSON dict'ten ProjectSpec oluşturur.

        Args:
            data: LLM'den dönen parse edilmiş JSON.

        Returns:
            ProjectSpec nesnesi.
        """
        files = [
            FileSpec(
                path=f.get("path", ""),
                purpose=f.get("purpose", ""),
                language=f.get("language", "python"),
            )
            for f in data.get("files", [])
        ]

        spec = cls(
            project_name=data.get("project_name", ""),
            description=data.get("description", ""),
            tech_stack=data.get("tech_stack", []),
            files=files,
            architecture=data.get("architecture", ""),
        )
        spec.validate()
        return spec
