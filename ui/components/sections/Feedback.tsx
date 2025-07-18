'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Brain, Zap, Shield } from 'lucide-react';
import { FeatureCard } from '@/types';
// import { FeatureCard } from '../types/feedback';
import { Variants } from "framer-motion";

const features: FeatureCard[] = [
  { icon: Brain, title: "AI-Powered Analysis", desc: "Advanced sentiment analysis and categorization" },
  { icon: Zap, title: "Real-time Insights", desc: "Get instant feedback analysis as it comes in" },
  { icon: Shield, title: "Enterprise Security", desc: "Bank-grade security for your sensitive data" }
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  }
};

const itemVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 10
    }
  }
};

const floatingAnimation = {
  y: [-10, 10, -10],
  transition: {
    duration: 3,
    repeat: Infinity,
    ease: "easeInOut" as const
  }
};

export function FeaturesGrid() {
  return (
    <motion.div 
      className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {features.map((feature, index) => (
        <motion.div key={index} variants={itemVariants}>
          <Card className="bg-white/5 backdrop-blur-sm border-white/10 hover:bg-white/10 transition-all duration-300 group">
            <CardContent className="p-6 text-center">
              <motion.div 
                className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300"
                animate={floatingAnimation}
              >
                <feature.icon className="w-8 h-8 text-white" />
              </motion.div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-300">{feature.desc}</p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}