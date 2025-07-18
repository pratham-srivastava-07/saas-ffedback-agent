'use client';

import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react';
import Link from 'next/link';

export function LandingHeader() {
  return (
    <motion.nav 
      className="relative z-10 p-6 flex justify-between items-center"
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
          <Sparkles className="w-5 h-5" />
        </div>
        <span className="text-xl font-bold">Sentilytics</span>
      </div>
      <Link href="/dashboard">
        <Button 
          variant="outline" 
          className="bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/20"
        >
          Launch Dashboard
        </Button>
      </Link>
    </motion.nav>
  );
}