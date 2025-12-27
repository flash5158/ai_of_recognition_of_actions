"use client";

import React, { useRef, useEffect } from 'react';

interface WaveformCanvasProps {
    width?: number;
    height?: number;
    speed?: number;
    color?: string;
    points?: number;
}

const WaveformCanvas: React.FC<WaveformCanvasProps> = ({
    width = 300,
    height = 100,
    speed = 0.05,
    color = "#00f2ff",
    points = 100
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;
        let offset = 0;

        const draw = () => {
            ctx.clearRect(0, 0, width, height);
            ctx.beginPath();
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.setLineDash([]);

            const step = width / points;

            for (let i = 0; i <= points; i++) {
                const x = i * step;
                // Complex wave simulation
                const y = height / 2 +
                    Math.sin(i * 0.2 + offset) * (height / 4) +
                    Math.sin(i * 0.1 - offset * 0.5) * (height / 8);

                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }

            ctx.stroke();

            // Add area fill
            ctx.lineTo(width, height);
            ctx.lineTo(0, height);
            ctx.fillStyle = `${color}05`;
            ctx.fill();

            offset += speed;
            animationFrameId = window.requestAnimationFrame(draw);
        };

        draw();
        return () => window.cancelAnimationFrame(animationFrameId);
    }, [width, height, speed, color, points]);

    return (
        <canvas
            ref={canvasRef}
            width={width}
            height={height}
            className="w-full h-full opacity-60"
        />
    );
};

export default WaveformCanvas;
