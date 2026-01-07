"use client";

import { useState } from "react";
import { Bot, ThumbsUp, ThumbsDown, Globe, Share2, Printer, Sparkles, Copy, Download, CheckCircle, AlertCircle, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { analyzePatient, generateDischarge, submitFeedback, type AnalysisResponse, type DischargeInstructions } from "../services/api";
import { MOCK_PATIENT } from "./MockData";

export default function AIOutput() {
    const [loading, setLoading] = useState(false);
    const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
    const [discharge, setDischarge] = useState<DischargeInstructions | null>(null);
    const [lang, setLang] = useState("English");
    const [feedback, setFeedback] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const analysisResult = await analyzePatient(MOCK_PATIENT);
            setAnalysis(analysisResult);
            
            const dischargeResult = await generateDischarge(MOCK_PATIENT, analysisResult);
            setDischarge(dischargeResult);
            
        } catch (err: any) {
            setError(err.message || 'Failed to generate analysis');
            console.error('Analysis error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async (value: string) => {
        setFeedback(value);
        try {
            await submitFeedback({
                alert_id: 'analysis-' + Date.now(),
                action: value === 'up' ? 'accepted' : 'rejected',
                clinician_note: value === 'up' ? 'Helpful analysis' : 'Needs improvement'
            });
        } catch (err) {
            console.error('Feedback error:', err);
        }
    };

    const handleCopy = () => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const translations: any = {
        "English": discharge?.patient_facing || "Click 'Analyze Patient' to generate instructions",
        "Spanish": "Continúe monitoreando el INR diariamente. Evite alimentos con alto contenido de vitamina K. Detenga el ibuprofeno de inmediato.",
        "Urdu": "روزانہ INR کی نگرانی جاری رکھیں۔ وٹامن K والی اشیا سے پرہیز کریں۔ آئیبوپروفین فوری طور پر بند کر دیں۔"
    };

    return (
        <div className="flex flex-col h-full gap-6">
            {/* Header with Actions */}
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 pb-4 border-b border-slate-700">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                        <Bot size={28} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Clinical AI Analysis</h1>
                        <p className="text-sm text-slate-400 font-medium">Evidence-Based Safety Assessment</p>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-lg transition-colors" title="Print">
                        <Printer size={20} />
                    </button>
                    <button className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-lg transition-colors" title="Share">
                        <Share2 size={20} />
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="btn-primary px-6 gap-2"
                    >
                        {loading ? (
                            <>
                                <Zap size={18} className="animate-spin" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Sparkles size={18} />
                                Analyze Patient
                            </>
                        )}
                    </button>
                </div>
            </div>

            {error && (
                <div className="p-4 alert-card-critical rounded-xl flex items-start gap-3">
                    <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                    <div>
                        <div className="font-bold">Analysis Error</div>
                        <p className="text-sm mt-1">{error}</p>
                    </div>
                </div>
            )}

            {!analysis && !loading ? (
                <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-slate-800/30 to-slate-700/30 border-2 border-dashed border-slate-600 rounded-3xl">
                    <Zap size={56} className="text-slate-600 mb-4" />
                    <p className="text-slate-300 font-semibold text-lg">Ready for Analysis</p>
                    <p className="text-sm text-slate-400 mt-2">Click "Analyze Patient" to generate safety assessment</p>
                </div>
            ) : loading ? (
                <div className="flex-1 space-y-4 pt-10 px-8">
                    <div className="h-6 bg-gradient-to-r from-slate-700 to-transparent rounded-full animate-pulse w-3/4" />
                    <div className="h-4 bg-gradient-to-r from-slate-700 to-transparent rounded-full animate-pulse w-full" />
                    <div className="h-4 bg-gradient-to-r from-slate-700 to-transparent rounded-full animate-pulse w-5/6" />
                    <div className="h-32 bg-slate-700/30 rounded-2xl animate-pulse mt-8" />
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto clinical-scroll space-y-6 pr-4">
                    {/* Summary Card */}
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-2xl p-6"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-2">
                                <CheckCircle size={20} className="text-blue-400" />
                                <h2 className="text-sm font-bold uppercase tracking-widest text-blue-300">Analysis Summary</h2>
                            </div>
                            <FeedbackLoop onFeedback={handleFeedback} active={feedback} />
                        </div>
                        <p className="text-lg text-slate-100 leading-relaxed font-medium">
                            {analysis?.summary}
                        </p>
                    </motion.div>

                    {/* Risk Stratification */}
                    {analysis?.risk_stratification && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.1 }}
                            className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-2xl p-6"
                        >
                            <h2 className="text-sm font-bold uppercase tracking-widest text-purple-300 mb-4">Risk Stratification</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <RiskMetric label="Overall Risk" value={analysis.risk_stratification.overall_risk} />
                                <RiskMetric label="Risk Score" value={`${analysis.risk_stratification.risk_score}/100`} />
                                <RiskMetric label="Critical" value={analysis.risk_stratification.critical_count} color="red" />
                                <RiskMetric label="High" value={analysis.risk_stratification.high_count} color="orange" />
                            </div>
                            <p className="text-sm text-slate-300 mt-4 p-3 bg-slate-700/30 rounded-lg">
                                <span className="font-semibold text-slate-200">Clinical Reasoning:</span> {analysis.risk_stratification.clinical_reasoning}
                            </p>
                        </motion.div>
                    )}

                    {/* Comprehension Analysis */}
                    {discharge?.comprehension_analysis && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="bg-gradient-to-br from-emerald-900/30 to-emerald-800/20 border border-emerald-700/50 rounded-2xl p-6"
                        >
                            <h2 className="text-sm font-bold uppercase tracking-widest text-emerald-300 mb-4">Patient Comprehension</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                                    <div className="text-3xl font-bold text-emerald-400">{discharge.comprehension_analysis.score}</div>
                                    <div className="text-xs text-slate-400 mt-1">Comprehension Score</div>
                                </div>
                                <div className="bg-slate-700/30 rounded-lg p-4">
                                    <div className="font-semibold text-emerald-400">Reading Level</div>
                                    <div className="text-sm text-slate-300 mt-1">Grade {discharge.comprehension_analysis.reading_level}</div>
                                </div>
                                <div className="bg-slate-700/30 rounded-lg p-4">
                                    <div className="font-semibold text-slate-300">{discharge.comprehension_analysis.interpretation}</div>
                                </div>
                            </div>
                            {discharge.comprehension_analysis.jargon_detected.length > 0 && (
                                <div className="text-xs text-orange-400 mt-3 p-2 bg-orange-900/20 rounded-lg">
                                    ⚠️ Complex terms found: {discharge.comprehension_analysis.jargon_detected.join(', ')}
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Discharge Instructions */}
                    {discharge && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-2xl overflow-hidden"
                        >
                            <div className="bg-slate-700/50 p-4 border-b border-slate-700 flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <Globe size={18} className="text-blue-400" />
                                    <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Patient Instructions</h2>
                                </div>
                                <button 
                                    onClick={handleCopy}
                                    className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-600 rounded-lg transition-colors"
                                >
                                    {copied ? <CheckCircle size={18} className="text-green-400" /> : <Copy size={18} />}
                                </button>
                            </div>
                            
                            <div className="p-6">
                                <div className="flex gap-2 mb-4 flex-wrap">
                                    {["English", "Spanish", "Urdu"].map((l) => (
                                        <button
                                            key={l}
                                            onClick={() => setLang(l)}
                                            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                                                lang === l 
                                                    ? 'bg-blue-600 text-white shadow-lg' 
                                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                            }`}
                                        >
                                            {l}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-slate-200 leading-relaxed text-base">
                                    {translations[lang]}
                                </p>
                            </div>
                        </motion.div>
                    )}
                </div>
            )}
        </div>
    );
}

function RiskMetric({ label, value, color }: { label: string; value: any; color?: string }) {
    const colorClass = {
        red: 'text-red-400 bg-red-900/20',
        orange: 'text-orange-400 bg-orange-900/20',
        default: 'text-blue-400 bg-blue-900/20'
    }[color || 'default'];

    return (
        <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-3 text-center">
            <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
            <div className="text-xs text-slate-400 mt-2 font-semibold">{label}</div>
        </div>
    );
}

function FeedbackLoop({ onFeedback, active }: { onFeedback: (v: string) => void, active: string | null }) {
    return (
        <div className="flex gap-1 bg-slate-700/30 rounded-lg p-1">
            <button
                onClick={() => onFeedback('up')}
                className={`p-2 rounded-md transition-all ${
                    active === 'up' 
                        ? 'bg-green-600 text-green-100 shadow-lg' 
                        : 'text-slate-400 hover:text-green-400 hover:bg-slate-600'
                }`}
                title="Helpful"
            >
                <ThumbsUp size={16} />
            </button>
            <button
                onClick={() => onFeedback('down')}
                className={`p-2 rounded-md transition-all ${
                    active === 'down' 
                        ? 'bg-red-600 text-red-100 shadow-lg' 
                        : 'text-slate-400 hover:text-red-400 hover:bg-slate-600'
                }`}
                title="Needs improvement"
            >
                <ThumbsDown size={16} />
            </button>
        </div>
    );
}
