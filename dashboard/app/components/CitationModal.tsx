"use client";

import { X, ExternalLink, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function CitationModal({ citation, isOpen, onClose }: { citation: any, isOpen: boolean, onClose: () => void }) {
    if (!isOpen || !citation) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                />
                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden"
                >
                    <div className="p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center">
                                    <ShieldCheck size={28} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-slate-900">{citation.source_name}</h3>
                                    <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{citation.section || "Clinical Guideline"}</p>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 text-slate-400 hover:bg-slate-50 rounded-xl">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="bg-slate-50 rounded-2xl p-6 mb-6 border border-slate-100">
                            <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
                                Verified Clinical Snippet
                            </div>
                            <p className="text-slate-700 leading-relaxed italic text-lg">
                                "{citation.snippet || "Full text content from verified medical source."}"
                            </p>
                        </div>

                        <div className="flex gap-3">
                            <button className="flex-1 btn-primary py-3">
                                View Full Protocol <ExternalLink size={16} />
                            </button>
                            <button onClick={onClose} className="px-6 py-3 text-slate-500 font-bold border border-slate-200 rounded-xl hover:bg-slate-50">
                                Close
                            </button>
                        </div>
                    </div>

                    <div className="bg-emerald-600 px-6 py-2 text-[10px] text-white font-bold text-center tracking-widest uppercase">
                        Clinical Safety Verified by Evidence-Based Guidelines
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
