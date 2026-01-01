"use client";

import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Connect to backend (adjust port if needed)
const socket = io('http://localhost:8001', {
  transports: ['websocket'],
  reconnectionAttempts: 5,
});

export default function RealtimeChart() {
  const [data, setData] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to WebSocket');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected');
      setConnected(false);
    });

    socket.on('history', (historyData: any[]) => {
      console.log('Received history:', historyData.length);
      setData(historyData);
    });

    socket.on('new_metric', (metric) => {
      // console.log('New metric:', metric);
      setData((prev) => {
        // Keep last 50 points to show trend without overcrowding
        const newData = [...prev, metric];
        if (newData.length > 50) return newData.slice(newData.length - 50);
        return newData;
      });
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('history');
      socket.off('new_metric');
    };
  }, []);

  if (!connected) {
    return <div className="text-yellow-500">Connecting to Experiment Backend...</div>;
  }

  // Extract keys from metrics if available (e.g. 'reward', 'loss')
  // We assume structure: { episode: 1, metrics: { agents: [...], global: {...} } }
  // Let's visualize Global Average Return if available, or just raw data structure.
  // Based on current Theus, 'metrics' usually contains 'avg_reward', 'avg_loss'.

  // Flatten data for Recharts
  const chartData = data.map(d => {
    const flat: any = { episode: d.episode };

    // Global/Avg Metrics
    if (d.metrics) {
      if (d.metrics.global) {
        flat.avg_reward = d.metrics.global.avg_return || 0;
        flat.avg_loss = d.metrics.global.avg_loss || 0;
      } else if (d.metrics.avg_reward !== undefined) {
        flat.avg_reward = d.metrics.avg_reward;
      }

      // Individual Agent Rewards
      if (Array.isArray(d.metrics.agent_rewards)) {
        d.metrics.agent_rewards.forEach((reward: number, idx: number) => {
          flat[`agent_${idx}`] = reward;
        });
      }
    }
    return flat;
  });

  // Calculate distinct agent keys from the last data point to generate lines dynamically
  const sample = chartData[chartData.length - 1] || {};
  const agentKeys = Object.keys(sample).filter(k => k.startsWith('agent_'));
  const colors = ['#f87171', '#fbbf24', '#34d399', '#60a5fa', '#a78bfa', '#f472b6']; // Tailwind-ish palette

  return (
    <div className="w-full h-[500px] bg-gray-900 p-6 rounded-xl border border-gray-700 shadow-2xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-cyan-400 tracking-tight">System Metrics</h2>
          <p className="text-gray-500 text-sm">Real-time reward aggregation per episode</p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 rounded-full bg-cyan-900/30 text-cyan-300 text-xs border border-cyan-800">Avg Reward</span>
          <span className="px-3 py-1 rounded-full bg-purple-900/30 text-purple-300 text-xs border border-purple-800">Agent Details</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis
            dataKey="episode"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#4b5563' }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#4b5563' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              borderColor: '#374151',
              borderRadius: '8px',
              padding: '12px',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
            }}
            itemStyle={{ color: '#e5e7eb', fontSize: '13px', fontWeight: 500 }}
            labelStyle={{ color: '#9ca3af', marginBottom: '8px', fontSize: '12px' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />

          {/* Main Average Line */}
          <Line
            type="monotone"
            dataKey="avg_reward"
            stroke="#22d3ee"
            strokeWidth={3}
            dot={false}
            name="Global Avg Reward"
            activeDot={{ r: 6, strokeWidth: 0 }}
            isAnimationActive={false}
          />

          {/* Individual Agent Lines (Thinner, semi-transparent) */}
          {agentKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length]}
              strokeWidth={1.5}
              strokeOpacity={0.7}
              dot={false}
              name={`Agent ${key.split('_')[1]}`}
              isAnimationActive={false}
            />
          ))}

        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
