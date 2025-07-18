
  export type ProcessedFeedback = {
    id: string;
    text: string;
    user_type: string;
    source: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    timestamp?: string;
    intent?: string;
    theme?: string;
    urgency?: 'low' | 'medium' | 'high';
  };
  

  export type AnalyticsData = {
    totalFeedback: number;
    sentiment: {
      positive: number;
      negative: number;
      neutral: number;
    };
    categories: {
      name: string;
      count: number;
      trend: string;
    }[];
    recentFeedback: Omit<Feedback, 'user_type'>[];
  };
  
  export type StatCard = {
    title: string;
    value: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
  };
  
  export type FeatureCard = {
    icon: React.ComponentType<{ className?: string }>;
    title: string;
    desc: string;
  };
  
  export type PricingPlan = {
    name: string;
    price: string;
    features: string[];
    popular?: boolean;
  };

  export interface Feedback {
    id: string;
    text: string;
    user_type: string;
    source: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    intent?: string;
    theme?: string;
    urgency?: 'high' | 'medium' | 'low';
    timestamp: string;
  }
  
  export interface AnalysisResult {
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence?: number;
    categories?: string[];
    keywords?: string[];
    priority: 'high' | 'medium' | 'low';
    intent?: string;
    theme?: string;
    urgency?: 'high' | 'medium' | 'low';
    recommendations?: string[];
  }
  
  export interface AnalyticsCard {
    title: string;
    value: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
    icon: string;
  }
  
  export const mockAnalyticsCardsData: AnalyticsCard[] = [
    {
      title: 'Total Feedback',
      value: '2,847',
      change: '+12.5%',
      trend: 'up',
      icon: 'MessageSquare'
    },
    {
      title: 'Positive Sentiment',
      value: '78.3%',
      change: '+5.2%',
      trend: 'up',
      icon: 'TrendingUp'
    },
    {
      title: 'Avg Response Time',
      value: '2.4h',
      change: '-15.3%',
      trend: 'down',
      icon: 'Clock'
    },
    {
      title: 'Resolution Rate',
      value: '94.7%',
      change: '+2.1%',
      trend: 'up',
      icon: 'CheckCircle'
    }
  ];


// Alternative simplified version if you only need the card stats
export const mockCardStats = {
  totalFeedback: '2,843',
  positiveSentiment: '72%',
  activeUsers: '14.2K',
  responseTime: '1.8h'
};

export interface AnalyticsCard {
    title: string;
    value: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
    icon: string;
}