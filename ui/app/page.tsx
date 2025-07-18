import { LandingHeader } from '@/components/layout/LandingNavbar';
import { FeaturesGrid } from '@/components/sections/Feedback';
import { HeroSection } from '@/components/sections/Hero';
import { PricingSection } from '@/components/sections/Pricing';
import { StatsSection } from '@/components/sections/Stats';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white relative overflow-hidden">
      {/* Animated Background - Responsive */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Mobile background elements */}
        <div className="absolute top-1/4 left-1/4 w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64 lg:w-72 lg:h-72 rounded-full bg-gradient-to-r from-blue-500/10 to-cyan-500/10 blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-52 h-52 sm:w-60 sm:h-60 md:w-72 md:h-72 lg:w-80 lg:h-80 rounded-full bg-gradient-to-r from-green-500/10 to-emerald-500/10 blur-3xl animate-pulse" />
        
        {/* Additional background elements for larger screens */}
        <div className="hidden lg:block absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-gradient-to-r from-purple-500/5 to-pink-500/5 blur-3xl animate-pulse" />
      </div>

      <LandingHeader />
      <HeroSection />
      <FeaturesGrid />
      <StatsSection />
      <PricingSection />
    </div>
  );
}