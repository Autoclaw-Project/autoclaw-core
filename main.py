"""
Autoclaw - AI-Powered App Builder
Kullanıcının uygulama fikrini alır, analiz eder ve teknik plan üretir.
"""

import sys
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

from core.llm_client import LLMClient
from agents.planner_agent import PlannerAgent


def main():
    print("=" * 55)
    print("🚀  AUTOCLAW — AI Uygulama Oluşturucu")
    print("=" * 55)
    print()
    print("Merhaba! Ben Autoclaw, senin uygulama fikrini")
    print("analiz edip teknik bir plan oluşturuyorum.")
    print()

    # Kullanıcıdan uygulama fikrini al
    app_idea = input("💡 Uygulama fikrin nedir? → ").strip()

    if not app_idea:
        print("\n⚠️  Bir fikir girmelisin! Tekrar dene.")
        return

    print()

    try:
        # LLM Client ve PlannerAgent'ı başlat
        llm = LLMClient()
        planner = PlannerAgent(llm)

        # Fikri analiz et → ProjectSpec üret
        spec = planner.analyze(app_idea)

        # Sonucu terminale yazdır
        PlannerAgent.display_spec(spec)

        print("🔧  Autoclaw bu plan üzerinde çalışmaya hazır!")
        print("    Bir sonraki adımda BuilderAgent kodları üretecek.")
        print()

    except ValueError as e:
        print(f"\n❌ Veri hatası: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ API hatası: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
