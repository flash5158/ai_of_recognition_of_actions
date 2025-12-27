"use client";

import React, { useRef, useEffect } from 'react';

const ProBackground: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener('resize', resize);
        resize();

        const particles: { x: number, y: number, r: number, a: number, vx: number, vy: number }[] = [];
        const count = Math.floor((canvas.width * canvas.height) / 90000);
        for (let i = 0; i < Math.max(40, count); i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: 0.6 + Math.random() * 1.8,
                a: Math.random() * Math.PI * 2,
                vx: (Math.random() - 0.5) * 0.25,
                vy: (Math.random() - 0.5) * 0.25
            });
        }

        let mouseX = canvas.width / 2;
        let mouseY = canvas.height / 2;

        const onMove = (e: MouseEvent) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        };

        window.addEventListener('mousemove', onMove);

        const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // subtle nebulous gradient
            const g = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
            g.addColorStop(0, 'rgba(59,130,246,0.03)');
            g.addColorStop(0.5, 'rgba(16,185,129,0.02)');
            g.addColorStop(1, 'transparent');
            ctx.fillStyle = g;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            particles.forEach(p => {
                p.x += p.vx + (mouseX - canvas.width / 2) * 0.0002;
                p.y += p.vy + (mouseY - canvas.height / 2) * 0.0002;

                if (p.x < -50) p.x = canvas.width + 50;
                if (p.x > canvas.width + 50) p.x = -50;
                if (p.y < -50) p.y = canvas.height + 50;
                if (p.y > canvas.height + 50) p.y = -50;

                ctx.beginPath();
                ctx.globalAlpha = 0.85;
                ctx.fillStyle = 'rgba(255,255,255,0.02)';
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fill();
            });

            ctx.globalAlpha = 1;
            animationFrameId = window.requestAnimationFrame(draw);
        };

        draw();
        return () => {
            window.removeEventListener('resize', resize);
            window.removeEventListener('mousemove', onMove);
            window.cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none opacity-30 z-[-1]" />;
};

export default ProBackground;
