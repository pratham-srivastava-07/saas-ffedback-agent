'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  BarChart3, 
  Brain, 
  Lightbulb, 
  AlertTriangle, 
  Gauge, 
  Target,
  Heart,
  Frown,
  Meh,
  Sparkles
} from 'lucide-react';
import { AnalysisResult } from '@/types';

const urgencyMap = {
  high: { 
    color: 'bg-gradient-to-r from-red-500 to-red-600', 
    icon: AlertTriangle,
    text: 'text-red-100'
  },
  medium: { 
    color: 'bg-gradient-to-r from-yellow-500 to-yellow-600', 
    icon: Gauge,
    text: 'text-yellow-100'
  },
  low: { 
    color: 'bg-gradient-to-r from-green-500 to-green-600', 
    icon: Target,
    text: 'text-green-100'
  }
};

const sentimentMap = {
  positive: { 
    color: 'bg-gradient-to-r from-green-500 to-emerald-600', 
    icon: Heart,
    text: 'text-green-100'
  },
  negative: { 
    color: 'bg-gradient-to-r from-red-500 to-rose-600', 
    icon: Frown,
    text: 'text-red-100'
  },
  neutral: { 
    color: 'bg-gradient-to-r from-blue-500 to-blue-600', 
    icon: Meh,
    text: 'text-blue-100'
  }
};

