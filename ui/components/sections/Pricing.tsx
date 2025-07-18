'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';
// import { PricingPlan } from '../types/feedback';
import Link from 'next/link';
import { PricingPlan } from '@/types';

const plans: PricingPlan[] = [
  { name: "Starter", price: "$49", features: ["1K feedback/month", "Basic analytics", "Email support"] },
  { name: "Pro", price: "$149", features: ["10K feedback/month", "Advanced AI", "Priority support", "Custom integrations"], popular: true },
  { name: "Enterprise", price: "Custom", features: ["Unlimited feedback", "White-label", "Dedicated support", "Custom AI models"] }
];

export function PricingSection() {
  return (
    <motion.div 
      className="relative z-10 max-w-6xl mx-auto px-6 pb-20"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.5 }}
    >
      <div className="text-center mb-16">
        <h2 className="text-4xl font-bold mb-4">Choose Your Plan</h2>
        <p className="text-xl text-gray-300">Scale with your business needs</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {plans.map((plan, index) => (
          <motion.div 
            key={index}
            whileHover={{ scale: 1.05 }}
            className={`relative ${plan.popular ? 'z-10' : ''}`}
          >
            <Card className={`${plan.popular ? 'bg-gradient-to-b from-purple-500/20 to-pink-500/20 border-purple-500/50' : 'bg-white/5 border-white/10'} backdrop-blur-sm`}>
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                    Most Popular
                  </Badge>
                </div>
              )}
              <CardContent className="p-6 text-center">
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <div className="text-4xl font-bold mb-4">{plan.price}</div>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center justify-center">
                      <Check className="w-5 h-5 text-green-400 mr-2" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href="/feedback-flow/dashboard">
                  <Button 
                    className={`w-full ${plan.popular ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600' : 'bg-white/10 hover:bg-white/20'}`}
                  >
                    Get Started
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}