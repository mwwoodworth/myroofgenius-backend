/**
 * ULTRA PREMIUM GLASSMORPHISM DESIGN SYSTEM
 * The Most Beautiful, Futuristic, Professional UI Ever Created
 * For BrainOps, MyRoofGenius, WeatherCraft - The Future of Business Software
 */

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';

// ============================================
// DESIGN TOKENS - ULTRA PREMIUM CONFIGURATION
// ============================================

export const ULTRA_PREMIUM_THEME = {
  // Quantum Glass Colors - Next Generation
  quantum: {
    dark: {
      void: '#030014',        // Absolute void black
      deep: '#0A0A1F',        // Deep space
      primary: '#0F0F2B',     // Primary dark
      secondary: '#141432',   // Secondary dark
      surface: '#1A1A3E',     // Surface dark
    },
    glass: {
      ultra: 'rgba(6, 0, 30, 0.98)',      // Ultra premium glass
      premium: 'rgba(15, 15, 43, 0.95)',   // Premium glass
      standard: 'rgba(26, 26, 62, 0.92)',  // Standard glass
      light: 'rgba(35, 35, 75, 0.88)',     // Light glass
      subtle: 'rgba(45, 45, 90, 0.85)',    // Subtle glass
    },
    blur: {
      extreme: '120px',    // Extreme blur
      heavy: '80px',       // Heavy blur
      strong: '60px',      // Strong blur
      medium: '40px',      // Medium blur
      light: '20px',       // Light blur
      subtle: '12px',      // Subtle blur
    },
  },
  
  // Neon Accent System - Professional Excellence
  neon: {
    cyan: {
      primary: '#00D9FF',    // Electric cyan
      glow: '#00F0FF',       // Cyan glow
      deep: '#0099CC',       // Deep cyan
      light: '#66EEFF',      // Light cyan
      pulse: 'rgba(0, 217, 255, 0.6)',
    },
    purple: {
      primary: '#A855F7',    // Royal purple
      glow: '#C084FC',       // Purple glow
      deep: '#7C3AED',       // Deep purple
      light: '#DDA6FF',      // Light purple
      pulse: 'rgba(168, 85, 247, 0.6)',
    },
    emerald: {
      primary: '#10B981',    // Success emerald
      glow: '#34D399',       // Emerald glow
      deep: '#059669',       // Deep emerald
      light: '#6EE7B7',      // Light emerald
      pulse: 'rgba(16, 185, 129, 0.6)',
    },
    gold: {
      primary: '#FFB800',    // Premium gold
      glow: '#FFC933',       // Gold glow
      deep: '#CC9400',       // Deep gold
      light: '#FFD966',      // Light gold
      pulse: 'rgba(255, 184, 0, 0.6)',
    },
  },
  
  // Premium Shadows - Multi-layered Excellence
  shadows: {
    quantum: `
      0 0 0 1px rgba(0, 217, 255, 0.1),
      0 2px 8px -2px rgba(0, 0, 0, 0.8),
      0 6px 20px -5px rgba(0, 217, 255, 0.2),
      0 12px 48px -12px rgba(168, 85, 247, 0.25),
      0 24px 80px -20px rgba(0, 0, 0, 0.9),
      inset 0 0 0 1px rgba(255, 255, 255, 0.08),
      inset 0 2px 0 0 rgba(255, 255, 255, 0.1)
    `,
    hover: `
      0 0 0 1px rgba(0, 217, 255, 0.3),
      0 4px 12px -2px rgba(0, 0, 0, 0.9),
      0 12px 32px -8px rgba(0, 217, 255, 0.4),
      0 20px 60px -15px rgba(168, 85, 247, 0.35),
      0 32px 100px -24px rgba(0, 0, 0, 0.95),
      inset 0 0 0 1px rgba(255, 255, 255, 0.12),
      inset 0 2px 0 0 rgba(255, 255, 255, 0.15)
    `,
    active: `
      0 0 0 1px rgba(0, 217, 255, 0.5),
      0 1px 4px -1px rgba(0, 0, 0, 0.9),
      0 3px 12px -3px rgba(0, 217, 255, 0.3),
      inset 0 2px 8px -2px rgba(0, 0, 0, 0.5)
    `,
  },
  
  // Animation Presets - Smooth & Professional
  animations: {
    transition: {
      instant: { duration: 0.1 },
      fast: { duration: 0.2, ease: [0.23, 1, 0.32, 1] },
      smooth: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
      spring: { type: "spring", stiffness: 400, damping: 30 },
      glide: { duration: 0.6, ease: [0.43, 0.13, 0.23, 0.96] },
      elastic: { type: "spring", stiffness: 200, damping: 20 },
    },
  },
};

