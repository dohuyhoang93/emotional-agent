"use client";

import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { FileCode, Database } from 'lucide-react';

// Reuse the socket connection or create a new one? 
// Ideally we share context, but for simplicity let's rely on the separate connection 
// or import the socket instance if it was exported. 
// For now, let's create a separate connection or try to import from a common socket file if we had one.
// Since RealtimeChart creates its own socket, we'll create one here too for simplicity.
// In a production app, we should move socket to a Context.

const socket = io('http://localhost:8000', {
  transports: ['websocket'],
  reconnectionAttempts: 5,
});

export default function ExperimentInfo() {
  const [info, setInfo] = useState<{path: string, filename: string, records: number} | null>(null);

  useEffect(() => {
    socket.on('experiment_info', (data) => {
      console.log("Experiment Info:", data);
      setInfo(data);
    });

    return () => {
      socket.off('experiment_info');
    };
  }, []);

  if (!info) return (
      <div className="flex items-center gap-2 text-gray-500 text-sm animate-pulse">
          <Database className="w-4 h-4" />
          <span>Scanning...</span>
      </div>
  );

  return (
    <div className="flex flex-col items-end">
        <div className="flex items-center gap-2 text-blue-300 text-sm bg-blue-900/20 px-3 py-1 rounded-full border border-blue-800/50">
            <FileCode className="w-4 h-4" />
            <span className="font-mono">{info.filename}</span>
        </div>
        <div className="text-gray-600 text-xs mt-1 font-mono hover:text-gray-400 transition-colors" title={info.path}>
            {info.path}
        </div>
    </div>
  );
}
