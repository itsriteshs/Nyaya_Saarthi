"""Shared language gate for production and experiments; not a fluency assessment."""
import re


def check_language(output, language):
    if output.language != language:
        raise ValueError('OUTPUT_LANGUAGE_CODE_MISMATCH')
    for text in (output.answer, output.explanation):
        devanagari = bool(re.search(r'[\u0900-\u097f]', text))
        roman_hindi = bool(re.search(
            r'\b(?:hai|hain|tha|thi|ka|ki|ke|ko|mein|nahi|nahin|aap|aapko|chahiye|sakta|sakti|liye|bataya|batayi|karein|hoga|hogi)\b',
            text, re.I))
        if language == 'english' and (devanagari or roman_hindi):
            raise ValueError('OUTPUT_LANGUAGE_TEXT_MISMATCH')
        if language == 'hindi' and not devanagari:
            raise ValueError('OUTPUT_LANGUAGE_TEXT_MISMATCH')
        if language == 'hinglish' and (devanagari or not re.search(
                r'\b(?:hai|hain|tha|thi|ka|ki|ke|ko|mein|nahi|nahin|aap|aapko|chahiye|sakta|sakti|liye)\b', text, re.I)):
            raise ValueError('OUTPUT_LANGUAGE_TEXT_MISMATCH')
