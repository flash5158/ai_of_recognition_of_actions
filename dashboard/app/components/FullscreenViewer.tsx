"use client";

import React from 'react';
import Image from 'next/image';
import { X } from 'lucide-react';

export default function FullscreenViewer({ src, onClose }: { src: string; onClose: () => void }) {
    return (
        <div className="fullscreen-viewer" role="dialog" aria-modal="true">
            <div className="fullscreen-inner glass-card">
                <div className="lens-flare" />
                <button onClick={onClose} className="absolute right-4 top-4 z-40 bg-black/30 p-3 rounded-full border border-white/10">
                    <X size={18} />
                </button>
                <div className="relative w-full h-full">
                    <Image src={src} alt="Stream fullscreen" fill style={{ objectFit: 'cover' }} unoptimized priority />
                </div>
            </div>
        </div>
    );
}
