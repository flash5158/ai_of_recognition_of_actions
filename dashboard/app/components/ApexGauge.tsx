"use client";
import { motion } from "framer-motion";

interface ApexGaugeProps {
    value: number;
    max: number;
    label: string;
    unit?: string;
    color?: string;
}

export default function ApexGauge({ value, max, label, unit = "", color = "#3b82f6" }: ApexGaugeProps) {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
        <div className="flex flex-col gap-2 group">
            <div className="flex justify-between items-end">
                <span className="t-label text-[10px] text-white/40 group-hover:text-white/60 transition-colors uppercase tracking-widest">{label}</span>
                <div className="flex items-baseline gap-1">
                    <span className="mono-data text-sm font-bold text-white">{value}</span>
                    {unit && <span className="t-label text-[8px] opacity-30">{unit}</span>}
                </div>
            </div>

            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5 relative">
                {/* Track segments for tactical look */}
                <div className="absolute inset-0 flex justify-between px-2 opacity-10">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-full w-[1px] bg-white" />
                    ))}
                </div>

                <motion.div
                    className="h-full rounded-full relative"
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    style={{
                        backgroundColor: color,
                        boxShadow: `0 0 15px ${color}44`
                    }}
                >
                    {/* Shine effect */}
                    <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20" />
                </motion.div>
            </div>
        </div>
    );
}
