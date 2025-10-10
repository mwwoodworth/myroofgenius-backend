// GLASSMORPHISM_DASHBOARD_COMPLETE.tsx
// Complete Dashboard Implementation with Ultra High-Tech Design
// =============================================================

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  Activity, Users, DollarSign, TrendingUp, Package,
  Settings, Bell, Search, Menu, X, ChevronRight,
  Calendar, Clock, MapPin, FileText, Shield,
  Zap, Globe, Database, Cloud, Cpu, HardDrive,
  Wifi, Battery, AlertCircle, CheckCircle
} from 'lucide-react';

// ============================================
// MASTER DASHBOARD COMPONENT
// ============================================

export const GlassmorphismDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [aiCopilotOpen, setAiCopilotOpen] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [realTimeData, setRealTimeData] = useState({});
  const [notifications, setNotifications] = useState([]);

  // Fetch real-time data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/dashboard/metrics');
        const data = await response.json();
        setRealTimeData(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'wss://api.brainops.com/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metric_update') {
        setRealTimeData(prev => ({ ...prev, ...data.payload }));
      } else if (data.type === 'notification') {
        setNotifications(prev => [data.payload, ...prev].slice(0, 5));
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B0B12] via-[#1A1A2E] to-[#16162B]">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-blue-500/5" />
        <AnimatedStars />
      </div>

      {/* Main container */}
      <div className="relative z-10">
        {/* Header */}
        <GlassHeader 
          onMenuClick={() => {}}
          onSearchChange={() => {}}
          notifications={notifications}
        />

        {/* Sidebar */}
        <GlassSidebar 
          activeView={activeView}
          onViewChange={setActiveView}
        />

        {/* Main content */}
        <main className="ml-64 p-8">
          <AnimatePresence mode="wait">
            {activeView === 'overview' && (
              <OverviewDashboard key="overview" data={realTimeData} />
            )}
            {activeView === 'projects' && (
              <ProjectsDashboard key="projects" />
            )}
            {activeView === 'analytics' && (
              <AnalyticsDashboard key="analytics" data={realTimeData} />
            )}
            {activeView === 'settings' && (
              <SettingsDashboard key="settings" />
            )}
          </AnimatePresence>
        </main>

        {/* AI Copilot */}
        <AICopilotPanel 
          isOpen={aiCopilotOpen}
          onClose={() => setAiCopilotOpen(false)}
        />

        {/* Floating AI Button */}
        <motion.button
          className="fixed bottom-8 right-8 w-16 h-16 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 shadow-2xl flex items-center justify-center text-white"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setAiCopilotOpen(true)}
        >
          <Zap size={24} />
        </motion.button>
      </div>
    </div>
  );
};

// ============================================
// GLASS HEADER COMPONENT
// ============================================

const GlassHeader = ({ onMenuClick, onSearchChange, notifications }) => {
  const [searchFocused, setSearchFocused] = useState(false);

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-40 h-20"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-gray-900/80 to-black/80 backdrop-blur-xl" />
      <div className="relative h-full flex items-center justify-between px-8">
        {/* Logo and title */}
        <div className="flex items-center gap-4">
          <motion.div
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center"
            whileHover={{ rotate: 360 }}
            transition={{ duration: 0.5 }}
          >
            <Globe className="text-white" size={24} />
          </motion.div>
          <div>
            <h1 className="text-xl font-bold text-white">BrainOps AIOS</h1>
            <p className="text-xs text-gray-400">Master Command Center</p>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex-1 max-w-xl mx-8">
          <motion.div
            className={`relative rounded-xl overflow-hidden ${
              searchFocused ? 'ring-2 ring-cyan-400' : ''
            }`}
            animate={{ scale: searchFocused ? 1.02 : 1 }}
          >
            <input
              type="text"
              placeholder="Search anything..."
              className="w-full px-12 py-3 bg-white/10 backdrop-blur-md text-white placeholder-gray-400 outline-none"
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              onChange={onSearchChange}
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <kbd className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-1 rounded bg-white/10 text-xs text-gray-400">
              ⌘K
            </kbd>
          </motion.div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <motion.button
            className="relative p-3 rounded-xl bg-white/10 backdrop-blur-md text-white"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Bell size={20} />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-xs flex items-center justify-center">
                {notifications.length}
              </span>
            )}
          </motion.button>

          {/* User avatar */}
          <motion.div
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-400 to-pink-600 flex items-center justify-center text-white font-bold cursor-pointer"
            whileHover={{ scale: 1.05 }}
          >
            MW
          </motion.div>
        </div>
      </div>
    </motion.header>
  );
};

// ============================================
// GLASS SIDEBAR COMPONENT
// ============================================