// ============================================
// QUANTUM GLASS CARD - ULTIMATE PREMIUM
// ============================================

export const QuantumGlassCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  glowColor?: 'cyan' | 'purple' | 'emerald' | 'gold';
}> = ({ children, className = '', hoverable = true, glowColor = 'cyan' }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };
  
  const glowColors = {
    cyan: ULTRA_PREMIUM_THEME.neon.cyan,
    purple: ULTRA_PREMIUM_THEME.neon.purple,
    emerald: ULTRA_PREMIUM_THEME.neon.emerald,
    gold: ULTRA_PREMIUM_THEME.neon.gold,
  };
  
  const glow = glowColors[glowColor];
  
  return (
    <motion.div
      ref={cardRef}
      className={`quantum-glass-card ${className}`}
      onMouseMove={handleMouseMove}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hoverable ? { 
        scale: 1.02,
        rotateX: 2,
        rotateY: -2,
      } : {}}
      transition={ULTRA_PREMIUM_THEME.animations.transition.smooth}
      style={{
        background: `
          radial-gradient(
            circle at ${mousePosition.x}px ${mousePosition.y}px,
            ${glow.pulse} 0%,
            transparent 25%
          ),
          linear-gradient(
            135deg,
            ${ULTRA_PREMIUM_THEME.quantum.glass.ultra} 0%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.premium} 50%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.standard} 100%
          )
        `,
        backdropFilter: `blur(${ULTRA_PREMIUM_THEME.quantum.blur.strong}) saturate(200%)`,
        WebkitBackdropFilter: `blur(${ULTRA_PREMIUM_THEME.quantum.blur.strong}) saturate(200%)`,
        boxShadow: ULTRA_PREMIUM_THEME.shadows.quantum,
        border: `1px solid ${glow.pulse}`,
        borderRadius: '32px',
        padding: '32px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Holographic Shimmer Overlay */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          background: `
            linear-gradient(
              105deg,
              transparent 40%,
              ${glow.light} 50%,
              transparent 60%
            )
          `,
          animation: 'shimmer 2s infinite',
        }}
      />
      
      {/* Premium Border Gradient */}
      <div 
        className="absolute inset-0 rounded-[32px]"
        style={{
          background: `
            linear-gradient(
              90deg,
              ${glow.primary},
              ${glow.glow},
              ${glow.primary}
            )
          `,
          padding: '1px',
          WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
          WebkitMaskComposite: 'xor',
          maskComposite: 'exclude',
          opacity: 0.5,
        }}
      />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

// ============================================
// NEON GLASS BUTTON - PROFESSIONAL EXCELLENCE
// ============================================

export const NeonGlassButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'accent' | 'danger';
  size?: 'small' | 'medium' | 'large' | 'xlarge';
  fullWidth?: boolean;
  disabled?: boolean;
  loading?: boolean;
}> = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium',
  fullWidth = false,
  disabled = false,
  loading = false,
}) => {
  const [isPressed, setIsPressed] = useState(false);
  
  const variants = {
    primary: {
      bg: 'linear-gradient(135deg, rgba(0, 217, 255, 0.2), rgba(168, 85, 247, 0.1))',
      border: ULTRA_PREMIUM_THEME.neon.cyan.primary,
      glow: ULTRA_PREMIUM_THEME.neon.cyan.glow,
      text: '#FFFFFF',
    },
    secondary: {
      bg: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(0, 217, 255, 0.1))',
      border: ULTRA_PREMIUM_THEME.neon.purple.primary,
      glow: ULTRA_PREMIUM_THEME.neon.purple.glow,
      text: '#FFFFFF',
    },
    accent: {
      bg: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(255, 184, 0, 0.1))',
      border: ULTRA_PREMIUM_THEME.neon.emerald.primary,
      glow: ULTRA_PREMIUM_THEME.neon.emerald.glow,
      text: '#FFFFFF',
    },
    danger: {
      bg: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.1))',
      border: '#EF4444',
      glow: '#FCA5A5',
      text: '#FFFFFF',
    },
  };
  
  const sizes = {
    small: { padding: '8px 16px', fontSize: '14px', borderRadius: '12px' },
    medium: { padding: '12px 24px', fontSize: '16px', borderRadius: '16px' },
    large: { padding: '16px 32px', fontSize: '18px', borderRadius: '20px' },
    xlarge: { padding: '20px 40px', fontSize: '20px', borderRadius: '24px' },
  };
  
  const style = variants[variant];
  const sizeStyle = sizes[size];
  
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      transition={ULTRA_PREMIUM_THEME.animations.transition.spring}
      style={{
        ...sizeStyle,
        width: fullWidth ? '100%' : 'auto',
        background: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        boxShadow: isPressed 
          ? ULTRA_PREMIUM_THEME.shadows.active
          : `
            0 0 20px ${style.glow}66,
            0 0 40px ${style.glow}33,
            ${ULTRA_PREMIUM_THEME.shadows.quantum}
          `,
        fontWeight: 600,
        letterSpacing: '0.5px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        position: 'relative',
        overflow: 'hidden',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
      }}
    >
      {/* Animated Gradient Overlay */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(90deg, transparent, ${style.glow}33, transparent)`,
        }}
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "linear",
        }}
      />
      
      {/* Loading Spinner */}
      {loading && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          style={{
            width: '16px',
            height: '16px',
            border: `2px solid ${style.text}33`,
            borderTopColor: style.text,
            borderRadius: '50%',
          }}
        />
      )}
      
      {/* Button Content */}
      <span className="relative z-10">
        {children}
      </span>
    </motion.button>
  );
};

