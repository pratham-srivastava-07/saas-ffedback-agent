'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  MessageSquare, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import { AnalyticsCard } from '@/types';

const iconMap = {
  MessageSquare,
  TrendingUp,
  Clock,
  CheckCircle
};

const trendIcons = {
  up: ArrowUp,
  down: ArrowDown,
  stable: Minus
};

const trendColors = {
  up: 'text-emerald-500',
  down: 'text-red-500',
  stable: 'text-slate-500'
};

export function AnalyticsCards({ analytics }: { analytics: AnalyticsCard[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
      {analytics.map((card, index) => {
        const Icon = iconMap[card.icon as keyof typeof iconMap];
        const TrendIcon = trendIcons[card.trend];
        
        return (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -2, transition: { duration: 0.2 } }}
          >
            <Card className="relative overflow-hidden bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg transition-shadow duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-slate-700/20" />
              <CardContent className="p-6 relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-400/10 dark:to-pink-400/10">
                    <Icon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <Badge 
                    variant="secondary" 
                    className={`${trendColors[card.trend]} bg-slate-100/80 dark:bg-slate-700/80 flex items-center gap-1`}
                  >
                    <TrendIcon className="w-3 h-3" />
                    {card.change}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    {card.title}
                  </h3>
                  <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {card.value}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}