"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface RadialGaugeProps {
    value: number;
    max: number;
    label: string;
    subLabel?: string;
    color?: string;
    size?: number;
}

const RadialGauge: React.FC<RadialGaugeProps> = ({
    value,
    max,
    label,
    subLabel,
    color = "#10b981",
    size = 120
}) => {
    const radius = size * 0.4;
    const stroke = 3;
    const normalizedRadius = radius - stroke * 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDashoffset = circumference - (Math.min(value, max) / max) * circumference;

    return (
        <div className="flex flex-col items-center justify-center relative" style={{ width: size, height: size }}>
            <svg
                height={size}
                width={size}
                className="transform -rotate-90"
            >
                {/* Background Circle */}
                <circle
                    stroke="rgba(255,255,255,0.05)"
                    fill="transparent"
                    strokeWidth={stroke}
                    r={normalizedRadius}
                    cx={size / 2}
                    cy={size / 2}
                />
                {/* Progress Circle */}
                <motion.circle
                    stroke={color}
                    fill="transparent"
                    strokeWidth={stroke}
                    strokeDasharray={circumference + ' ' + circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    r={normalizedRadius}
                    cx={size / 2}
                    cy={size / 2}
                    style={{ filter: `drop-shadow(0 0 5px ${color}80)` }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-[10px] font-black text-white leading-none mb-0.5" style={{ textShadow: `0 0 8px ${color}` }}>
                    {Math.round((value / max) * 100)}%
                </span>
                <span className="text-[7px] font-mono text-white/30 uppercase tracking-widest leading-none">
                    {label}
                </span>
                {subLabel && (
                    <span className="text-[6px] font-mono text-white/10 uppercase tracking-tighter mt-1">
                        {subLabel}
                    </span>
                )}
            </div>

            {/* Corner Accents */}
            <div className={`absolute top-0 left-0 w-2 h-2 border-t border-l border-${color === '#10b981' ? 'emerald-500' : 'cyan-500'}/30`}></div>
            <div className={`absolute bottom-0 right-0 w-2 h-2 border-b border-r border-${color === '#10b981' ? 'emerald-500' : 'cyan-500'}/30`}></div>
        </div>
    );
};

export default RadialGauge;
