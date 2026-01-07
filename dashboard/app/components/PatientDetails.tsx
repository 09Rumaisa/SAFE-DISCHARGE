"use client";

import { useState } from "react";
import { Activity, Beaker, ClipboardList, Pill, Plus, Trash2 } from "lucide-react";
import { MOCK_PATIENT } from "./MockData";

export default function PatientDetails() {
    const { demographics, medications, lab_results, vital_signs, clinical_notes } = MOCK_PATIENT;
    const [editMode, setEditMode] = useState(false);

    return (
        <div className="flex flex-col h-full gap-4 overflow-y-auto clinical-scroll pr-2">
            {/* Patient Overview Card */}
            <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="section-title">
                        <Activity size={20} className="text-blue-400" />
                        Patient Overview
                    </h3>
                    <button 
                        onClick={() => setEditMode(!editMode)}
                        className="text-xs px-3 py-1 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition"
                    >
                        {editMode ? "Done" : "Edit"}
                    </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="section-subtitle block mb-1">Full Name</label>
                        <div className="text-white font-semibold">{demographics.first_name} {demographics.last_name}</div>
                    </div>
                    <div>
                        <label className="section-subtitle block mb-1">Medical Record #</label>
                        <div className="text-white font-mono font-semibold">{demographics.patient_id}</div>
                    </div>
                    <div>
                        <label className="section-subtitle block mb-1">Date of Birth</label>
                        <div className="text-white font-semibold">{demographics.date_of_birth}</div>
                    </div>
                    <div>
                        <label className="section-subtitle block mb-1">Status</label>
                        <div className="inline-flex items-center gap-2">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                            <span className="text-emerald-400 font-semibold">Stable</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Vital Signs */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="section-title mb-4">
                    <Activity size={20} className="text-rose-400" />
                    Vital Signs
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <VitalStatCard 
                        label="Heart Rate" 
                        value={vital_signs.heart_rate} 
                        unit="bpm" 
                        alert={vital_signs.heart_rate > 100}
                        normal="60-100"
                    />
                    <VitalStatCard 
                        label="Blood Pressure" 
                        value={`${vital_signs.sys_bp}/72`} 
                        unit="mmHg" 
                        alert={vital_signs.sys_bp < 90}
                        normal="90-120/60-80"
                    />
                    <VitalStatCard 
                        label="Temperature" 
                        value={vital_signs.temperature_c} 
                        unit="°C" 
                        alert={vital_signs.temperature_c > 38}
                        normal="36.5-37.5"
                    />
                    <VitalStatCard 
                        label="Oxygen Saturation" 
                        value={vital_signs.sp_o2} 
                        unit="%" 
                        alert={vital_signs.sp_o2 < 92}
                        normal="94-100"
                    />
                </div>
            </div>

            {/* Current Medications */}
            <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="section-title">
                        <Pill size={20} className="text-indigo-400" />
                        Current Medications
                    </h3>
                    <button className="p-2 hover:bg-slate-700 rounded-lg transition" title="Add medication">
                        <Plus size={18} className="text-blue-400" />
                    </button>
                </div>
                <div className="space-y-2">
                    {medications.map((med, i) => (
                        <div key={i} className="glass-card-sm p-3 rounded-lg flex items-start justify-between">
                            <div>
                                <div className="font-semibold text-white text-sm">{med.name}</div>
                                <div className="text-xs text-slate-400 mt-1">{med.dosage} • {med.frequency}</div>
                            </div>
                            <button className="text-slate-400 hover:text-red-400 transition p-1">
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Laboratory Results */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="section-title mb-4">
                    <Beaker size={20} className="text-emerald-400" />
                    Laboratory Results
                </h3>
                <div className="space-y-2">
                    {lab_results.map((lab, i) => (
                        <div key={i} className="flex items-center justify-between p-3 glass-card-sm rounded-lg">
                            <div>
                                <div className="text-sm font-semibold text-white">{lab.test_name}</div>
                                <div className="text-xs text-slate-400">Reference: {lab.reference_range}</div>
                            </div>
                            <div className={`text-lg font-bold font-mono ${
                                lab.value > 3.0 ? 'text-red-400' : 'text-green-400'
                            }`}>
                                {lab.value}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Clinical Notes */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="section-title mb-4">
                    <ClipboardList size={20} className="text-amber-400" />
                    Clinical Notes
                </h3>
                <div className="bg-slate-700/30 p-4 rounded-lg border border-slate-600">
                    <p className="text-slate-300 text-sm leading-relaxed">
                        "{clinical_notes[0].content}"
                    </p>
                    <div className="text-xs text-slate-500 mt-3">
                        Last updated: {new Date().toLocaleTimeString()}
                    </div>
                </div>
            </div>
        </div>
    );
}

function VitalStatCard({ 
    label, 
    value, 
    unit, 
    alert, 
    normal 
}: { 
    label: string
    value: any
    unit: string
    alert?: boolean
    normal?: string
}) {
    return (
        <div className={`glass-card-sm p-4 rounded-lg border-2 transition ${
            alert 
                ? 'border-red-600/50 bg-red-900/10' 
                : 'border-green-600/30 bg-green-900/5'
        }`}>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{label}</div>
            <div className="flex items-baseline justify-between">
                <span className={`text-2xl font-bold ${
                    alert ? 'text-red-400' : 'text-green-400'
                }`}>
                    {value}
                </span>
                <span className="text-xs text-slate-400 ml-2">{unit}</span>
            </div>
            <div className="text-xs text-slate-500 mt-2">Normal: {normal}</div>
        </div>
    );
}