export function FeedbackAnalysis({ result }: { result: AnalysisResult | null }) {
  const UrgencyIcon = result?.urgency ? urgencyMap[result.urgency].icon : null;
  const SentimentIcon = result?.sentiment ? sentimentMap[result.sentiment].icon : null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Card className="relative overflow-hidden bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 shadow-xl">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 dark:from-blue-400/5 dark:to-purple-400/5" />
        
        <CardHeader className="relative">
          <CardTitle className="flex items-center text-xl font-semibold">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 dark:from-blue-400/10 dark:to-purple-400/10 mr-3">
              <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            Analysis Results
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="ml-2"
            >
              <Sparkles className="w-4 h-4 text-blue-500 dark:text-blue-400" />
            </motion.div>
          </CardTitle>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            AI-powered insights and recommendations
          </p>
        </CardHeader>
        
        <CardContent className="relative">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
                className="space-y-6"
              >
                {/* Primary Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Sentiment */}
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="space-y-2"
                  >
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Sentiment</span>
                    <Badge className={`${sentimentMap[result.sentiment].color} ${sentimentMap[result.sentiment].text} border-0 px-3 py-1 font-medium flex items-center gap-2 w-fit`}>
                      {SentimentIcon && <SentimentIcon className="w-3 h-3" />}
                      {result.sentiment}
                    </Badge>
                  </motion.div>

                  {/* Urgency */}
                  {result.urgency && (
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.2 }}
                      className="space-y-2"
                    >
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Urgency</span>
                      <Badge className={`${urgencyMap[result.urgency].color} ${urgencyMap[result.urgency].text} border-0 px-3 py-1 font-medium flex items-center gap-2 w-fit`}>
                        {UrgencyIcon && <UrgencyIcon className="w-3 h-3" />}
                        {result.urgency}
                      </Badge>
                    </motion.div>
                  )}
                </div>

                {/* Confidence */}
                {result.confidence && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="space-y-3"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Confidence Score</span>
                      <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {(result.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress 
                      value={result.confidence * 100} 
                      className="h-2 bg-slate-200/50 dark:bg-slate-700/50"
                    />
                  </motion.div>
                )}

                <Separator className="bg-slate-200/50 dark:bg-slate-700/50" />

                {/* Secondary Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Intent */}
                  {result.intent && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 }}
                      className="space-y-2"
                    >
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Intent</span>
                      <Badge variant="outline" className="capitalize bg-white/50 dark:bg-slate-700/50 border-slate-300/50 dark:border-slate-600/50">
                        {result.intent}
                      </Badge>
                    </motion.div>
                  )}

                  {/* Theme */}
                  {result.theme && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 }}
                      className="space-y-2"
                    >
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Theme</span>
                      <Badge variant="secondary" className="capitalize bg-slate-100/80 dark:bg-slate-700/80">
                        {result.theme}
                      </Badge>
                    </motion.div>
                  )}
                </div>

                {/* Categories */}
                {Array.isArray(result.categories) && result.categories.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="space-y-3"
                  >
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Categories</span>
                    <div className="flex flex-wrap gap-2">
                      {result.categories?.map((category, i) => (
                        <motion.div
                          key={i}
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: 0.7 + i * 0.1 }}
                        >
                          <Badge variant="secondary" className="capitalize bg-purple-100/80 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                            {category}
                          </Badge>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Keywords */}
                {Array.isArray(result.keywords) && result.keywords.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    className="space-y-3"
                  >
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Key Terms</span>
                    <div className="flex flex-wrap gap-2">
                      {result.keywords?.map((keyword, i) => (
                        <motion.div
                          key={i}
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: 0.9 + i * 0.1 }}
                        >
                          <Badge variant="outline" className="lowercase bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-200/50 dark:border-blue-700/50">
                            {keyword}
                          </Badge>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}

                <Separator className="bg-slate-200/50 dark:bg-slate-700/50" />

                {/* Priority */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.0 }}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Priority Level</span>
                  <Badge className={`${
                    result.priority === 'high' ? 'bg-gradient-to-r from-red-500 to-red-600 text-red-100' : 
                    result.priority === 'medium' ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-yellow-100' : 
                    'bg-gradient-to-r from-green-500 to-green-600 text-green-100'
                  } border-0 px-3 py-1 font-medium`}>
                    {result.priority}
                  </Badge>
                </motion.div>
                
                {/* Recommendations */}
                {result.recommendations && result.recommendations.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.1 }}
                    className="pt-4 border-t border-slate-200/50 dark:border-slate-700/50"
                  >
                    <div className="flex items-center text-sm font-medium mb-4 text-slate-700 dark:text-slate-300">
                      <div className="p-2 rounded-lg bg-gradient-to-br from-yellow-500/10 to-orange-500/10 dark:from-yellow-400/10 dark:to-orange-400/10 mr-3">
                        <Lightbulb className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                      </div>
                      AI Recommendations
                    </div>
                    <div className="space-y-3">
                      {result.recommendations
                        .filter(rec => rec.trim().length > 0)
                        .map((rec, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 1.2 + i * 0.1 }}
                            className="flex items-start p-3 rounded-lg bg-gradient-to-r from-slate-50/80 to-slate-100/80 dark:from-slate-700/50 dark:to-slate-800/50 border border-slate-200/50 dark:border-slate-600/50"
                          >
                            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                              {rec.startsWith('**') ? (
                                <span className="font-semibold text-purple-600 dark:text-purple-400">
                                  {rec.replace(/\*\*/g, '')}
                                </span>
                              ) : rec.match(/^\d+\./) ? (
                                <>
                                  <span className="font-medium text-slate-900 dark:text-slate-100">
                                    {rec.split(' ')[0]}
                                  </span>
                                  <span className="ml-1">{rec.split(' ').slice(1).join(' ')}</span>
                                </>
                              ) : (
                                rec
                              )}
                            </span>
                          </motion.div>
                        ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-12"
              >
                <div className="relative">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                    className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-400/10 dark:to-pink-400/10 flex items-center justify-center"
                  >
                    <Brain className="w-8 h-8 text-purple-500 dark:text-purple-400" />
                  </motion.div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      className="w-2 h-2 bg-purple-500 dark:bg-purple-400 rounded-full"
                    />
                  </div>
                </div>
                <p className="text-slate-500 dark:text-slate-400 font-medium">
                  Submit feedback to see AI analysis
                </p>
                <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
                  Get insights on sentiment, urgency, and recommendations
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}