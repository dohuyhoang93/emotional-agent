"use client";

import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

const socket = io('http://localhost:8001', {
    transports: ['websocket'],
    reconnectionAttempts: 5,
});

export default function SuccessChart() {
    const [data, setData] = useState<any[]>([]);

    useEffect(() => {
        socket.on('history', (historyData: any[]) => {
            setData(historyData);
        });

        socket.on('new_metric', (metric) => {
            setData((prev) => {
                const newData = [...prev, metric];
                if (newData.length > 50) return newData.slice(newData.length - 50);
                return newData;
            });
        });

        return () => {
            socket.off('history');
            socket.off('new_metric');
        };
    }, []);

    const chartData = data.map(d => {
        const flat: any = { episode: d.episode };
        if (d.metrics) {
            flat.success_rate = (d.metrics.success_rate || 0) * 100; // Convert to %
            // Agent success
            if (Array.isArray(d.metrics.agent_success)) {
                d.metrics.agent_success.forEach((s: boolean, i: number) => {
                    flat[`agent_${i}`] = s ? 100 : 0;
                });
            }
        }
        return flat;
    });

    return (
        <div className="w-full h-[300px] bg-gray-900 p-6 rounded-xl border border-gray-700 shadow-xl">
            <h2 className="text-xl font-bold mb-4 text-green-400">Success Rate (%)</h2>
            <ResponsiveContainer width="100%" height="85%">
                <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="episode" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                    <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} domain={[0, 100]} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend />
                    <Bar dataKey="success_rate" fill="#34d399" name="Global Success Rate" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
