/**
 * API service for connecting to the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PatientRecord {
  demographics: {
    patient_id: string;
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: string;
    weight_kg?: number;
    height_cm?: number;
  };
  medications: Array<{
    name: string;
    dosage: string;
    frequency: string;
    route?: string;
    indication?: string;
  }>;
  lab_results: Array<{
    test_name: string;
    value: number;
    unit: string;
    reference_range?: string;
  }>;
  clinical_notes: Array<{
    note_id: string;
    author_role: string;
    content: string;
  }>;
  vital_signs?: {
    heart_rate?: number;
    sys_bp?: number;
    dia_bp?: number;
    temperature_c?: number;
    resp_rate?: number;
    sp_o2?: number;
  };
  allergies: string[];
  active_problems: string[];
}

export interface AnalysisResponse {
  summary: string;
  flags: Array<{
    severity: string;
    title: string;
    description: string;
    action_required?: string;
    citations: Array<{
      source_name: string;
      snippet?: string;
    }>;
  }>;
  equity_flags: Array<{
    category: string;
    title: string;
    description: string;
    educational_note: string;
    citations: Array<{
      source_name: string;
    }>;
  }>;
  relevant_protocols: Array<{
    title: string;
    summary: string;
    source: string;
  }>;
  analysis_timestamp: string;
}

export interface DischargeInstructions {
  clinician_facing: string;
  patient_facing: string;
  comprehension_analysis?: {
    score: number;
    reading_level: number;
    interpretation: string;
    jargon_detected: string[];
    simplified_version: string;
    needs_improvement: boolean;
  };
  medication_changes: string[];
  follow_up_required: string;
  safety_netting: string;
}

/**
 * Analyze patient safety
 */
export async function analyzePatient(patient: PatientRecord): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/clinical/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(patient),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Analysis failed');
  }

  return response.json();
}

/**
 * Generate discharge instructions
 */
export async function generateDischarge(
  patient: PatientRecord,
  analysis: AnalysisResponse
): Promise<DischargeInstructions> {
  const response = await fetch(`${API_BASE_URL}/v1/clinical/draft-discharge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ patient, analysis }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Discharge generation failed');
  }

  return response.json();
}

/**
 * Submit clinician feedback
 */
export async function submitFeedback(feedback: {
  alert_id: string;
  action: 'accepted' | 'rejected' | 'modified';
  clinician_note?: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/v1/clinical/feedback/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedback),
  });

  if (!response.ok) {
    throw new Error('Feedback submission failed');
  }
}

/**
 * Check backend health
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}