const GlassSidebar = ({ activeView, onViewChange }) => {
  const menuItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'projects', label: 'Projects', icon: Package },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'finance', label: 'Finance', icon: DollarSign },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      className="fixed left-0 top-20 bottom-0 w-64 z-30"
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xl border-r border-white/10" />
      <nav className="relative p-4">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <motion.button
              key={item.id}
              className={`w-full mb-2 px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
              onClick={() => onViewChange(item.id)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ x: 5 }}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
              {isActive && (
                <motion.div
                  className="ml-auto"
                  initial={{ rotate: 0 }}
                  animate={{ rotate: 90 }}
                >
                  <ChevronRight size={16} />
                </motion.div>
              )}
            </motion.button>
          );
        })}
      </nav>
    </motion.aside>
  );
};

// ============================================
// OVERVIEW DASHBOARD
// ============================================

const OverviewDashboard = ({ data }) => {
  const metrics = [
    {
      title: 'Total Revenue',
      value: '$847,392',
      change: 12.5,
      trend: 'up',
      icon: DollarSign,
      color: 'from-green-400 to-emerald-600',
    },
    {
      title: 'Active Users',
      value: '12,847',
      change: 8.2,
      trend: 'up',
      icon: Users,
      color: 'from-blue-400 to-indigo-600',
    },
    {
      title: 'Projects',
      value: '384',
      change: -2.4,
      trend: 'down',
      icon: Package,
      color: 'from-purple-400 to-pink-600',
    },
    {
      title: 'System Health',
      value: '98.7%',
      change: 0.3,
      trend: 'up',
      icon: Activity,
      color: 'from-cyan-400 to-blue-600',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="pt-8"
    >
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} delay={index * 0.1} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <RevenueChart />
        <ActivityChart />
      </div>

      {/* Projects and Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ProjectsTable />
        </div>
        <div>
          <TasksList />
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// METRIC CARD COMPONENT
// ============================================

const MetricCard = ({ title, value, change, trend, icon: Icon, color, delay }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -5, scale: 1.02 }}
      className="relative overflow-hidden rounded-2xl"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl" />
      <div className="absolute inset-0 bg-gradient-to-br opacity-20" 
        style={{
          backgroundImage: `linear-gradient(135deg, ${color.split(' ')[1].slice(5)}, ${color.split(' ')[3].slice(3)})`
        }}
      />
      
      <div className="relative p-6">
        <div className="flex items-start justify-between mb-4">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center text-white`}>
            <Icon size={24} />
          </div>
          <div className={`text-sm font-medium ${
            trend === 'up' ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend === 'up' ? '↑' : '↓'} {Math.abs(change)}%
          </div>
        </div>
        
        <div>
          <p className="text-gray-400 text-sm mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// REVENUE CHART COMPONENT
// ============================================

const RevenueChart = () => {
  const data = [
    { month: 'Jan', revenue: 65000, profit: 45000 },
    { month: 'Feb', revenue: 72000, profit: 52000 },
    { month: 'Mar', revenue: 78000, profit: 58000 },
    { month: 'Apr', revenue: 85000, profit: 62000 },
    { month: 'May', revenue: 92000, profit: 68000 },
    { month: 'Jun', revenue: 98000, profit: 75000 },
  ];

  return (
    <motion.div
      className="relative rounded-2xl overflow-hidden"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.2 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl" />
      <div className="relative p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Revenue Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#00D4FF" stopOpacity={0.1}/>
              </linearGradient>
              <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9945FF" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#9945FF" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="month" stroke="rgba(255,255,255,0.5)" />
            <YAxis stroke="rgba(255,255,255,0.5)" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.8)',
                border: '1px solid rgba(0,212,255,0.3)',
                borderRadius: '8px',
              }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#00D4FF"
              fillOpacity={1}
              fill="url(#revenueGradient)"
            />
            <Area
              type="monotone"
              dataKey="profit"
              stroke="#9945FF"
              fillOpacity={1}
              fill="url(#profitGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

// ============================================
// ACTIVITY CHART COMPONENT
// ============================================

const ActivityChart = () => {
  const data = [
    { day: 'Mon', users: 4200, sessions: 8400 },
    { day: 'Tue', users: 4800, sessions: 9200 },
    { day: 'Wed', users: 5200, sessions: 10100 },
    { day: 'Thu', users: 4900, sessions: 9800 },
    { day: 'Fri', users: 5500, sessions: 11200 },
    { day: 'Sat', users: 3200, sessions: 6400 },
    { day: 'Sun', users: 2800, sessions: 5600 },
  ];

  return (
    <motion.div
      className="relative rounded-2xl overflow-hidden"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl" />
      <div className="relative p-6">
        <h3 className="text-lg font-semibold text-white mb-4">User Activity</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="day" stroke="rgba(255,255,255,0.5)" />
            <YAxis stroke="rgba(255,255,255,0.5)" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.8)',
                border: '1px solid rgba(153,69,255,0.3)',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="users" fill="#00D4FF" radius={[8, 8, 0, 0]} />
            <Bar dataKey="sessions" fill="#9945FF" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

// ============================================
// PROJECTS TABLE COMPONENT
// ============================================

const ProjectsTable = () => {
  const projects = [
    { id: 1, name: 'E-Commerce Platform', status: 'active', progress: 75, team: 8, deadline: '2024-03-15' },
    { id: 2, name: 'Mobile App Redesign', status: 'active', progress: 60, team: 5, deadline: '2024-03-20' },
    { id: 3, name: 'Data Analytics Dashboard', status: 'pending', progress: 30, team: 6, deadline: '2024-04-01' },
    { id: 4, name: 'API Integration', status: 'completed', progress: 100, team: 4, deadline: '2024-02-28' },
    { id: 5, name: 'Security Audit', status: 'active', progress: 45, team: 3, deadline: '2024-03-10' },
  ];

  const statusColors = {
    active: 'text-green-400',
    pending: 'text-yellow-400',
    completed: 'text-blue-400',
  };

  return (
    <motion.div
      className="relative rounded-2xl overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl" />
      <div className="relative p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Projects</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm">
                <th className="pb-4">Project</th>
                <th className="pb-4">Status</th>
                <th className="pb-4">Progress</th>
                <th className="pb-4">Team</th>
                <th className="pb-4">Deadline</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project, index) => (
                <motion.tr
                  key={project.id}
                  className="border-t border-white/5"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.05 }}
                >
                  <td className="py-4">
                    <p className="text-white font-medium">{project.name}</p>
                  </td>
                  <td className="py-4">
                    <span className={`text-sm ${statusColors[project.status]}`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-cyan-400 to-purple-600"
                          initial={{ width: 0 }}
                          animate={{ width: `${project.progress}%` }}
                          transition={{ delay: 0.6 + index * 0.05, duration: 0.5 }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{project.progress}%</span>
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex -space-x-2">
                      {[...Array(Math.min(project.team, 3))].map((_, i) => (
                        <div
                          key={i}
                          className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-600 border-2 border-gray-900 flex items-center justify-center text-xs text-white"
                        >
                          {i + 1}
                        </div>
                      ))}
                      {project.team > 3 && (
                        <div className="w-8 h-8 rounded-full bg-gray-700 border-2 border-gray-900 flex items-center justify-center text-xs text-white">
                          +{project.team - 3}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-4">
                    <p className="text-sm text-gray-400">{project.deadline}</p>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// TASKS LIST COMPONENT
// ============================================

const TasksList = () => {
  const tasks = [
    { id: 1, title: 'Review pull requests', priority: 'high', time: '2 hours ago' },
    { id: 2, title: 'Update documentation', priority: 'medium', time: '4 hours ago' },
    { id: 3, title: 'Fix critical bug', priority: 'urgent', time: '5 hours ago' },
    { id: 4, title: 'Deploy to production', priority: 'high', time: '1 day ago' },
    { id: 5, title: 'Team meeting', priority: 'low', time: '2 days ago' },
  ];

  const priorityColors = {
    urgent: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-green-500',
  };

  return (
    <motion.div
      className="relative rounded-2xl overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl" />
      <div className="relative p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Tasks</h3>
        <div className="space-y-3">
          {tasks.map((task, index) => (
            <motion.div
              key={task.id}
              className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 cursor-pointer transition-all"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + index * 0.05 }}
              whileHover={{ x: 5 }}
            >
              <div className={`w-2 h-2 rounded-full ${priorityColors[task.priority]}`} />
              <div className="flex-1">
                <p className="text-white text-sm">{task.title}</p>
                <p className="text-gray-400 text-xs">{task.time}</p>
              </div>
              <ChevronRight className="text-gray-400" size={16} />
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// ANIMATED STARS BACKGROUND
// ============================================

const AnimatedStars = () => {
  return (
    <div className="absolute inset-0">
      {[...Array(50)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-white rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            opacity: [0, 1, 0],
            scale: [0, 1, 0],
          }}
          transition={{
            duration: Math.random() * 3 + 2,
            repeat: Infinity,
            delay: Math.random() * 5,
          }}
        />
      ))}
    </div>
  );
};

// ============================================
// AI COPILOT PANEL
// ============================================

const AICopilotPanel = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('AI chat error:', error);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 20 }}
          className="fixed right-0 top-0 h-full w-96 z-50"
        >
          <div className="absolute inset-0 bg-black/80 backdrop-blur-xl border-l border-white/10" />
          <div className="relative h-full flex flex-col p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center">
                  <Zap className="text-white" size={20} />
                </div>
                <div>
                  <h3 className="text-white font-semibold">AI Copilot</h3>
                  <p className="text-xs text-gray-400">Always here to help</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white'
                        : 'bg-white/10 text-white'
                    }`}
                  >
                    {message.content}
                  </div>
                </motion.div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white/10 p-3 rounded-xl">
                    <div className="flex gap-1">
                      <motion.div
                        className="w-2 h-2 bg-white rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity }}
                      />
                      <motion.div
                        className="w-2 h-2 bg-white rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: 0.1 }}
                      />
                      <motion.div
                        className="w-2 h-2 bg-white rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: 0.2 }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask me anything..."
                className="flex-1 px-4 py-3 rounded-xl bg-white/10 text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-cyan-400"
              />
              <motion.button
                onClick={sendMessage}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Send
              </motion.button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Export default dashboard
export default GlassmorphismDashboard;