import { HeroSection } from "@/components/landing/hero-section"
import { LandingNavbar } from "@/components/landing/navbar"
import { SocialProofSection } from "@/components/landing/social-proof"

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      <LandingNavbar />
      <HeroSection />
      <SocialProofSection />
    </main>
  )
}
