"""
Patient Comprehension Analyzer
Ensures discharge instructions are understandable by patients.
Uses reading level analysis and medical jargon detection.
"""

import re
from typing import List, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..config import get_settings

settings = get_settings()


class ComprehensionAnalyzer:
    """Analyzes and improves patient-facing text comprehension."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=1  # Using default temperature
        )
        
        # Common medical jargon patterns
        self.medical_jargon = {
            "anticoagulant": "blood thinner",
            "hypertension": "high blood pressure",
            "myocardial infarction": "heart attack",
            "cerebrovascular accident": "stroke",
            "dyspnea": "shortness of breath",
            "edema": "swelling",
            "tachycardia": "fast heartbeat",
            "bradycardia": "slow heartbeat",
            "prn": "as needed",
            "bid": "twice daily",
            "tid": "three times daily",
            "qid": "four times daily",
            "po": "by mouth",
            "inr": "blood test for blood thinners",
            "eGFR": "kidney function test",
            "hemoglobin": "red blood cell count",
            "creatinine": "kidney function marker",
        }
    
    def detect_jargon(self, text: str) -> List[str]:
        """Detect medical jargon in text."""
        found_jargon = []
        text_lower = text.lower()
        
        for jargon_term in self.medical_jargon.keys():
            if jargon_term in text_lower:
                found_jargon.append(jargon_term)
        
        return found_jargon
    
    def calculate_reading_level(self, text: str) -> Tuple[float, str]:
        """
        Calculate Flesch-Kincaid Grade Level.
        Returns: (grade_level, interpretation)
        """
        # Remove special characters for accurate counting
        clean_text = re.sub(r'[^\w\s\.]', '', text)
        
        sentences = [s.strip() for s in clean_text.split('.') if s.strip()]
        words = clean_text.split()
        
        if not sentences or not words:
            return 0.0, "Unable to calculate"
        
        # Count syllables (simplified approximation)
        syllable_count = sum(self._count_syllables(word) for word in words)
        
        # Flesch-Kincaid Grade Level formula
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllable_count / len(words)
        
        grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        grade_level = max(0, grade_level)  # Ensure non-negative
        
        # Interpretation
        if grade_level <= 6:
            interpretation = "Easy to read"
        elif grade_level <= 8:
            interpretation = "Fairly easy to read"
        elif grade_level <= 10:
            interpretation = "Moderate difficulty"
        elif grade_level <= 12:
            interpretation = "Fairly difficult"
        else:
            interpretation = "Very difficult"
        
        return round(grade_level, 1), interpretation
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count for a word."""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)
    
    def calculate_comprehension_score(self, text: str) -> int:
        """
        Calculate overall comprehension score (0-100).
        Higher is better (more comprehensible).
        """
        grade_level, _ = self.calculate_reading_level(text)
        jargon_count = len(self.detect_jargon(text))
        word_count = len(text.split())
        
        # Base score from reading level (target: Grade 6-8)
        if grade_level <= 8:
            reading_score = 100 - (grade_level * 5)
        else:
            reading_score = max(0, 100 - ((grade_level - 8) * 10))
        
        # Penalty for jargon (each jargon term reduces score)
        jargon_penalty = min(40, jargon_count * 10)
        
        # Penalty for very long text (over 200 words)
        length_penalty = max(0, (word_count - 200) / 10) if word_count > 200 else 0
        
        final_score = max(0, min(100, reading_score - jargon_penalty - length_penalty))
        return int(final_score)
    
    async def simplify_text(self, text: str, target_grade_level: int = 6) -> str:
        """
        Use AI to simplify medical text to target reading level.
        """
        system_prompt = (
            f"You are a medical communication expert. Your job is to rewrite medical instructions "
            f"so they are easy for patients to understand (Grade {target_grade_level} reading level).\\n\\n"
            "RULES:\\n"
            "1. Replace medical jargon with simple terms\\n"
            "2. Use short sentences (10-15 words)\\n"
            "3. Use active voice\\n"
            "4. Maintain medical accuracy\\n"
            "5. Keep the same meaning and all critical information\\n"
            "6. Be warm and reassuring in tone\\n"
        )
        
        human_prompt = f"Simplify this medical text:\\n\\n{text}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content.strip()
    
    async def analyze_and_improve(self, text: str, language: str = "en") -> Dict:
        """
        Complete analysis: detect issues and provide simplified version.
        """
        jargon_detected = self.detect_jargon(text)
        grade_level, interpretation = self.calculate_reading_level(text)
        score = self.calculate_comprehension_score(text)
        
        # Only simplify if score is below 70
        simplified_version = text
        if score < 70:
            simplified_version = await self.simplify_text(text)
        
        return {
            "original_text": text,
            "score": score,
            "reading_level": grade_level,
            "interpretation": interpretation,
            "jargon_detected": jargon_detected,
            "simplified_version": simplified_version,
            "language": language,
            "needs_improvement": score < 70
        }
