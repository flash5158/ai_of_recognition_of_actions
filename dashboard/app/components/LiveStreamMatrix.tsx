"use client";
import React from 'react';
import { Shield, Video, VideoOff } from 'lucide-react';
import FullscreenViewer from './FullscreenViewer';
import { motion, AnimatePresence } from 'framer-motion';

interface TelemetryData {
    fps: number;
    latency: number;
    track_count: number;
    anomalies: number;
    latest_analysis: string;
    detections: Detection[];
    cam_active: boolean;
    camera_status?: string;
    frame?: string; // Base64 encoded frame
}

interface Detection {
    id: number;
    box: [number, number, number, number];
    conf: number;
    action?: string;
    emotion?: string;
    emotion_conf?: number;
    landmarks?: [number, number, number, number][]; // [id, x, y, conf]
}

// COCO Skeleton Connections (pairs of indices)
const SKELETON_PAIRS = [
    [5, 7], [7, 9], [6, 8], [8, 10], // Arms
    [11, 13], [13, 15], [12, 14], [14, 16], // Legs
    [5, 6], [11, 12], // Shoulders and Hips
    [5, 11], [6, 12] // Torso
];

export default function LiveStreamMatrix({ telemetry }: { telemetry: TelemetryData | null }) {
    const [fullscreen, setFullscreen] = React.useState(false);
    const [toggling, setToggling] = React.useState(false);

    // Dynamic URL
    const streamSrc = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000/video_feed` : 'http://localhost:8000/video_feed';

    const toggleCamera = async (enabled: boolean) => {
        setToggling(true);
        try {
            const host = window.location.hostname || 'localhost';
            const url = `http://${host}:8000/camera/toggle`;
            const resp = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
            if (!resp.ok) {
                const text = await resp.text().catch(() => '');
                throw new Error(`Toggle request failed: ${resp.status} ${resp.statusText} ${text}`);
            }
        } catch (e) {
            console.error("Hardware control failure", e);
            try { window.alert('No se pudo conectar al backend (toggle cámara). Revisa que el servidor esté activo.'); } catch { }
        } finally {
            setTimeout(() => setToggling(false), 800);
        }
    };

    const canvasRef = React.useRef<HTMLCanvasElement>(null);

    React.useEffect(() => {
        if (telemetry?.frame && canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            if (ctx) {
                const img = new Image();
                img.onload = () => {
                    ctx.drawImage(img, 0, 0, canvasRef.current!.width, canvasRef.current!.height);
                };
                img.src = `data:image/jpeg;base64,${telemetry.frame}`;
            }
        }
    }, [telemetry?.frame]);

    return (
        <div className="relative w-full h-full bg-[#050505] rounded-2xl overflow-hidden border border-white/5 hardware-accel group shadow-2xl">
            {/* 60FPS Optimized Video Feed (WebSocket Canvas) */}
            {telemetry?.cam_active || (telemetry?.camera_status && telemetry.camera_status.includes("ERROR")) ? (
                <div className="w-full h-full relative">
                    {/* Error Overlay */}
                    {telemetry?.camera_status && telemetry.camera_status.includes("ERROR") && (
                        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                            <div className="flex flex-col items-center gap-4 text-red-500 p-8 border border-red-500/30 rounded-2xl bg-black/50">
                                <Shield size={48} className="animate-pulse" />
                                <div className="text-xl font-bold">ERROR DE CÁMARA DETECTADO</div>
                                <div className="text-sm font-mono opacity-80">{telemetry.camera_status}</div>
                                <div className="text-xs text-center text-white/50 max-w-md">
                                    Revisa: Ajustes del Sistema &gt; Privacidad y Seguridad &gt; Cámara.<br />
                                    Asegúrate de que la Terminal/VSCode tenga permiso ACTIVADO.
                                </div>
                                <button className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded" onClick={() => window.open('x-apple.systempreferences:com.apple.preference.security?Privacy_Camera')}>Abrir Configuración de Cámara</button>
                            </div>
                        </div>
                    )}

                    {/* MJPEG Stream Implementation */}
                    {telemetry?.cam_active ? (
                        <div className="relative w-full h-full">
                            {/* Primary MJPEG Stream */}
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src={streamSrc}
                                alt="Live Sensor Feed"
                                className="w-full h-full object-cover"
                                style={{ filter: "contrast(1.06) brightness(1.02) saturate(1.05)" }}
                                onClick={() => setFullscreen(true)}
                            />
                        </div>
                    ) : (
                        <canvas
                            ref={canvasRef}
                            width={1280}
                            height={720}
                            className="hidden" // Connect canvas ref but hide it to satisfy existing logic if needed
                        />
                    )}

                    <div className="absolute left-4 bottom-4 glass-card p-3 flex items-center gap-4">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl flex items-center justify-center border border-white/10">
                            <Shield size={18} />
                        </div>
                        <div>
                            <div className="t-label text-[9px] text-white/40">TRANSMISIÓN EN VIVO</div>
                            <div className="font-black text-sm">UNIDAD DE SENSOR 01</div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="w-full h-full flex items-center justify-center flex-col gap-6 text-white/5">
                    <Shield size={120} className="animate-pulse" />
                    <div className="flex flex-col items-center gap-1">
                        <span className="t-label text-[14px] text-white/20 tracking-[0.3em]">SISTEMA_EN_ESPERA</span>
                        <span className="t-label text-[10px] text-white/10 uppercase font-mono">Sensores Desconectados // IA_INACTIVA</span>
                    </div>
                </div>
            )}

            {/* SVG OVERLAY LAYER */}
            <svg
                className="absolute inset-0 w-full h-full pointer-events-none z-20"
                viewBox="0 0 1280 720"
                preserveAspectRatio="xMidYMid slice"
            >
                <AnimatePresence>
                    {telemetry?.detections?.map((det) => {
                        const [x1, y1, x2, y2] = det.box;
                        return (
                            <motion.g
                                key={det.id}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                            >
                                <rect
                                    x={x1} y={y1} width={x2 - x1} height={y2 - y1}
                                    fill="none" stroke="#60a5fa" strokeWidth="1"
                                    className="opacity-40"
                                />
                                <path d={`M ${x1} ${y1 + 15} V ${y1} H ${x1 + 15}`} stroke="#60a5fa" strokeWidth="2" fill="none" />
                                <path d={`M ${x2 - 15} ${y1} H ${x2} V ${y1 + 15}`} stroke="#60a5fa" strokeWidth="2" fill="none" />
                                <path d={`M ${x1} ${y2 - 15} V ${y2} H ${x1 + 15}`} stroke="#60a5fa" strokeWidth="2" fill="none" />
                                <path d={`M ${x2 - 15} ${y2} H ${x2} V ${y2 - 15}`} stroke="#60a5fa" strokeWidth="2" fill="none" />

                                <text x={x1} y={y1 - 6} className="fill-blue-400 text-[12px] font-bold font-mono italic">
                                    ID_{det.id} [{det.action || "DESCONOCIDO"}] {det.emotion && det.emotion !== "NEUTRAL" ? ` // ${det.emotion}` : ""}
                                </text>

                                {/* Skeleton Rendering */}
                                {det.landmarks && det.landmarks.length > 0 && det.landmarks.map((lm, i) => (
                                    <circle key={`lm-${det.id}-${i}`} cx={lm[1]} cy={lm[2]} r="3" fill="#00e5ff" className="opacity-80" />
                                ))}
                                {det.landmarks && det.landmarks.length > 0 && SKELETON_PAIRS.map((pair, i) => {
                                    const p1 = det.landmarks!.find(l => l[0] === pair[0]);
                                    const p2 = det.landmarks!.find(l => l[0] === pair[1]);
                                    if (p1 && p2 && p1[3] > 0.5 && p2[3] > 0.5) {
                                        return (
                                            <line
                                                key={`bone-${det.id}-${i}`}
                                                x1={p1[1]} y1={p1[2]}
                                                x2={p2[1]} y2={p2[2]}
                                                stroke="#00e5ff"
                                                strokeWidth="2"
                                                className="opacity-70 shadow-[0_0_10px_#00e5ff]"
                                            />
                                        );
                                    }
                                    return null;
                                })}
                            </motion.g>
                        );
                    })}
                </AnimatePresence>
            </svg>

            {/* Overlay UI Layer */}
            <div className="absolute inset-0 pointer-events-none p-6 flex flex-col justify-between z-30">
                <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3 bg-black/60 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10 shadow-2xl">
                        <div className={`w-2 h-2 rounded-full ${telemetry?.cam_active ? 'bg-blue-500 animate-pulse-pro shadow-[0_0_10px_#3b82f6]' : 'bg-red-500'}`} />
                        <span className="t-label text-[11px] text-white/90 font-bold tracking-wider">UNIDAD_SENSOR_01</span>
                    </div>

                    <div className="flex gap-2">
                        {/* Space for extra controls if needed */}
                    </div>
                </div>

                <div className="flex justify-between items-end">
                    <div className="flex flex-col gap-3 max-w-[50%]">
                        <div className="bg-blue-600/10 backdrop-blur-3xl p-5 border border-blue-500/20 rounded-2xl shadow-2xl">
                            <h4 className="t-label text-blue-400 text-[8px] mb-2 uppercase tracking-[0.2em] font-black">INFERENCIA_COGNITIVA_IA</h4>
                            <p className="t-body text-white font-bold leading-tight uppercase tracking-tight text-[13px] italic">
                                {telemetry?.latest_analysis || "Esperando secuencia de adquisición de objetivo..."}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="bg-black/60 backdrop-blur-xl p-3 rounded-2xl border border-white/10 flex gap-4">
                            <div className="flex flex-col items-center px-4 border-r border-white/5">
                                <span className="t-label text-[8px] opacity-40">LATENCIA</span>
                                <span className="mono-data text-blue-400 font-bold text-xs">{telemetry?.latency || 0}ms</span>
                            </div>
                            <div className="flex flex-col items-center px-4">
                                <span className="t-label text-[8px] opacity-40">RASTROS</span>
                                <span className="mono-data text-emerald-500 font-bold text-xs">{telemetry?.track_count || 0}</span>
                            </div>
                        </div>

                        <button
                            onClick={() => toggleCamera(!telemetry?.cam_active)}
                            disabled={toggling}
                            className={`pointer-events-auto px-6 py-4 rounded-xl t-label text-[10px] font-black transition-all flex items-center gap-2 border shadow-xl ${toggling
                                ? 'bg-white/10 border-white/20 text-white/50 cursor-wait'
                                : telemetry?.cam_active
                                    ? 'bg-red-500/10 border-red-500/30 text-red-500 hover:bg-red-500/20'
                                    : 'bg-blue-600 border-blue-500 text-white shadow-[0_0_30px_rgba(59,130,246,0.5)] hover:bg-blue-500'
                                }`}
                        >
                            {toggling ? (
                                <div className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            ) : (
                                telemetry?.cam_active ? <VideoOff size={14} /> : <Video size={14} />
                            )}
                            {toggling ? 'PROCESANDO...' : (telemetry?.cam_active ? 'TERMINAR TRANSMISIÓN' : 'INICIAR SENSORES')}
                        </button>
                    </div>
                </div>
            </div>

            {fullscreen && <FullscreenViewer src={streamSrc} onClose={() => setFullscreen(false)} />}

            {/* Scanline & Grid Effect */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] z-40" />
            </div>
        </div>
    );
}
