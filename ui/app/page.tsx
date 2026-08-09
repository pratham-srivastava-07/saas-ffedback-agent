import { LandingNav } from "@/components/landing/nav";
import { Hero } from "@/components/landing/hero";
import { Problem } from "@/components/landing/problem";
import { Pipeline } from "@/components/landing/pipeline";
import { Evidence } from "@/components/landing/evidence";
import { Limits } from "@/components/landing/limits";
import { Pricing } from "@/components/landing/pricing";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="min-h-dvh bg-background">
      <LandingNav />
      <main>
        <Hero />
        <Problem />
        <Pipeline />
        <Evidence />
        <Limits />
        <Pricing />
      </main>
      <Footer />
    </div>
  );
}
