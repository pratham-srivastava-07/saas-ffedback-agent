'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Menu, X, BarChart3, MessageSquare, Settings, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AnalyticsCards } from '@/components/sections/Analytics';
import { FeedbackForm } from '@/components/sections/FeedbackForm';
import { FeedbackAnalysis } from '@/components/sections/FeedbackAnalysis';
import { Feedback, AnalysisResult, mockAnalyticsCardsData } from '@/types';
import { ThemeToggle } from "@/components/ui/theme-toggle"

export default function Dashboard() {
  const [feedbackList, setFeedbackList] = useState<Feedback[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNewFeedback = async (feedback: Feedback) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raw_feedback: [{
            id: feedback.id,
            text: feedback.text,
            user_type: feedback.user_type,
            source: feedback.source
          }]
        })
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const { processed_feedback, recommendations } = await response.json();
      const processed = processed_feedback[0];

      setFeedbackList(prev => [{
        ...feedback,
        sentiment: processed.sentiment,
        intent: processed.intent,
        theme: processed.theme,
        urgency: processed.urgency
      }, ...prev]);

      setResult({
        sentiment: processed.sentiment,
        confidence: 0.9,
        categories: processed.theme ? [processed.theme] : ['General'],
        keywords: processed.text.toLowerCase().split(/\s+/).slice(0, 3),
        priority: processed.urgency || 'medium',
        intent: processed.intent,
        theme: processed.theme,
        urgency: processed.urgency,
        recommendations: recommendations
      });

    } catch (err) {
      console.error('Error analyzing feedback:', err);
      setError('Failed to analyze feedback. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <motion.header 
        className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50 shadow-sm"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <motion.div 
              className="flex items-center"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    Sentilytics
                  </h1>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Smart Analysis Platform
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <ThemeToggle />
            </nav>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-slate-200/50 dark:border-slate-700/50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md"
          >
            <div className="px-4 py-4 space-y-2">
              <Button variant="ghost" className="w-full justify-start">
                <BarChart3 className="w-4 h-4 mr-2" />
                Analytics
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                <MessageSquare className="w-4 h-4 mr-2" />
                Feedback
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </motion.div>
        )}
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 text-red-700 dark:text-red-300 rounded-lg shadow-sm"
          >
            <div className="flex items-center">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-3"></div>
              {error}
            </div>
          </motion.div>
        )}

        {/* Loading Overlay */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 dark:bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white dark:bg-slate-800 p-8 rounded-2xl shadow-2xl"
            >
              <div className="flex items-center space-x-4">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                    Analyzing Feedback
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    AI is processing your request...
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* Analytics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <AnalyticsCards analytics={mockAnalyticsCardsData} />
        </motion.div>
        
        {/* Main Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="order-2 xl:order-1"
          >
            <FeedbackForm 
              onFeedbackSubmit={handleNewFeedback}
              isLoading={isLoading}
            />
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="order-1 xl:order-2"
          >
            <FeedbackAnalysis result={result} />
          </motion.div>
        </div>

        {/* Spacer */}
        <div className="h-12"></div>
      </main>
    </div>
  );
}