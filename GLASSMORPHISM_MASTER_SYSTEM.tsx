// GLASSMORPHISM_MASTER_SYSTEM.tsx
// Ultra High-Tech Design System with AI-Native Components
// =========================================================

import { motion, AnimatePresence, MotionConfig } from 'framer-motion';
import { ReactNode, useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

// ============================================
// CORE DESIGN TOKENS & THEME
// ============================================

export const glassTheme = {
  colors: {
    // Deep blacks and charcoals
    background: {
      primary: '#0B0B12',
      secondary: '#1A1A2E',
      tertiary: '#16162B',
      overlay: 'rgba(11, 11, 18, 0.95)',
    },
    // Electric blues and cyans
    accent: {
      primary: '#00D4FF',
      secondary: '#0099CC',
      tertiary: '#00FFFF',
      glow: 'rgba(0, 212, 255, 0.4)',
    },
    // Holographic purples
    purple: {
      primary: '#9945FF',
      secondary: '#7B3FF2',
      tertiary: '#B794F6',
      glow: 'rgba(153, 69, 255, 0.3)',
    },
    // Silver and whites
    text: {
      primary: '#FFFFFF',
      secondary: '#E0E0E0',
      tertiary: '#A0A0A0',
      muted: '#707070',
    },
    // Status colors
    status: {
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
  },
  glass: {
    // Glass effect configurations
    blur: {
      sm: 'blur(10px)',
      md: 'blur(20px)',
      lg: 'blur(30px)',
      xl: 'blur(40px)',
    },
    opacity: {
      light: 0.1,
      medium: 0.2,
      heavy: 0.3,
      solid: 0.9,
    },
  },
  animation: {
    spring: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
    },
    smooth: {
      type: 'tween',
      duration: 0.3,
      ease: 'easeInOut',
    },
    fast: {
      type: 'tween',
      duration: 0.15,
      ease: 'easeOut',
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  borderRadius: {
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    '2xl': '2rem',
    full: '9999px',
  },
};

// ============================================
// GLASSMORPHIC BASE COMPONENTS
// ============================================

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'interactive' | 'ai';
  blur?: 'sm' | 'md' | 'lg' | 'xl';
  glow?: boolean;
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

export const GlassCard = ({
  children,
  className,
  variant = 'default',
  blur = 'lg',
  glow = false,
  hoverable = true,
  clickable = false,
  onClick,
}: GlassCardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, []);

  const baseStyles = cn(
    'relative overflow-hidden rounded-2xl transition-all duration-300',
    'border border-white/10',
    className
  );

  const glassStyles = {
    default: 'bg-gradient-to-br from-white/10 to-white/5',
    elevated: 'bg-gradient-to-br from-white/15 to-white/10 shadow-2xl',
    interactive: 'bg-gradient-to-br from-purple-500/10 to-blue-500/10',
    ai: 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20',
  };

  return (
    <motion.div
      className={baseStyles}
      style={{
        backdropFilter: glassTheme.glass.blur[blur],
        WebkitBackdropFilter: glassTheme.glass.blur[blur],
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hoverable ? { scale: 1.02, y: -5 } : undefined}
      whileTap={clickable ? { scale: 0.98 } : undefined}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseMove={handleMouseMove}
      onClick={onClick}
      transition={glassTheme.animation.spring}
    >
      {/* Glass background */}
      <div className={cn('absolute inset-0', glassStyles[variant])} />

      {/* Glow effect */}
      {glow && (
        <motion.div
          className="absolute inset-0 opacity-0"
          animate={{ opacity: isHovered ? 0.3 : 0 }}
          style={{
            background: `radial-gradient(circle at ${mousePosition.x}px ${mousePosition.y}px, ${glassTheme.colors.accent.glow}, transparent 50%)`,
          }}
        />
      )}

      {/* Border glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl"
        animate={{
          boxShadow: isHovered
            ? `0 0 30px ${glassTheme.colors.accent.glow}, inset 0 0 20px ${glassTheme.colors.purple.glow}`
            : 'none',
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>

      {/* Noise texture overlay */}
      <div className="absolute inset-0 opacity-5 mix-blend-overlay pointer-events-none">
        <svg width="100%" height="100%">
          <filter id="noise">
            <feTurbulence baseFrequency="0.9" numOctaves="4" />
            <feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#noise)" />
        </svg>
      </div>
    </motion.div>
  );
};

// ============================================
// AI COPILOT PANEL
// ============================================

interface AICopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  context?: string;
}

export const AICopilotPanel = ({ isOpen, onClose, context }: AICopilotPanelProps) => {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    // Fetch context-aware suggestions
    if (context) {
      fetchSuggestions(context);
    }
  }, [context]);

  const fetchSuggestions = async (ctx: string) => {
    try {
      const res = await fetch('/api/ai/suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context: ctx }),
      });
      const data = await res.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    
    setIsStreaming(true);
    setResponse('');

    try {
      const res = await fetch('/api/ai/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, context }),
      });

      if (!res.ok) throw new Error('AI request failed');

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        setResponse(prev => prev + chunk);
      }
    } catch (error) {
      console.error('AI prompt failed:', error);
      setResponse('Error processing request. Please try again.');
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={glassTheme.animation.spring}
          className="fixed right-0 top-0 h-full w-96 z-50"
        >
          <GlassCard
            className="h-full w-full rounded-l-2xl rounded-r-none"
            variant="ai"
            blur="xl"
          >
            <div className="flex flex-col h-full p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center">
                    <span className="text-white text-lg">🤖</span>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">AI Copilot</h3>
                    <p className="text-xs text-gray-400">Powered by Claude</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-400 mb-2">Suggested actions:</p>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => setPrompt(suggestion)}
                        className="px-3 py-1 rounded-full bg-white/10 text-xs text-white hover:bg-white/20 transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Response area */}
              <div className="flex-1 overflow-y-auto mb-4">
                {response && (
                  <div className="p-4 rounded-xl bg-black/30">
                    <div className="text-white whitespace-pre-wrap">
                      {response}
                      {isStreaming && (
                        <span className="inline-block w-2 h-4 bg-cyan-400 ml-1 animate-pulse" />
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Input area */}
              <div className="border-t border-white/10 pt-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                    placeholder="Ask anything..."
                    className="flex-1 px-4 py-2 rounded-xl bg-white/10 text-white placeholder-gray-400 border border-white/10 focus:outline-none focus:border-cyan-400 transition-colors"
                    disabled={isStreaming}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={isStreaming || !prompt.trim()}
                    className="px-6 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium disabled:opacity-50 hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
                  >
                    {isStreaming ? '...' : 'Send'}
                  </button>
                </div>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// ============================================
// ANIMATED DATA CARD
// ============================================

interface DataCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  onClick?: () => void;
}

export const DataCard = ({ title, value, change, icon, trend = 'neutral', onClick }: DataCardProps) => {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-400',
  };

  return (
    <GlassCard
      className="p-6 cursor-pointer"
      variant="elevated"
      glow
      clickable
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        {icon && (
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
            {icon}
          </div>
        )}
        {change !== undefined && (
          <div className={cn('text-sm font-medium', trendColors[trend])}>
            {trend === 'up' && '↑'}
            {trend === 'down' && '↓'}
            {change > 0 ? '+' : ''}{change}%
          </div>
        )}
      </div>
      <div>
        <p className="text-gray-400 text-sm mb-1">{title}</p>
        <p className="text-2xl font-bold text-white">
          <motion.span
            key={value}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={glassTheme.animation.fast}
          >
            {value}
          </motion.span>
        </p>
      </div>
    </GlassCard>
  );
};

// ============================================
// GLASSMORPHIC TABLE
// ============================================

interface TableColumn {
  key: string;
  label: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface GlassTableProps {
  columns: TableColumn[];
  data: any[];
  onRowClick?: (row: any) => void;
}

export const GlassTable = ({ columns, data, onRowClick }: GlassTableProps) => {
  return (
    <GlassCard variant="default" className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-6 py-4 text-left text-sm font-medium text-gray-400',
                    col.align && `text-${col.align}`
                  )}
                  style={{ width: col.width }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <motion.tr
                key={idx}
                className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                onClick={() => onRowClick?.(row)}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      'px-6 py-4 text-sm text-white',
                      col.align && `text-${col.align}`
                    )}
                  >
                    {row[col.key]}
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
};

// ============================================
// GLASSMORPHIC BUTTON
// ============================================

interface GlassButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  className?: string;
}

