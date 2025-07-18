'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Brain, MessageSquare, Sparkles, User, MapPin } from 'lucide-react';
import { Feedback } from '@/types';

export function FeedbackForm({ 
  onFeedbackSubmit,
  isLoading
}: {
  onFeedbackSubmit: (feedback: Feedback) => Promise<void>;
  isLoading: boolean;
}) {
  const [text, setText] = useState('');
  const [source, setSource] = useState('review');
  const [userType, setUserType] = useState('free');

  const handleSubmit = async () => {
    if (!text.trim()) return;
    
    const newFeedback: Feedback = {
      id: Date.now().toString(),
      text: text.trim(),
      user_type: userType,
      source,
      sentiment: 'neutral',
      timestamp: new Date().toISOString()
    };

    await onFeedbackSubmit(newFeedback);
    setText('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Card className="relative overflow-hidden bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 shadow-xl">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-pink-500/5 dark:from-purple-400/5 dark:to-pink-400/5" />
        
        <CardHeader className="relative">
          <CardTitle className="flex items-center text-xl font-semibold">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-400/10 dark:to-pink-400/10 mr-3">
              <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            Submit Feedback
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="ml-2"
            >
              <Sparkles className="w-4 h-4 text-purple-500 dark:text-purple-400" />
            </motion.div>
          </CardTitle>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Enter customer feedback for AI-powered analysis and insights
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6 relative">
          <div className="space-y-2">
            <Label htmlFor="feedback-text" className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Feedback Text
            </Label>
            <Textarea
              id="feedback-text"
              placeholder="Share your thoughts, suggestions, or concerns..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[120px] resize-none bg-white/70 dark:bg-slate-700/70 border-slate-200/50 dark:border-slate-600/50 focus:border-purple-500/50 dark:focus:border-purple-400/50 focus:ring-purple-500/20 dark:focus:ring-purple-400/20 transition-all duration-200"
            />
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Be specific and detailed for better analysis</span>
              <span>{text.length} characters</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center">
                <User className="w-4 h-4 mr-2" />
                User Type
              </Label>
              <Select value={userType} onValueChange={setUserType}>
                <SelectTrigger className="bg-white/70 dark:bg-slate-700/70 border-slate-200/50 dark:border-slate-600/50 focus:border-purple-500/50 dark:focus:border-purple-400/50 focus:ring-purple-500/20 dark:focus:ring-purple-400/20">
                  <SelectValue placeholder="Select user type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="free">Free User</SelectItem>
                  <SelectItem value="paid">Paid User</SelectItem>
                  <SelectItem value="premium">Premium User</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center">
                <MapPin className="w-4 h-4 mr-2" />
                Source
              </Label>
              <Select value={source} onValueChange={setSource}>
                <SelectTrigger className="bg-white/70 dark:bg-slate-700/70 border-slate-200/50 dark:border-slate-600/50 focus:border-purple-500/50 dark:focus:border-purple-400/50 focus:ring-purple-500/20 dark:focus:ring-purple-400/20">
                  <SelectValue placeholder="Select source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="review">Review</SelectItem>
                  <SelectItem value="support">Support</SelectItem>
                  <SelectItem value="nps">NPS Survey</SelectItem>
                  <SelectItem value="social">Social Media</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button 
              onClick={handleSubmit} 
              disabled={isLoading || !text.trim()}
              className="w-full h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                  <span>Analyzing with AI...</span>
                </div>
              ) : (
                <>
                  <Brain className="w-5 h-5 mr-3" />
                  <span>Analyze Feedback</span>
                </>
              )}
            </Button>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
}