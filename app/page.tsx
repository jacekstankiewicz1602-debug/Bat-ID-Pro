import { HeroGeometric } from "@/components/ui/shape-landing-hero";
import { Button } from "@/components/ui/neon-button";

export default function Home() {
  return (
    <main>
      {/* Sekcja Hero */}
      <HeroGeometric
        badge="Kokonut UI"
        title1="Elevate Your"
        title2="Digital Vision"
      />

      {/* Sekcja z przyciskami - ciemny motyw */}
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 bg-[#030303] text-white p-8">
        <h2 className="text-4xl font-bold">Przegląd Komponentów</h2>
        <div className="flex flex-col gap-3">
          <Button>Domyślny Przycisk</Button>
          <Button neon={false}>Zwykły Przycisk</Button>
          <Button variant={"solid"}>Solidny Przycisk</Button>
          <Button size="lg">Duży Przycisk</Button>
        </div>
      </div>
    </main>
  );
}
