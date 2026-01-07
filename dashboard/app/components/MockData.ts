export const MOCK_PATIENT = {
  demographics: {
    first_name: "John",
    last_name: "Doe",
    patient_id: "MRN-123456",
    date_of_birth: "1975-05-15",
    gender: "Male",
    weight_kg: 82.5
  },
  medications: [
    { name: "Warfarin", dosage: "5mg", frequency: "Once daily", indication: "Atrial Fibrillation" },
    { name: "Ibuprofen", dosage: "400mg", frequency: "As needed", indication: "Pain" }
  ],
  lab_results: [
    { test_name: "INR", value: 3.8, unit: "ratio", reference_range: "2.0-3.0" },
    { test_name: "Creatinine", value: 1.1, unit: "mg/dL", reference_range: "0.7-1.3" }
  ],
  vital_signs: {
    heart_rate: 105,
    sys_bp: 105,
    dia_bp: 70,
    temperature_c: 38.2,
    resp_rate: 22,
    sp_o2: 94
  },
  clinical_notes: [
    { note_id: "N1", author_role: "ED Physician", content: "Patient reports recent calf pain and increased shortness of breath. History of AFib on Warfarin. Current INR elevated." }
  ],
  allergies: ["Penicillin"],
  active_problems: ["Atrial Fibrillation", "Hypertension"]
};

export const MOCK_ANALYSIS = {
  summary: "Patient presents with elevated INR (3.8) and is currently taking Ibuprofen, which significantly increases bleeding risk. NEWS2 score indicates moderate clinical warning. Potential Sepsis/Infection markers present.",
  flags: [
    {
      severity: "Red",
      title: "High Bleeding Risk",
      description: "INR is 3.8 (Target 2.0-3.0). Interaction between Warfarin and Ibuprofen increases hemorrhage risk.",
      action_required: "Discontinue Ibuprofen immediately. Consider Vitamin K if bleeding occurs.",
      citations: [{ source_name: "NICE KTT21", section: "Warfarin Interaction", snippet: "Significant interactions include NSAIDs (e.g., Ibuprofen) which raise hemorrhage risk." }]
    },
    {
      severity: "Yellow",
      title: "Moderate Clinical Warning",
      description: "Elevated Heart Rate (105) and Resp Rate (22). NEWS2 score signals potential decompensation.",
      action_required: "Frequent vital signs monitoring every 4 hours.",
      citations: [{ source_name: "NICE NG51", section: "Sepsis Risk", snippet: "Heart Rate > 100bpm and Resp Rate > 20/min are markers for clinical review." }]
    }
  ],
  relevant_protocols: [
    { title: "Warfarin Management", summary: "Target INR for AF is 2.5. INR > 3.0 increases major bleeding risk.", source: "NICE KTT21" },
    { title: "Sepsis Early Warning", summary: "Early identification using NEWS2 is critical for patient safety.", source: "NICE NG51" }
  ]
};
