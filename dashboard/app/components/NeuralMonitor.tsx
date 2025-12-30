"use client";

import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

const socket = io('http://localhost:8000', {
    transports: ['websocket'],
    reconnectionAttempts: 5,
});

export default function NeuralMonitor() {
    const [data, setData] = useState<any[]>([]);

    useEffect(() => {
        socket.on('history', (h: any[]) => setData(h));
        socket.on('new_metric', (m) => setData(p => [...p, m].slice(-50)));
        return () => {
            socket.off('history');
            socket.off('new_metric');
        };
    }, []);

    const chartData = data.map(d => ({
        episode: d.episode,
        avg_firing_rate: d.metrics?.avg_firing_rate || 0,
        maturity: (d.metrics?.maturity || 0) // Already 0-100 from backend
    }));

    const lastEntry = chartData[chartData.length - 1] || {};

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Firing Rate Area Chart */}
            <div className="h-[250px] bg-gray-900 p-6 rounded-xl border border-gray-700 shadow-xl">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-lg font-bold text-yellow-400">⚡ SNN Activity</h3>
                    <span className="text-xl font-mono text-yellow-200">
                        {((lastEntry.avg_firing_rate || 0) * 100).toFixed(2)}% Active
                    </span>
                </div>
                <ResponsiveContainer width="100%" height="80%">
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorFire" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="episode" hide />
                        <YAxis stroke="#9ca3af" fontSize={10} />
                        <Tooltip contentStyle={{ backgroundColor: '#1f2937' }} />
                        <Area type="monotone" dataKey="avg_firing_rate" stroke="#fbbf24" fillOpacity={1} fill="url(#colorFire)" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Maturity Gauge (Progress Bar style) */}
            <div className="h-[250px] bg-gray-900 p-6 rounded-xl border border-gray-700 shadow-xl flex flex-col justify-center items-center">
                <h3 className="text-lg font-bold text-blue-400 mb-4">🧠 Maturity (Learning Phase)</h3>

                <div className="relative w-48 h-48">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
                        {/* Background Circle */}
                        <circle
                            cx="100" cy="100" r="80"
                            stroke="#1f2937" strokeWidth="16" fill="transparent"
                        />
                        {/* Progress Circle */}
                        <circle
                            cx="100" cy="100" r="80"
                            stroke="#60a5fa" strokeWidth="16" fill="transparent"
                            strokeDasharray={2 * Math.PI * 80}
                            strokeDashoffset={2 * Math.PI * 80 * (1 - (lastEntry.maturity || 0) / 100)}
                            strokeLinecap="round"
                            className="transition-all duration-500 ease-out"
                        />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-4xl font-bold text-white">
                            {(lastEntry.maturity || 0).toFixed(1)}%
                        </span>
                        <span className="text-xs text-gray-400 mt-1">Confidence Level</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
