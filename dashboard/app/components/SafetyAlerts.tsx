"use client";

import { AlertCircle, AlertTriangle, CheckCircle2, ChevronRight, Shield, Zap, TrendingUp } from "lucide-react";
import { MOCK_ANALYSIS } from "./MockData";
import { motion, AnimatePresence } from "framer-motion";

export default function SafetyAlerts({ onCitationClick }: { onCitationClick: (citation: any) => void }) {
    const { flags } = MOCK_ANALYSIS;
    const criticalCount = flags.filter(f => f.severity === "Red").length;
    const warningCount = flags.filter(f => f.severity === "Yellow").length;

    return (
        <div className="flex flex-col h-full gap-4">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h3 className="section-title">
                    <Shield size={20} className="text-red-400" />
                    Clinical Safety Alerts
                </h3>
                <div className="badge-critical">
                    {flags.length} Issues
                </div>
            </div>

            {/* Alert Summary */}
            <div className="grid grid-cols-3 gap-2">
                <AlertStatCard count={criticalCount} label="Critical" color="red" />
                <AlertStatCard count={warningCount} label="High Risk" color="orange" />
                <AlertStatCard count={flags.filter(f => f.severity === "Green").length} label="Passed" color="green" />
            </div>

            {/* Alert List */}
            <div className="flex flex-col gap-3 overflow-y-auto clinical-scroll pr-1 flex-1">
                <AnimatePresence>
                    {flags.map((flag, i) => (
                        <motion.div
                            key={i}
                            initial={{ x: 20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: i * 0.08 }}
                            className={`rounded-xl border-l-4 p-4 transition-all hover:shadow-lg ${
                                flag.severity === "Red"
                                    ? "alert-card-critical border-l-red-600"
                                    : flag.severity === "Yellow"
                                    ? "alert-card-moderate border-l-yellow-600"
                                    : "bg-green-900/20 border-l-green-600 text-green-200"
                            }`}
                        >
                            <div className="flex gap-3">
                                <div className="shrink-0 mt-0.5">
                                    {flag.severity === "Red" && <AlertCircle size={20} className="text-red-500" />}
                                    {flag.severity === "Yellow" && <AlertTriangle size={20} className="text-yellow-500" />}
                                    {flag.severity === "Green" && <CheckCircle2 size={20} className="text-green-500" />}
                                </div>
                                <div className="flex flex-col gap-2 flex-1">
                                    <h4 className="font-semibold text-sm leading-tight">{flag.title}</h4>
                                    <p className="text-xs opacity-90 leading-relaxed">{flag.description}</p>

                                    {flag.action_required && (
                                        <div className="mt-2 p-2.5 bg-slate-900/40 rounded-lg text-xs font-semibold border border-slate-700">
                                            <span className="font-bold">Action Required:</span> {flag.action_required}
                                        </div>
                                    )}

                                    <div className="mt-2 flex flex-wrap gap-2">
                                        {flag.citations.map((cite, j) => (
                                            <button
                                                key={j}
                                                onClick={() => onCitationClick(cite)}
                                                className="text-[10px] font-bold px-2 py-1 rounded-full bg-slate-700/40 hover:bg-slate-600 transition-all flex items-center gap-1"
                                            >
                                                📚 {cite.source_name.split(" ")[0]} <ChevronRight size={12} />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* System Status Card */}
            <div className="glass-card p-4 rounded-2xl border-2 border-emerald-700/30 bg-emerald-900/10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Zap size={16} className="text-emerald-400 animate-pulse" />
                        <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">System Status</span>
                    </div>
                    <div className="text-xs font-semibold text-emerald-300">Connected</div>
                </div>
                <div className="text-xs text-slate-400 mt-2">
                    Last scan: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            </div>
        </div>
    );
}

function AlertStatCard({ count, label, color }: { count: number; label: string; color: 'red' | 'orange' | 'green' }) {
    const colorMap = {
        red: 'bg-red-900/20 border-red-700 text-red-400',
        orange: 'bg-orange-900/20 border-orange-700 text-orange-400',
        green: 'bg-green-900/20 border-green-700 text-green-400'
    };

    return (
        <div className={`${colorMap[color]} border rounded-lg p-3 text-center`}>
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-xs font-semibold mt-1 opacity-80">{label}</div>
        </div>
    );
}
