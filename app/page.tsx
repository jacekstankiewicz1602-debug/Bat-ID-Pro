import { HeroGeometric } from "@/components/ui/shape-landing-hero";
import BatAnalyzer from "@/components/BatAnalyzer";

export default function Home() {
  return (
    <main className="bg-[#030303] min-h-screen">
      {/* Hero Section */}
      <HeroGeometric
        badge="Bat ID Pro v1.0"
        title1="Identify Bats"
        title2="By Their Voice"
      />

      {/* Functional Analyzer Section */}
      <div className="pb-24 px-8 relative z-10">
        <BatAnalyzer />
      </div>

      {/* Footer info */}
      <footer className="py-12 border-t border-zinc-900 text-center">
        <p className="text-zinc-600 text-sm">
          Powered by BattyBirdNET-Analyzer & TFLite
        </p>
      </footer>
    </main>
  );
}

