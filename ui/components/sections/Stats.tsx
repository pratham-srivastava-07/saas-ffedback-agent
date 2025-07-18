'use client';

import { motion } from 'framer-motion';
import { Variants } from "framer-motion";

const stats = [
  { value: "99.9%", label: "Accuracy" },
  { value: "10M+", label: "Analyzed" },
  { value: "500+", label: "Companies" },
  { value: "50ms", label: "Response Time" }
];

const containerVariants = {
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

export function StatsSection() {
  return (
    <motion.div 
      className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center mb-20"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {stats.map((stat, index) => (
        <motion.div key={index} variants={itemVariants}>
          <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            {stat.value}
          </div>
          <div className="text-gray-300">{stat.label}</div>
        </motion.div>
      ))}
    </motion.div>
  );
}