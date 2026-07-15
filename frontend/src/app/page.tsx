import { HeroSection } from "@/components/landing/hero-section"
import { LandingNavbar } from "@/components/landing/navbar"

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      <LandingNavbar />
      <HeroSection />
    </main>
  )
}