export const GlassButton = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  loading = false,
  onClick,
  className,
}: GlassButtonProps) => {
  const sizeStyles = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  const variantStyles = {
    primary: 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white hover:shadow-lg hover:shadow-cyan-500/25',
    secondary: 'bg-white/10 text-white hover:bg-white/20',
    danger: 'bg-red-500/20 text-red-400 hover:bg-red-500/30',
    ghost: 'bg-transparent text-white hover:bg-white/10',
  };

  return (
    <motion.button
      className={cn(
        'relative rounded-xl font-medium transition-all backdrop-blur-md',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        sizeStyles[size],
        variantStyles[variant],
        fullWidth && 'w-full',
        className
      )}
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? (
        <div className="flex items-center justify-center gap-2">
          <motion.div
            className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </motion.button>
  );
};

// ============================================
// GLASSMORPHIC INPUT
// ============================================

interface GlassInputProps {
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  icon?: ReactNode;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export const GlassInput = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  icon,
  error,
  disabled = false,
  className,
}: GlassInputProps) => {
  return (
    <div className={cn('relative', className)}>
      {icon && (
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
          {icon}
        </div>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={cn(
          'w-full px-4 py-3 rounded-xl',
          'bg-white/10 backdrop-blur-md',
          'text-white placeholder-gray-400',
          'border border-white/10',
          'focus:outline-none focus:border-cyan-400',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-all',
          icon && 'pl-12',
          error && 'border-red-500'
        )}
      />
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
};

// ============================================
// ANIMATED CHART COMPONENT
// ============================================

interface ChartDataPoint {
  label: string;
  value: number;
}

interface GlassChartProps {
  data: ChartDataPoint[];
  height?: number;
  showGrid?: boolean;
}

export const GlassChart = ({ data, height = 200, showGrid = true }: GlassChartProps) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <GlassCard variant="default" className="p-6">
      <div className="relative" style={{ height }}>
        {/* Grid lines */}
        {showGrid && (
          <div className="absolute inset-0">
            {[0, 25, 50, 75, 100].map((percent) => (
              <div
                key={percent}
                className="absolute w-full border-t border-white/5"
                style={{ top: `${100 - percent}%` }}
              />
            ))}
          </div>
        )}
        
        {/* Bars */}
        <div className="relative h-full flex items-end justify-between gap-2">
          {data.map((point, idx) => {
            const heightPercent = (point.value / maxValue) * 100;
            
            return (
              <motion.div
                key={idx}
                className="flex-1 relative group"
                initial={{ height: 0 }}
                animate={{ height: `${heightPercent}%` }}
                transition={{ delay: idx * 0.1, ...glassTheme.animation.spring }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-cyan-500 to-purple-600 rounded-t-lg opacity-80 group-hover:opacity-100 transition-opacity" />
                
                {/* Tooltip */}
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  <div className="bg-black/90 backdrop-blur-md px-2 py-1 rounded text-xs text-white whitespace-nowrap">
                    {point.value}
                  </div>
                </div>
                
                {/* Label */}
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-gray-400 whitespace-nowrap">
                  {point.label}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </GlassCard>
  );
};

// ============================================
// NOTIFICATION TOAST
// ============================================

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  onClose?: () => void;
}

export const GlassToast = ({ message, type = 'info', duration = 3000, onClose }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose?.();
    }, duration);
    
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const typeStyles = {
    success: 'from-green-500/20 to-green-600/20 border-green-500/30',
    error: 'from-red-500/20 to-red-600/20 border-red-500/30',
    warning: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30',
    info: 'from-blue-500/20 to-blue-600/20 border-blue-500/30',
  };

  const icons = {
    success: '✓',
    error: '✕',
    warning: '!',
    info: 'i',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.9 }}
      className={cn(
        'fixed bottom-8 right-8 z-50',
        'px-6 py-4 rounded-xl',
        'bg-gradient-to-r backdrop-blur-xl',
        'border',
        'shadow-2xl',
        typeStyles[type]
      )}
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white font-bold">
          {icons[type]}
        </div>
        <p className="text-white">{message}</p>
        <button
          onClick={onClose}
          className="ml-4 text-white/60 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>
    </motion.div>
  );
};

// Export everything as default
export default {
  theme: glassTheme,
  GlassCard,
  AICopilotPanel,
  DataCard,
  GlassTable,
  GlassButton,
  GlassInput,
  GlassChart,
  GlassToast,
};