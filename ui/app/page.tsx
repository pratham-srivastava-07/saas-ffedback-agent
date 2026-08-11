import { LandingNav } from "@/components/landing/nav";
import { Hero } from "@/components/landing/hero";
import { ProductPreview } from "@/components/landing/product-preview";
import { Problem } from "@/components/landing/problem";
import { Pipeline } from "@/components/landing/pipeline";
import { Evidence } from "@/components/landing/evidence";
import { Limits } from "@/components/landing/limits";
import { Pricing } from "@/components/landing/pricing";
import { FinalCta } from "@/components/landing/final-cta";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="min-h-dvh bg-background">
      <LandingNav />
      <main>
        <Hero />
        {/* Product before explanation: the interface appears before anything
            is claimed about it. */}
        <ProductPreview />
        <Problem />
        <Pipeline />
        <Evidence />
        <Limits />
        <Pricing />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}
