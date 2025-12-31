import RealtimeChart from "./components/RealtimeChart";
import SuccessChart from "./components/SuccessChart";
import NeuralMonitor from "./components/NeuralMonitor";
import ExperimentInfo from "./components/ExperimentInfo";
import { Activity, Brain, Trophy } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white p-8 font-mono">
      <header className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div className="flex items-center gap-4">
          <Activity className="w-8 h-8 text-green-500" />
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
              Theus SNN Dashboard
            </h1>
            <p className="text-gray-400 text-sm">Real-time Neural Monitoring & Orchestration</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="px-4 py-2 bg-gray-900 rounded-lg border border-gray-700 flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-bold">ONLINE</span>
          </div>
          <ExperimentInfo />
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Row 1: Main Rewards */}
        <div className="col-span-2">
          <RealtimeChart />
        </div>

        {/* Row 2: Success Rate & Neural Stats */}
        <div className="col-span-2 grid grid-cols-1 xl:grid-cols-2 gap-8">
          <SuccessChart />
          <NeuralMonitor />
        </div>

        {/* Status Panels (Placeholder data for now) */}
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 lg:col-span-2">
          <h3 className="text-lg font-bold text-gray-400 mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5" /> Experiment Configuration
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="p-3 bg-gray-950 rounded border border-gray-800">
              <span className="text-gray-500 block">Orchestrator Mode</span>
              <span className="text-green-300 font-bold">Flux (Hybrid)</span>
            </div>
            <div className="p-3 bg-gray-950 rounded border border-gray-800">
              <span className="text-gray-500 block">Neural Architecture</span>
              <span className="text-blue-300 font-bold">LIF + STDP + RL</span>
            </div>
            <div className="p-3 bg-gray-950 rounded border border-gray-800">
              <span className="text-gray-500 block">Agent Count</span>
              <span className="text-purple-300 font-bold">5 Agents</span>
            </div>
            <div className="p-3 bg-gray-950 rounded border border-gray-800">
              <span className="text-gray-500 block">Max Episodes</span>
              <span className="text-yellow-300 font-bold">1000</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
