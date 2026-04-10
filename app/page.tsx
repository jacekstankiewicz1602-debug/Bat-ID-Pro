import { HeroGeometric } from "@/components/ui/shape-landing-hero";
import BatAnalyzer from "@/components/BatAnalyzer";

export default function Home() {
  return (
    <main className="bg-[#030303] min-h-screen">
      {/* Hero Section */}
      <HeroGeometric
        badge="Bat ID Pro v1.0"
        title1="Identyfikacja Nietoperzy"
        title2="Na Podstawie Głosu"
        description="Profesjonalny system analizy bioakustycznej wykorzystujący zaawansowane sieci neuronowe do automatycznej identyfikacji i klasyfikacji gatunków nietoperzy w czasie rzeczywistym."
      />

      {/* Functional Analyzer Section */}
      <div className="pb-24 px-8 relative z-10">
        <BatAnalyzer />
      </div>

      {/* Stopka informacyjna */}
      <footer className="py-12 border-t border-zinc-900 text-center">
        <p className="text-zinc-600 text-sm">
          Napędzane przez BattyBirdNET-Analyzer & TFLite
        </p>
      </footer>
    </main>
  );
}

