"use client";

import React from 'react';

const GlobalMap: React.FC = () => {
    return (
        <div className="relative w-full h-full flex items-center justify-center opacity-40">
            <svg viewBox="0 0 200 100" className="w-full h-full text-cyan-500">
                {/* World Outline Simplified Dots */}
                {Array.from({ length: 20 }).map((_, i) => (
                    <g key={i}>
                        {Array.from({ length: 40 }).map((_, j) => {
                            // Dummy logic to simulate landmasses
                            const isLand = Math.sin(j * 0.5) + Math.cos(i * 0.8) > 0.5;
                            if (!isLand) return null;
                            return (
                                <circle
                                    key={j}
                                    cx={j * 5}
                                    cy={i * 5}
                                    r="0.5"
                                    fill="currentColor"
                                    className="animate-pulse"
                                    style={{ animationDelay: `${(i + j) * 0.1}s` }}
                                />
                            );
                        })}
                    </g>
                ))}

                {/* Connecting lines */}
                <path
                    d="M 40,30 Q 80,10 120,40 M 60,70 Q 100,80 160,20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.2"
                    strokeDasharray="2 2"
                    className="opacity-50"
                />
            </svg>
        </div>
    );
};

export default GlobalMap;
