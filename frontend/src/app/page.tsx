import type { Metadata } from "next";
import { HeroSection } from "@/components/landing/hero-section";
import { LandingNavbar } from "@/components/landing/navbar";
import { SocialProofSection } from "@/components/landing/social-proof";
import { FeaturesSection } from "@/components/landing/features";
import { ArchitectureSection } from "@/components/landing/architecture";
import { ProductPreviewSection } from "@/components/landing/product-preview";
import { CtaSection } from "@/components/landing/cta-section";
import { LandingFooter } from "@/components/landing/footer";

export const metadata: Metadata = {
  title: "ASEP | Autonomous Software Engineering Platform",
  description: "Deploy, govern, and monitor autonomous developer agent collectives locally inside secure sandboxes.",
  openGraph: {
    title: "ASEP - Autonomous Software Engineering Platform",
    description: "Deploy, govern, and monitor autonomous developer agent collectives locally inside secure sandboxes.",
    type: "website",
  },
};

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      <LandingNavbar />
      <HeroSection />
      <SocialProofSection />
      <FeaturesSection />
      <ArchitectureSection />
      <ProductPreviewSection />
      <CtaSection />
      <LandingFooter />
    </main>
  );
}