// ============================================
// HOLOGRAPHIC PANEL - NEXT GENERATION
// ============================================

export const HolographicPanel: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => {
  const { scrollY } = useScroll();
  const parallax = useTransform(scrollY, [0, 1000], [0, -50]);
  
  return (
    <motion.div
      className={`holographic-panel ${className}`}
      style={{
        y: parallax,
        background: `
          linear-gradient(
            135deg,
            ${ULTRA_PREMIUM_THEME.quantum.glass.ultra} 0%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.premium} 25%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.standard} 50%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.light} 75%,
            ${ULTRA_PREMIUM_THEME.quantum.glass.subtle} 100%
          )
        `,
        backdropFilter: `blur(${ULTRA_PREMIUM_THEME.quantum.blur.extreme}) saturate(250%)`,
        WebkitBackdropFilter: `blur(${ULTRA_PREMIUM_THEME.quantum.blur.extreme}) saturate(250%)`,
        border: `2px solid ${ULTRA_PREMIUM_THEME.neon.cyan.pulse}`,
        borderRadius: '40px',
        padding: '48px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: `
          0 0 80px ${ULTRA_PREMIUM_THEME.neon.cyan.pulse},
          0 0 120px ${ULTRA_PREMIUM_THEME.neon.purple.pulse},
          ${ULTRA_PREMIUM_THEME.shadows.quantum}
        `,
      }}
    >
      {/* Animated Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div
          style={{
            backgroundImage: `
              repeating-linear-gradient(
                45deg,
                ${ULTRA_PREMIUM_THEME.neon.cyan.primary} 0,
                ${ULTRA_PREMIUM_THEME.neon.cyan.primary} 1px,
                transparent 1px,
                transparent 15px
              ),
              repeating-linear-gradient(
                -45deg,
                ${ULTRA_PREMIUM_THEME.neon.purple.primary} 0,
                ${ULTRA_PREMIUM_THEME.neon.purple.primary} 1px,
                transparent 1px,
                transparent 15px
              )
            `,
            animation: 'holographic-shift 10s linear infinite',
          }}
          className="absolute inset-0"
        />
      </div>
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

// ============================================
// PREMIUM INPUT FIELD - REFINED EXCELLENCE
// ============================================

export const PremiumInput: React.FC<{
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: string;
  icon?: React.ReactNode;
  error?: string;
}> = ({ placeholder, value, onChange, type = 'text', icon, error }) => {
  const [isFocused, setIsFocused] = useState(false);
  
  return (
    <div className="premium-input-wrapper">
      <motion.div
        animate={{
          borderColor: isFocused 
            ? ULTRA_PREMIUM_THEME.neon.cyan.primary 
            : error 
            ? '#EF4444'
            : 'rgba(0, 217, 255, 0.2)',
        }}
        transition={ULTRA_PREMIUM_THEME.animations.transition.fast}
        style={{
          background: ULTRA_PREMIUM_THEME.quantum.glass.ultra,
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid',
          borderRadius: '16px',
          padding: '16px',
          position: 'relative',
          boxShadow: isFocused 
            ? `0 0 30px ${ULTRA_PREMIUM_THEME.neon.cyan.pulse}`
            : 'none',
        }}
      >
        <div className="flex items-center gap-3">
          {icon && (
            <div className="text-gray-400">
              {icon}
            </div>
          )}
          <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#FFFFFF',
              fontSize: '16px',
              width: '100%',
              '::placeholder': {
                color: 'rgba(255, 255, 255, 0.4)',
              },
            }}
          />
        </div>
      </motion.div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-red-400 text-sm mt-2 ml-2"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
};

// ============================================
// CSS STYLES - PROFESSIONAL ANIMATIONS
// ============================================

export const ultraPremiumStyles = `
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  
  @keyframes holographic-shift {
    0% { background-position: 0 0; }
    100% { background-position: 100px 100px; }
  }
  
  @keyframes pulse-glow {
    0%, 100% { 
      opacity: 0.5;
      filter: blur(20px);
    }
    50% { 
      opacity: 0.8;
      filter: blur(30px);
    }
  }
  
  @keyframes quantum-float {
    0%, 100% { 
      transform: translateY(0) translateZ(0) rotateX(0) rotateY(0);
    }
    25% { 
      transform: translateY(-20px) translateZ(10px) rotateX(2deg) rotateY(-2deg);
    }
    50% { 
      transform: translateY(-10px) translateZ(20px) rotateX(-1deg) rotateY(1deg);
    }
    75% { 
      transform: translateY(-15px) translateZ(10px) rotateX(1deg) rotateY(2deg);
    }
  }
  
  /* Professional Typography */
  .ultra-heading {
    font-size: clamp(2.5rem, 5vw, 4.5rem);
    font-weight: 900;
    letter-spacing: -0.02em;
    line-height: 1.1;
    background: linear-gradient(
      135deg,
      ${ULTRA_PREMIUM_THEME.neon.cyan.primary} 0%,
      ${ULTRA_PREMIUM_THEME.neon.purple.primary} 50%,
      ${ULTRA_PREMIUM_THEME.neon.cyan.primary} 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
    animation: gradient-shift 8s ease infinite;
  }
  
  /* Premium Scrollbar */
  ::-webkit-scrollbar {
    width: 12px;
    height: 12px;
  }
  
  ::-webkit-scrollbar-track {
    background: ${ULTRA_PREMIUM_THEME.quantum.dark.void};
    border: 1px solid ${ULTRA_PREMIUM_THEME.neon.cyan.pulse};
  }
  
  ::-webkit-scrollbar-thumb {
    background: linear-gradient(
      135deg,
      ${ULTRA_PREMIUM_THEME.neon.cyan.primary},
      ${ULTRA_PREMIUM_THEME.neon.purple.primary}
    );
    border-radius: 6px;
    border: 2px solid ${ULTRA_PREMIUM_THEME.quantum.dark.void};
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(
      135deg,
      ${ULTRA_PREMIUM_THEME.neon.cyan.glow},
      ${ULTRA_PREMIUM_THEME.neon.purple.glow}
    );
  }
  
  /* Selection Style */
  ::selection {
    background: ${ULTRA_PREMIUM_THEME.neon.cyan.pulse};
    color: #FFFFFF;
  }
`;

// Export everything for use across all projects
export default {
  QuantumGlassCard,
  NeonGlassButton,
  HolographicPanel,
  PremiumInput,
  ULTRA_PREMIUM_THEME,
  ultraPremiumStyles,
};