# SAFE-DISCHARGE AI

An Explainable AI Safety Copilot for High-Risk Hospital Discharge Decisions.

SAFE-DISCHARGE AI assists clinicians during one of the highest-risk moments in patient care — hospital discharge. It summarizes patient data, flags safety risks with explainable citations, generates patient-friendly multilingual discharge instructions, and learns from clinician feedback to reduce alert fatigue over time.

---

## The Problem

Hospital discharge is error-prone and cognitively demanding:

- Clinicians spend excessive time on documentation
- Drug interaction checks are manual and inconsistent
- Patients frequently misunderstand discharge instructions
- Language barriers worsen outcomes
- Existing tools lack transparency and equity awareness

---

## What It Does

The system acts as a second pair of eyes — it does not replace clinicians, it supports safer decisions.

**AI Patient Summary Generator**
Summarizes diagnosis, medications, allergies, labs, and follow-up requirements in a structured format, reducing documentation time.

**Explainable Safety Risk Alerts (RAG-based)**
Flags drug-drug interactions, missed follow-ups, and abnormal labs. Every alert includes a reason, a clinical guideline citation, and a confidence level — so clinicians understand why something was flagged, not just what was flagged.

**Patient Comprehension Scoring**
Detects medical jargon, measures reading level, and rewrites instructions to Grade 6-8 readability. Example: "Obtain INR in 5-7 days" becomes "Get a blood test next week to make sure your blood thinner dose is safe."

**Bias and Equity Safety Checks**
Flags known diagnostic biases using clinical guidelines — such as atypical heart attack symptoms in women or kidney function interpretation in elderly patients. Increases clinician awareness without enforcement.

**Near-Miss Learning System**
Learns from ignored alerts, edited AI suggestions, and clinician feedback to improve relevance and reduce alert fatigue over time.

**Multilingual Output**
Supports English, Urdu, Hindi, and Spanish for patient-facing instructions, improving understanding across diverse populations.

---

## MVP Focus

High-risk discharge for patients on multiple medications — anticoagulants (Warfarin, DOACs), elderly patients with polypharmacy, and patients discharged with antibiotics alongside chronic conditions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI reasoning & summarization | Azure OpenAI |
| Guideline retrieval (RAG) | Azure Cognitive Search |
| Multilingual support | Azure Translator |
| Backend orchestration | Azure App Service / Azure Functions |
| Secrets management | Azure Key Vault |
| Monitoring & logs | Azure Application Insights |
| Database | SQLite |
| Backend | Python, FastAPI |
| Frontend | JavaScript (dashboard) |

---

## Project Structure

```
SAFE-DISCHARGE/
├── backend/                  # FastAPI backend and AI pipeline
├── dashboard/                # Frontend dashboard (JavaScript)
├── SAFE-DISCHARGE-AI.txt     # Full system design document
├── SAFE-DISCHARGE-AI.docx    # System design (Word format)
├── Warfarin-2306-PIL.pdf     # Clinical reference — Warfarin guidelines
├── oral-anticoagulant-warfarin-and-noacs-.pdf  # Clinical reference — NOACs
├── requirements.txt
└── db.sqlite3
```

---

## Key Design Principles

- AI never makes final decisions — clinicians remain in control
- All alerts are citation-grounded, no hallucination
- Clear uncertainty signaling on every output
- Secure, de-identified data handling
- Bias-aware prompts and inclusive design
- Enterprise-ready deployment on Azure

---

## Ethical Considerations

- Transparent explanations on every AI decision
- Escalation suggestions instead of prescriptions
- Equity checks to flag systemic bias in clinical guidelines
- Designed for inclusivity across languages and literacy levels

---

## Author

Rumaisa Siddiqa
GitHub: https://github.com/09Rumaisa
LinkedIn: https://linkedin.com/in/rumaisa-siddiqa
