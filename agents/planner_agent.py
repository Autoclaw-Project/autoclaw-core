"""
Autoclaw — Planner Agent
Kullanıcının uygulama fikrini analiz edip yapılandırılmış bir
ProjectSpec (dosya yapısı + teknik spesifikasyon) üreten ajan.
"""

import os
from pathlib import Path

from core.llm_client import LLMClient
from models.schemas import ProjectSpec


class PlannerAgent:
    """
    Doğal dildeki bir uygulama fikrini, yapılandırılmış bir
    teknik plana (ProjectSpec) dönüştürür.

    Kullanım:
        planner = PlannerAgent(llm_client)
        spec = planner.analyze("Bir Todo uygulaması yap")
        print(spec.project_name)  # "todo-app"
    """

    PROMPT_FILE = "prompts/planner_prompt.txt"

    def __init__(self, llm_client: LLMClient):
        """
        Args:
            llm_client: Yapılandırılmış LLMClient instance'ı.
        """
        self.llm = llm_client
        self._system_prompt = self._load_prompt()

    def analyze(self, app_idea: str) -> ProjectSpec:
        """
        Uygulama fikrini analiz eder ve ProjectSpec döner.

        Args:
            app_idea: Kullanıcının doğal dildeki uygulama fikri.

        Returns:
            ProjectSpec: Projenin teknik planı.

        Raises:
            ValueError: LLM yanıtı geçerli bir ProjectSpec değilse.
            RuntimeError: LLM API çağrısı başarısız olursa.
        """
        print("🧠 Fikir analiz ediliyor...")

        # LLM'den JSON yanıt al
        raw_spec = self.llm.chat_json(
            user_prompt=f"Uygulama fikri: {app_idea}",
            system_prompt=self._system_prompt,
        )

        # JSON'ı ProjectSpec nesnesine dönüştür ve doğrula
        spec = ProjectSpec.from_dict(raw_spec)

        print(f"✅ Plan hazır: \"{spec.project_name}\" — {len(spec.files)} dosya planlandı.")
        return spec

    def _load_prompt(self) -> str:
        """
        prompts/planner_prompt.txt dosyasından system prompt'u yükler.
        Dosya bulunamazsa varsayılan bir prompt kullanır.
        """
        # Dosya yolunu main.py'nin bulunduğu dizine göre çözümle
        base_dir = Path(__file__).resolve().parent.parent
        prompt_path = base_dir / self.PROMPT_FILE

        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8").strip()

        # Fallback: Dosya yoksa minimal prompt
        print(f"⚠️  Prompt dosyası bulunamadı: {prompt_path}")
        return (
            "Kullanıcının uygulama fikrini analiz et. "
            "Sadece geçerli JSON döndür, açıklama yapma. "
            "JSON şu alanları içermeli: project_name, description, "
            "tech_stack (liste), architecture, files (her biri path, purpose, language içeren liste)."
        )

    @staticmethod
    def display_spec(spec: ProjectSpec) -> None:
        """ProjectSpec'i okunaklı formatta terminale yazdırır."""
        print()
        print("=" * 55)
        print(f"📋  PROJE PLANI: {spec.project_name}")
        print("=" * 55)
        print()
        print(f"📝  Açıklama   : {spec.description}")
        print(f"🛠️  Teknolojiler: {', '.join(spec.tech_stack)}")

        if spec.architecture:
            print(f"🏗️  Mimari      : {spec.architecture}")

        print()
        print(f"📂  Dosya Yapısı ({len(spec.files)} dosya):")
        print("-" * 55)
        for i, f in enumerate(spec.files, 1):
            print(f"   {i}. {f.path}")
            print(f"      └─ {f.purpose}")
        print("-" * 55)
        print()
