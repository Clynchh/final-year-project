import re
from pathlib import Path

def clean_transcript(text):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    if not lines:
        return ""
    
    if lines:
        lines = lines[:-1]
    
    if not lines:
        return ""
    
    lines = _filter_corrupted_lines(lines)
    
    if not lines:
        return ""
    
    result = [lines[0]]
    
    for i in range(1, len(lines)):
        current_line = lines[i]
        prev_line = result[-1]
        
        best_overlap_end = 0
        found_overlap = False
        
        def normalize(s):
            s = s.lower().replace('—', '-').replace('–', '-')
            s = s.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
            return s
        
        def remove_spaces(s):
            return re.sub(r'\s+', '', s)
        
        prev_norm = normalize(prev_line)
        curr_norm = normalize(current_line)
        
        prev_nospace = remove_spaces(prev_norm)
        curr_nospace = remove_spaces(curr_norm)
        
        for overlap_len in range(min(len(prev_nospace), len(curr_nospace)), 10, -1):
            prev_suffix = prev_nospace[-overlap_len:]
            curr_prefix = curr_nospace[:overlap_len]
            
            if prev_suffix == curr_prefix:
                found_overlap = True
                
                char_count = 0
                cut_point = 0
                curr_norm_lower = normalize(current_line)
                
                while char_count < overlap_len and cut_point < len(current_line):
                    if not current_line[cut_point].isspace():
                        char_count += 1
                    cut_point += 1
                
                while cut_point < len(current_line) and not current_line[cut_point].isspace():
                    cut_point += 1
                
                best_overlap_end = cut_point
                break
        
        if found_overlap:
            new_content = current_line[best_overlap_end:].strip()
            if new_content:
                result[-1] = result[-1] + ' ' + new_content
        else:
            if not _is_substring_of(current_line, prev_line):
                result.append(current_line)
    
    cleaned = ' '.join(result)
    
    cleaned = re.sub(r'[(\[{|)\]}#]', '', cleaned)
    
    cleaned = re.sub(r'\.{2,}', '', cleaned)
    
    cleaned = re.sub(r"\b[A-Z]{2,}(?:['''][a-zA-Z]+)?\b", '', cleaned)
    
    cleaned = _normalize_apostrophes(cleaned)
    
    cleaned = _remove_single_letters(cleaned)
    
    cleaned = cleaned.lower()
    
    cleaned = _remove_nonsense_words(cleaned)
    
    cleaned = re.sub(r"[''']s\b", '', cleaned)
    
    cleaned = re.sub(r"^[''']s\s*", '', cleaned)
    
    cleaned = re.sub(r'([.!?])\s*', r'\1\n', cleaned)
    
    cleaned = re.sub(r' +', ' ', cleaned)
    
    cleaned = re.sub(r'\n ', '\n', cleaned)
    
    cleaned = re.sub(r'\n+', '\n', cleaned)
    
    cleaned_lines = cleaned.split('\n')
    cleaned_lines = [line for line in cleaned_lines if not re.match(r'^[.!?,]', line.strip())]
    cleaned = '\n'.join(cleaned_lines)
    
    cleaned = cleaned.strip()
    
    return cleaned


def _normalize_apostrophes(text):
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace('—', '-').replace('–', '-')
    return text


def _remove_single_letters(text):
    apostrophes = "'''"
    result = []
    i = 0
    while i < len(text):
        if text[i].isalpha() and text[i].lower() not in ('a', 'i'):
            before_char = text[i-1] if i > 0 else ' '
            after_char = text[i+1] if i < len(text) - 1 else ' '
            
            before_is_space = before_char.isspace()
            after_is_space = after_char.isspace()
            before_is_apostrophe = before_char in apostrophes
            after_is_apostrophe = after_char in apostrophes
            before_is_letter = before_char.isalpha()
            after_is_letter = after_char.isalpha()
            
            is_standalone = before_is_space and after_is_space
            
            if is_standalone and not before_is_apostrophe and not after_is_apostrophe:
                i += 1
                continue
        
        result.append(text[i])
        i += 1
    
    return ''.join(result)


def _filter_corrupted_lines(lines):
    filtered = []
    
    for i, line in enumerate(lines):
        if re.search(r'[A-Z][a-z]?\s*$', line) and len(line.split()) > 2:
            continue
        
        if re.search(r'[A-Z]\s*[)}\]]\s*$', line):
            continue
        
        if re.search(r'\s[A-Z]{1,2}\s*$', line) and not re.search(r'\s(I|A|UK|US|EU|UN)\s*$', line):
            continue
        
        filtered.append(line)
    
    return filtered


def _is_substring_of(shorter, longer):
    def normalize(s):
        return re.sub(r'\s+', '', s.lower())
    
    short_norm = normalize(shorter)
    long_norm = normalize(longer)
    
    return short_norm in long_norm


def _remove_nonsense_words(text):
    common_short_words = {
        'a', 'i', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in',
        'is', 'it', 'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us',
        'we', 'am', 'oh', 'ok', 'hi', 'ha', 'ah', 'uh', 'um', 'hm', 'ay', 'oi',
        'ox', 'ex', 'ax', 'id', 'ad', 're'
    }
    
    def is_valid_word(word):
        if any(c in word for c in "'''"):
            return True
        
        if not word.isalpha():
            return True
        
        if len(word) <= 2:
            return word.lower() in common_short_words
        
        vowels = set('aeiou')
        has_vowel = any(c in vowels for c in word.lower())
        
        if not has_vowel and len(word) > 1:
            return False
        
        consonants = set('bcdfghjklmnpqrstvwxyz')
        max_consonants = 0
        current_consonants = 0
        for c in word.lower():
            if c in consonants:
                current_consonants += 1
                max_consonants = max(max_consonants, current_consonants)
            else:
                current_consonants = 0
        
        if max_consonants > 4:
            return False
        
        return True
    
    words = text.split()
    filtered_words = [word for word in words if is_valid_word(word)]
    
    return ' '.join(filtered_words)


if __name__ == "__main__":
    _CURRENT = Path(__file__).resolve()
    PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

    RAW_BASE = PROJECT_ROOT / "data" / "raw"
    CLEAN_BASE = PROJECT_ROOT / "data" / "clean"

    for raw_file_path in sorted(RAW_BASE.rglob("*.txt")):
        rel_path = raw_file_path.relative_to(RAW_BASE)
        clean_file_path = CLEAN_BASE / rel_path
        clean_file_path.parent.mkdir(parents=True, exist_ok=True)

        raw_text = raw_file_path.read_text(encoding="utf-8")
        cleaned_text = clean_transcript(raw_text)
        clean_file_path.write_text(cleaned_text, encoding="utf-8")

        print(f"Cleaned: {rel_path}")