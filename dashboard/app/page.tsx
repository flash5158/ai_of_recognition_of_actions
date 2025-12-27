"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Activity,
    Shield,
    Cpu,
    Layers,
    Database,
    Settings,
    User,
    Zap
} from 'lucide-react';
import LiveStreamMatrix from './components/LiveStreamMatrix';
import ApexGauge from './components/ApexGauge';
import ProBackground from './components/ProBackground';

interface Detection {
    id: number;
    box: number[];
    conf: number;
    action: string;
    emotion: string;
    emotion_conf: number;
    landmarks: number[][];
}

interface TelemetryData {
    fps: number;
    latency: number;
    track_count: number;
    anomalies: number;
    latest_analysis: string;
    detections: Detection[];
    cam_active: boolean;
    logs: Array<{ id: number; time: string; msg: string; type: string }>;
    db_mode?: string;
}

interface VaultItem {
    id: number;
    person_id: number;
    timestamp: number;
    metadata: { conf?: number; class?: string;[k: string]: unknown };
}

interface AnalyticsData {
    total_incidents: number;
    danger_count: number;
    warning_count: number;
    activity_trend: number[];
}

type TabId = 'realtime' | 'vault' | 'analytics' | 'settings';

export default function Home() {
    const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
    const [uptime, setUptime] = useState(0);
    const [activeTab, setActiveTab] = useState<TabId>('realtime');
    const [settings, setSettings] = useState({ conf_threshold: 0.40, draw_on_server: false });
    const [vaultData, setVaultData] = useState<VaultItem[]>([]);
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [loading, setLoading] = useState(true);

    // WebSocket connection for high-frequency telemetry
    useEffect(() => {
        let socket: WebSocket | null = null;
        let reconnectTimeout: number | null = null;
        let shouldReconnect = true;

        const connect = () => {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.hostname;
                const wsUrl = `${protocol}//${host}:8000/ws/telemetry`;

                socket = new WebSocket(wsUrl);

                socket.onopen = () => {
                    console.log(`WebSocket connected. URL: ${wsUrl}`);
                    setWsConnected(true);
                    setLoading(false);
                };

                socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        setTelemetry(data);
                    } catch (e) {
                        console.error("Telemetry parse error", e);
                    }
                };

                socket.onerror = (error) => {
                    console.error("WebSocket connection error:", error);
                    setWsConnected(false);
                };

                socket.onclose = () => {
                    console.warn("WebSocket disconnected from backend");
                    setWsConnected(false);
                    if (shouldReconnect) {
                        reconnectTimeout = window.setTimeout(() => connect(), 3000);
                    }
                };
            } catch (error) {
                console.error("Failed to create WebSocket:", error);
                setWsConnected(false);
                setLoading(false);
            }
        };

        connect();

        const uptimeInterval = window.setInterval(() => setUptime(prev => prev + 1), 1000);

        return () => {
            shouldReconnect = false;
            if (reconnectTimeout) window.clearTimeout(reconnectTimeout);
            if (socket) socket.close();
            window.clearInterval(uptimeInterval);
        };
    }, []);

    // Simple REST fetch helpers
    const fetchVaultData = useCallback(() => {
        fetch('http://localhost:8000/vault')
            .then(res => res.json())
            .then(data => setVaultData(data))
            .catch(e => console.error("Vault fetch error", e));
    }, []);

    const fetchAnalyticsData = useCallback(() => {
        fetch('http://localhost:8000/analytics')
            .then(res => res.json())
            .then(data => setAnalyticsData(data))
            .catch(e => console.error("Analytics fetch error", e));
    }, []);

    // Load data when tab changes
    useEffect(() => {
        if (activeTab === 'vault') {
            fetchVaultData();
        } else if (activeTab === 'analytics') {
            fetchAnalyticsData();
        }
    }, [activeTab, fetchVaultData, fetchAnalyticsData]);

    const updateSettings = useCallback(async (newSettings: Partial<typeof settings>) => {
        try {
            const host = window.location.hostname;
            const res = await fetch(`http://${host}:8000/update_settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSettings)
            });
            if (res.ok) {
                setSettings(prev => ({ ...prev, ...newSettings }));
            }
        } catch (e) {
            console.error("Failed to update settings", e);
        }
    }, []);

    const formatUptime = (s: number) => {
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
    };

    return (
        <div className="apex-container hardware-accel">
            <ProBackground />
            <div className="scanline-subtle" />

            {/* TOP NAVIGATION BAR: Executive Polish */}
            <header className="flex justify-between items-center px-6 py-4 frost-panel">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-700 to-blue-900 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/20">
                            <Shield className="text-white" size={22} />
                        </div>
                        <h1 className="pro-header t-h1 tracking-tighter text-[26px]">CHALAS AI <span className="text-blue-500">RECOGNITION</span></h1>
                    </div>
                    <nav className="flex items-center gap-2 border-l border-white/10 pl-6 h-8">
                        {[
                            { id: 'realtime', label: 'Monitor', icon: Activity },
                            { id: 'vault', label: 'Bóveda', icon: Database },
                            { id: 'analytics', label: 'Análisis', icon: Layers },
                            { id: 'settings', label: 'Config', icon: Settings }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as TabId)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all t-label text-[10px] uppercase font-black tracking-widest ${activeTab === tab.id
                                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.1)]'
                                    : 'text-white/30 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                <tab.icon size={14} />
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                <div className="flex items-center gap-4">
                    {/* Connection Status Indicator */}
                    {loading ? (
                        <div className="bg-yellow-500/10 px-4 py-2 rounded-full border border-yellow-500/20 flex items-center gap-3">
                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse shadow-[0_0_10px_#eab308]" />
                            <span className="mono-data text-[11px] font-bold text-yellow-500 uppercase tracking-tighter">CONECTANDO...</span>
                        </div>
                    ) : wsConnected ? (
                        <div className="bg-emerald-500/10 px-4 py-2 rounded-full border border-emerald-500/20 flex items-center gap-3">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]" />
                            <span className="mono-data text-[11px] font-bold text-emerald-500 uppercase tracking-tighter">BACKEND EN LÍNEA</span>
                        </div>
                    ) : (
                        <div className="bg-red-500/10 px-4 py-2 rounded-full border border-red-500/20 flex items-center gap-3">
                            <div className="w-2 h-2 bg-red-500 rounded-full shadow-[0_0_10px_#ef4444]" />
                            <span className="mono-data text-[11px] font-bold text-red-500 uppercase tracking-tighter">RECONNECTING</span>
                        </div>
                    )}

                    <div className="bg-emerald-500/10 px-4 py-2 rounded-full border border-emerald-500/20 flex items-center gap-3">
                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]" />
                        <span className="mono-data text-[11px] font-bold text-emerald-500 uppercase tracking-tighter">TIEMPO: {formatUptime(uptime)}</span>
                    </div>

                    <div className="bg-blue-500/10 px-4 py-2 rounded-full border border-blue-500/20 flex items-center gap-3">
                        <Database size={12} className="text-blue-400" />
                        <span className="mono-data text-[11px] font-bold text-blue-400 uppercase tracking-tighter">
                            {telemetry?.db_mode === 'MILVUS' ? 'NÚCLEO MILVUS' : 'SQLITE LOCAL'}
                        </span>
                    </div>
                    <div className="w-10 h-10 bg-blue-500/10 rounded-2xl flex items-center justify-center border border-blue-500/20">
                        <User size={20} className="text-blue-400" />
                    </div>
                </div>
            </header >

            {/* MAIN DASHBOARD CONTENT */}
            <main className="flex-grow flex gap-6 overflow-hidden">
                <AnimatePresence mode="wait">
                    {activeTab === 'realtime' && (
                        <motion.div
                            key="realtime"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className="flex flex-grow gap-6 w-full"
                        >
                            <aside className="w-80 flex flex-col gap-6 custom-scrollbar-pro overflow-y-auto">
                                <section className="frost-panel p-6 space-y-8">
                                    <h2 className="t-label text-white uppercase tracking-[0.2em] text-[11px]">VITALIDAD DEL SISTEMA</h2>
                                    <div className="space-y-6">
                                        <ApexGauge value={telemetry?.fps || 0} max={60} label="Freq. Inferencia" unit="fps" color="var(--accent-primary)" />
                                        <ApexGauge value={telemetry?.track_count || 0} max={15} label="Perfil de Compromiso" unit="objs" color="var(--accent-success)" />
                                        <ApexGauge value={telemetry?.latency || 0} max={100} label="Latencia del Núcleo" unit="ms" color="var(--accent-warning)" />
                                    </div>
                                </section>

                                <section className="frost-panel p-6 flex-grow">
                                    <h2 className="t-label text-white/40 mb-6 uppercase tracking-[0.2em] text-[8px]">FLUJO DE INTELIGENCIA</h2>
                                    <div className="space-y-4">
                                        {telemetry?.latest_analysis && (
                                            <div className="p-4 bg-blue-600/5 rounded-2xl border-l-4 border-blue-500 shadow-xl">
                                                <div className="text-[10px] text-blue-400 mb-2 font-black uppercase tracking-widest">EVENTO_EN_TIEMPO_REAL</div>
                                                <p className="text-[13px] font-black text-white leading-tight italic uppercase tracking-tight">
                                                    &quot;{telemetry.latest_analysis}&quot;
                                                </p>
                                            </div>
                                        )}
                                        <div className="opacity-10 text-[10px] font-mono space-y-3 pt-4">
                                            <div className="flex justify-between">&gt; KERNEL_QUANTUM_LISTO <span className="text-emerald-500">OK</span></div>
                                            <div className="flex justify-between">&gt; PESOS_NEURONALES_CARGADOS <span className="text-emerald-500">OK</span></div>
                                            <div className="flex justify-between">&gt; ZONA_PERIMETRO_FORZADA <span className="text-blue-500">ACTIVO</span></div>
                                        </div>
                                    </div>
                                </section>
                            </aside>

                            <section className="flex-grow flex flex-col gap-6">
                                <div className="flex-grow frost-panel relative group overflow-hidden">
                                    <LiveStreamMatrix telemetry={telemetry} />
                                </div>
                            </section>
                        </motion.div>
                    )}

                    {activeTab === 'vault' && (
                        <motion.div
                            key="vault"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="flex-grow frost-panel p-8 overflow-y-auto custom-scrollbar-pro"
                        >
                            <div className="flex justify-between items-center mb-10">
                                <div>
                                    <h2 className="t-h1 text-blue-500 text-4xl">Bóveda de Inteligencia</h2>
                                    <p className="t-body text-white/40 mt-2">Firmas de detección históricas y archivos de comportamiento.</p>
                                </div>
                                <button
                                    onClick={() => fetch('http://localhost:8000/vault').then(r => r.json()).then(setVaultData)}
                                    className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 t-label text-[10px] transition-all"
                                >
                                    ACTUALIZAR_FIRMAS
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {vaultData && vaultData.length > 0 ? vaultData.map((item: VaultItem, idx: number) => (
                                    <div key={idx} className="bg-white/5 border border-white/10 rounded-3xl p-6 hover:border-blue-500/30 transition-all group">
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="w-12 h-12 bg-blue-600/10 rounded-2xl flex items-center justify-center border border-blue-500/20">
                                                <User size={24} className="text-blue-400" />
                                            </div>
                                            <span className="mono-data text-[10px] text-white/20">ID: {item.id || item.person_id}</span>
                                        </div>
                                        <div className="space-y-4">
                                            <div>
                                                <div className="t-label text-[9px] text-blue-400 font-bold mb-1">TIMESTAMP</div>
                                                <div className="mono-data text-sm text-white">{new Date(item.timestamp * 1000).toLocaleString()}</div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="t-label text-[9px] text-white/20 mb-1">CONFIANZA</div>
                                                    <div className="text-xs font-black text-emerald-500">{Math.round((item.metadata?.conf || 0) * 100)}%</div>
                                                </div>
                                                <div>
                                                    <div className="t-label text-[9px] text-white/20 mb-1">CLASE</div>
                                                    <div className="text-xs font-black text-white/60 uppercase">{item.metadata?.class || 'PERSONA'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="col-span-full py-20 text-center opacity-20">
                                        <Database size={64} className="mx-auto mb-4" />
                                        <p className="t-label tracking-[0.3em]">BÓVEDA_VACÍA // ESPERANDO_TELEMETRÍA</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'analytics' && (
                        <motion.div
                            key="analytics"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className="flex-grow frost-panel p-12 overflow-y-auto custom-scrollbar-pro"
                        >
                            <div className="mb-16">
                                <h2 className="t-h1 text-blue-500 text-5xl">Analítica Global</h2>
                                <p className="t-body text-white/40 mt-4 text-lg">Tendencias de comportamiento cruzadas y métricas de eficiencia.</p>
                            </div>

                            <div className="grid grid-cols-4 gap-8 mb-16">
                                <div className="bg-white/5 p-8 rounded-[40px] border border-white/10">
                                    <div className="t-label text-blue-400 mb-2">Incidentes Totales</div>
                                    <div className="text-5xl font-black">{analyticsData?.total_incidents || 0}</div>
                                </div>
                                <div className="bg-white/5 p-8 rounded-[40px] border border-white/10">
                                    <div className="t-label text-red-400 mb-2">Peligro Alto</div>
                                    <div className="text-5xl font-black">{analyticsData?.danger_count || 0}</div>
                                </div>
                                <div className="bg-white/5 p-8 rounded-[40px] border border-white/10">
                                    <div className="t-label text-orange-400 mb-2">Advertencias</div>
                                    <div className="text-5xl font-black">{analyticsData?.warning_count || 0}</div>
                                </div>
                                <div className="bg-white/5 p-8 rounded-[40px] border border-white/10">
                                    <div className="t-label text-emerald-400 mb-2">Salud del Sistema</div>
                                    <div className="text-5xl font-black">99.9%</div>
                                </div>
                            </div>

                            <section className="space-y-8">
                                <h3 className="t-label tracking-[0.4em] text-white/30">Tendencia_Actividad_24H</h3>
                                <div className="h-64 flex items-end gap-2 px-6 bg-white/5 rounded-[40px] border border-white/5 p-8">
                                    {analyticsData?.activity_trend && analyticsData.activity_trend.length > 0 ? (
                                        analyticsData.activity_trend.map((val: number, i: number) => (
                                            <motion.div
                                                key={i}
                                                initial={{ height: 0 }}
                                                animate={{ height: `${Math.min(val * 20, 100)}%` }}
                                                className="flex-grow bg-blue-500/20 border-t-2 border-blue-500/50 rounded-t-lg relative group"
                                            >
                                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-blue-500 text-[10px] px-2 py-1 rounded font-black">
                                                    {val}
                                                </div>
                                            </motion.div>
                                        ))
                                    ) : (
                                        <div className="flex-grow flex items-center justify-center text-white/10 t-label text-[10px]">
                                            NO_HAY_DATOS_DE_ACTIVIDAD
                                        </div>
                                    )}
                                </div>
                            </section>
                        </motion.div>
                    )}

                    {activeTab === 'settings' && (
                        <motion.div
                            key="settings"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="flex-grow frost-panel p-12 overflow-y-auto custom-scrollbar-pro"
                        >
                            <div className="max-w-4xl mx-auto space-y-16">
                                <div className="border-b border-white/10 pb-10">
                                    <h2 className="t-h1 text-blue-500 text-5xl">Orquestación del Sistema</h2>
                                    <p className="t-body text-white/40 mt-4 text-lg">Ajuste los parámetros del motor Quantum Apex y la asignación de hardware.</p>
                                </div>

                                <section className="grid grid-cols-2 gap-16">
                                    <div className="space-y-6">
                                        <div className="flex items-center gap-3">
                                            <Zap size={20} className="text-blue-500" />
                                            <label className="t-label text-lg font-black tracking-tight">Filtro de Confianza IA</label>
                                        </div>
                                        <p className="text-sm text-white/30 leading-relaxed">Ajuste la sensibilidad del núcleo de inferencia YOLOv11. Valores más bajos capturan más movimiento pero aumentan el ruido.</p>
                                        <input
                                            type="range" min="10" max="95"
                                            value={settings.conf_threshold * 100}
                                            onChange={(e) => updateSettings({ conf_threshold: parseInt(e.target.value) / 100 })}
                                            className="w-full h-2 bg-white/5 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                        />
                                        <div className="flex justify-between t-label text-[10px] font-mono text-blue-400 px-1">
                                            <span>SENSIBLE</span>
                                            <span className="text-xl font-black">{Math.round(settings.conf_threshold * 100)}%</span>
                                            <span>ESTRICTO</span>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="flex items-center gap-3">
                                            <Cpu size={20} className="text-emerald-500" />
                                            <label className="t-label text-lg font-black tracking-tight">Descarga Computacional</label>
                                        </div>
                                        <p className="text-sm text-white/30 leading-relaxed">Cambie entre dibujo en el servidor (mayor uso de CPU) y renderizado SVG del cliente (alto rendimiento).</p>
                                        <button
                                            onClick={() => updateSettings({ draw_on_server: !settings.draw_on_server })}
                                            className={`w-full py-5 rounded-3xl border-2 transition-all t-label font-black text-xs tracking-[0.2em] ${settings.draw_on_server
                                                ? 'bg-orange-500/10 border-orange-500/40 text-orange-500 shadow-[0_0_30px_rgba(249,115,22,0.1)]'
                                                : 'bg-emerald-500/10 border-emerald-500/40 text-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.1)]'
                                                }`}
                                        >
                                            {settings.draw_on_server ? 'TERMINAR_RENDER_SERVIDOR' : 'ACTIVAR_RENDER_CLIENTE'}
                                        </button>
                                    </div>
                                </section>

                                <div className="bg-white/5 p-10 rounded-[40px] border border-white/10 flex justify-between items-center group hover:bg-white/[0.07] transition-all">
                                    <div className="flex items-center gap-8">
                                        <div className="w-20 h-20 bg-blue-600/10 rounded-[30px] flex items-center justify-center border border-blue-500/20 group-hover:scale-110 transition-transform">
                                            <Shield size={40} className="text-blue-500" />
                                        </div>
                                        <div>
                                            <h3 className="t-h2 text-2xl font-black">Sincronización de Núcleo Seguro</h3>
                                            <p className="t-body text-white/40 mt-1">Túnel de telemetría cifrado de extremo a extremo establecido.</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-center gap-2">
                                        <div className="w-4 h-4 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_20px_#10b981]" />
                                        <span className="t-label text-[8px] text-emerald-500 font-black">CIFRADO</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main >
        </div >
    );
}
