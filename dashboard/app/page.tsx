'use client';

import { useState } from 'react';
import { analyzePatient, generateDischarge, submitFeedback } from './services/api';

export default function SafeDischarge() {
  const [step, setStep] = useState<'form' | 'review' | 'results'>('form');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [discharge, setDischarge] = useState<any>(null);
  const [patientData, setPatientData] = useState<any>(null);
  const [clinicianNotes, setClinicianNotes] = useState('');
  const [feedback, setFeedback] = useState<'accepted' | 'rejected' | 'modified'>('accepted');
  
  const [form, setForm] = useState({
    name: 'Sarah Johnson',
    age: '48',
    gender: 'Male',
    hr: '105',
    bp: '118/76',
    temp: '38.2',
    rr: '22',
    o2: '96',
    history: 'Atrial Fibrillation, Hypertension',
    meds: [{ name: 'Warfarin', dose: '5mg', freq: 'daily' }],
    labs: [{ name: 'INR', value: '3.8', ref: '2.0-3.0' }],
    complaint: 'Shortness of breath, calf pain',
    notes: 'Patient reports recent calf pain and shortness of breath'
  });

  const analyze = async () => {
    setLoading(true);
    try {
      // Parse blood pressure
      const bpParts = form.bp.split('/');
      const sys_bp = bpParts[0] ? parseInt(bpParts[0]) : undefined;
      const dia_bp = bpParts[1] ? parseInt(bpParts[1]) : undefined;

      const data = {
        demographics: {
          patient_id: `MRN-${Date.now()}`,
          first_name: form.name.split(' ')[0] || 'John',
          last_name: form.name.split(' ').slice(1).join(' ') || 'Doe',
          date_of_birth: new Date(new Date().getFullYear() - parseInt(form.age), 0, 1).toISOString().split('T')[0],
          gender: form.gender,
          weight_kg: null,
          height_cm: null
        },
        vital_signs: {
          heart_rate: form.hr ? parseInt(form.hr) : undefined,
          sys_bp: sys_bp,
          dia_bp: dia_bp,
          temperature_c: form.temp ? parseFloat(form.temp) : undefined,
          resp_rate: form.rr ? parseInt(form.rr) : undefined,
          sp_o2: form.o2 ? parseInt(form.o2) : undefined
        },
        medications: form.meds.filter(m => m.name).map(m => ({
          name: m.name,
          dosage: m.dose,
          frequency: m.freq,
          route: 'Oral',
          indication: null
        })),
        lab_results: form.labs.filter(l => l.name).map(l => ({
          test_name: l.name,
          value: parseFloat(l.value) || 0,
          unit: '',
          reference_range: l.ref
        })),
        clinical_notes: [{
          note_id: `NOTE-${Date.now()}`,
          author_role: 'Physician',
          content: `Chief Complaint: ${form.complaint}\n\nClinical Notes: ${form.notes}\n\nMedical History: ${form.history}`
        }],
        allergies: [],
        active_problems: form.history ? form.history.split(',').map(h => h.trim()) : []
      };
      
      const analysisResult = await analyzePatient(data);
      setAnalysis(analysisResult);
      setPatientData(data);
      
      // Move to review step instead of directly generating discharge
      setStep('review');
    } catch (err) {
      console.error(err);
      alert('Analysis failed! ' + (err as Error).message);
    }
    setLoading(false);
  };

  const submitApproval = async () => {
    setLoading(true);
    try {
      // Submit feedback to backend
      await submitFeedback({
        alert_id: analysis.risk_stratification.overall_risk,
        action: feedback,
        clinician_note: clinicianNotes
      });

      // Only after feedback is submitted, generate discharge instructions
      const dischargeResult = await generateDischarge(patientData, analysis);
      setDischarge(dischargeResult);
      
      setStep('results');
    } catch (err) {
      console.error(err);
      alert('Failed to submit approval! ' + (err as Error).message);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <header className="bg-slate-900/50 backdrop-blur border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">SafeDischarge AI</h1>
              <p className="text-sm text-blue-300">Clinical Safety Copilot</p>
            </div>
          </div>
          <div className="px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-full flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-300">Ready</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {step === 'form' ? (
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-white mb-6">Patient Assessment</h2>
            <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-2">Age</label>
                  <input value={form.age} onChange={e => setForm({...form, age: e.target.value})} className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white" />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-2">Gender</label>
                  <select value={form.gender} onChange={e => setForm({...form, gender: e.target.value})} className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white">
                    <option>Male</option>
                    <option>Female</option>
                  </select>
                </div>
              </div>

              {/* Vital Signs Section */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  Vital Signs
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Heart Rate (bpm)</label>
                    <input value={form.hr} onChange={e => setForm({...form, hr: e.target.value})} placeholder="105" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Blood Pressure (mmHg)</label>
                    <input value={form.bp} onChange={e => setForm({...form, bp: e.target.value})} placeholder="118/76" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Temperature (°C)</label>
                    <input value={form.temp} onChange={e => setForm({...form, temp: e.target.value})} placeholder="38.2" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Respiratory Rate (breaths/min)</label>
                    <input value={form.rr} onChange={e => setForm({...form, rr: e.target.value})} placeholder="22" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-slate-300 mb-2">Oxygen Saturation (%)</label>
                    <input value={form.o2} onChange={e => setForm({...form, o2: e.target.value})} placeholder="96" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                </div>
              </div>

              {/* Medical History Section */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Medical History
                </h3>
                <textarea value={form.history} onChange={e => setForm({...form, history: e.target.value})} placeholder="e.g., Atrial Fibrillation, Hypertension, Diabetes (comma-separated)" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white h-24 focus:outline-none focus:border-blue-500" />
              </div>

              {/* Medications Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                    Current Medications
                  </h3>
                  <button
                    onClick={() => setForm({...form, meds: [...form.meds, { name: '', dose: '', freq: '' }]})}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors font-medium"
                  >
                    + Add Medication
                  </button>
                </div>
                <div className="space-y-3">
                  {form.meds.map((med, idx) => (
                    <div key={idx} className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Medication Name</label>
                        <input
                          value={med.name}
                          onChange={e => {
                            const newMeds = [...form.meds];
                            newMeds[idx].name = e.target.value;
                            setForm({...form, meds: newMeds});
                          }}
                          placeholder="e.g., Warfarin"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Dose</label>
                        <input
                          value={med.dose}
                          onChange={e => {
                            const newMeds = [...form.meds];
                            newMeds[idx].dose = e.target.value;
                            setForm({...form, meds: newMeds});
                          }}
                          placeholder="e.g., 5mg"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Frequency</label>
                        <input
                          value={med.freq}
                          onChange={e => {
                            const newMeds = [...form.meds];
                            newMeds[idx].freq = e.target.value;
                            setForm({...form, meds: newMeds});
                          }}
                          placeholder="e.g., daily"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Laboratory Results Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                    Laboratory Results
                  </h3>
                  <button
                    onClick={() => setForm({...form, labs: [...form.labs, { name: '', value: '', ref: '' }]})}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors font-medium"
                  >
                    + Add Lab Result
                  </button>
                </div>
                <div className="space-y-3">
                  {form.labs.map((lab, idx) => (
                    <div key={idx} className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Test Name</label>
                        <input
                          value={lab.name}
                          onChange={e => {
                            const newLabs = [...form.labs];
                            newLabs[idx].name = e.target.value;
                            setForm({...form, labs: newLabs});
                          }}
                          placeholder="e.g., INR"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Value</label>
                        <input
                          value={lab.value}
                          onChange={e => {
                            const newLabs = [...form.labs];
                            newLabs[idx].value = e.target.value;
                            setForm({...form, labs: newLabs});
                          }}
                          placeholder="e.g., 3.8"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Reference Range</label>
                        <input
                          value={lab.ref}
                          onChange={e => {
                            const newLabs = [...form.labs];
                            newLabs[idx].ref = e.target.value;
                            setForm({...form, labs: newLabs});
                          }}
                          placeholder="e.g., 2.0-3.0"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Clinical Assessment Section */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Clinical Assessment
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Chief Complaint</label>
                    <input value={form.complaint} onChange={e => setForm({...form, complaint: e.target.value})} placeholder="e.g., Shortness of breath, calf pain" className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Clinical Notes</label>
                    <textarea value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Detailed clinical observations and patient history..." className="w-full px-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-white h-32 focus:outline-none focus:border-blue-500" />
                  </div>
                </div>
              </div>

              <button onClick={analyze} disabled={loading} className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-3 disabled:opacity-50">
                {loading ? 'Analyzing...' : 'Analyze Patient'}
              </button>
            </div>
          </div>
        ) : step === 'review' ? (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-3xl font-bold text-white">Clinician Review</h2>
              <button onClick={() => setStep('form')} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">Back to Form</button>
            </div>

            <div className="max-w-4xl mx-auto">
              <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-8 space-y-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-4">Clinical Analysis</h3>
                  {analysis && (
                    <div className="space-y-4">
                      <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
                        <p className="text-red-300 font-semibold text-lg">{analysis.risk_stratification.overall_risk} Risk</p>
                        <p className="text-slate-300 text-sm mt-2">{analysis.summary}</p>
                      </div>
                      <div className="space-y-3">
                        <h4 className="text-white font-semibold">Safety Flags:</h4>
                        {analysis.flags.map((f: any, i: number) => (
                          <div key={i} className="border-l-4 border-red-500 bg-red-500/10 p-4 rounded">
                            <p className="font-semibold text-white">{f.title}</p>
                            <p className="text-slate-300 text-sm mt-1">{f.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="border-t border-slate-600 pt-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Clinician Review & Approval</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-3">Your Decision:</label>
                      <div className="flex gap-4">
                        <button
                          onClick={() => setFeedback('accepted')}
                          className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                            feedback === 'accepted'
                              ? 'bg-green-600 text-white'
                              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                          }`}
                        >
                          ✓ Approve Analysis
                        </button>
                        <button
                          onClick={() => setFeedback('modified')}
                          className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                            feedback === 'modified'
                              ? 'bg-yellow-600 text-white'
                              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                          }`}
                        >
                          ✎ Approve with Notes
                        </button>
                        <button
                          onClick={() => setFeedback('rejected')}
                          className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                            feedback === 'rejected'
                              ? 'bg-red-600 text-white'
                              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                          }`}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">Clinician Notes (Optional)</label>
                      <textarea
                        value={clinicianNotes}
                        onChange={e => setClinicianNotes(e.target.value)}
                        placeholder="Add any additional observations, modifications, or reasoning for your decision..."
                        className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white h-24 focus:outline-none focus:border-blue-500"
                      />
                    </div>

                    <button
                      onClick={submitApproval}
                      disabled={loading}
                      className="w-full px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-700 hover:to-emerald-600 text-white font-semibold rounded-lg transition-all disabled:opacity-50"
                    >
                      {loading ? 'Submitting...' : 'Submit Review & Generate Patient Summary'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-3xl font-bold text-white">Analysis Results</h2>
              <button onClick={() => {setStep('form'); setAnalysis(null); setDischarge(null); setClinicianNotes('');}} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">New Assessment</button>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-xl font-bold text-white mb-4">Clinical Analysis (Approved)</h3>
                {analysis && (
                  <div className="space-y-4">
                    <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4">
                      <p className="text-green-300 font-semibold">✓ Approved</p>
                      <p className="text-slate-300 text-xs mt-1">Decision: {feedback}</p>
                    </div>
                    <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
                      <p className="text-red-300 font-semibold">{analysis.risk_stratification.overall_risk} Risk</p>
                    </div>
                    <p className="text-slate-300 text-sm">{analysis.summary}</p>
                    {analysis.flags.map((f: any, i: number) => (
                      <div key={i} className="border-l-4 border-red-500 bg-red-500/10 p-3 rounded">
                        <p className="font-semibold text-white text-sm">{f.title}</p>
                        <p className="text-slate-300 text-xs mt-1">{f.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-xl font-bold text-white mb-4">Patient Discharge Instructions</h3>
                {discharge && (
                  <div className="space-y-4">
                    <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                      <p className="text-slate-200 text-sm">{discharge.patient_facing}</p>
                    </div>
                    <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                      <h4 className="text-sm font-semibold text-red-300 mb-2">Emergency Care</h4>
                      <p className="text-slate-200 text-sm">{discharge.safety_netting}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
