"use client";

import React from 'react';
import { AreaChart, Area, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
    time: string;
    value: number;
}

const TelemetryChart = ({ data, color = "#10b981" }: { data: ChartData[], color?: string }) => {
    return (
        <div className="w-full h-full opacity-80 hover:opacity-100 transition-opacity duration-500">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0a0a0c', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '10px' }}
                        itemStyle={{ color: color }}
                    />
                    <Area
                        type="monotone"
                        dataKey="value"
                        stroke={color}
                        fillOpacity={1}
                        fill="url(#colorValue)"
                        strokeWidth={2}
                        isAnimationActive={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TelemetryChart;
