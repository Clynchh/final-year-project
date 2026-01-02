import os
import re

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
            return s
        
        def remove_spaces(s):
            return re.sub(r'\s+', '', s)
        
        prev_norm = normalize(prev_line)
        curr_norm = normalize(current_line)
        
        prev_nospace = remove_spaces(prev_norm)
        curr_nospace = remove_spaces(curr_norm)
        
        for overlap_len in range(min(len(prev_nospace), len(curr_nospace)), 5, -1):
            prev_suffix = prev_nospace[-overlap_len:]
            curr_prefix = curr_nospace[:overlap_len]
            
            if _fuzzy_match_string(prev_suffix, curr_prefix):
                found_overlap = True
                
                char_count = 0
                cut_point = 0
                
                while char_count < overlap_len and cut_point < len(current_line):
                    if not current_line[cut_point].isspace():
                        char_count += 1
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
    
    cleaned = re.sub(r'\b[A-Z]{2,}\b', '', cleaned)
    
    cleaned = _remove_single_letters(cleaned)
    
    cleaned = cleaned.lower()
    
    cleaned = _remove_nonsense_words(cleaned)
    
    cleaned = re.sub(r'([.!?])\s*', r'\1\n', cleaned)
    
    cleaned = re.sub(r' +', ' ', cleaned)
    
    cleaned = re.sub(r'\n ', '\n', cleaned)
    
    cleaned = re.sub(r'\n+', '\n', cleaned)
    
    cleaned_lines = cleaned.split('\n')
    cleaned_lines = [line for line in cleaned_lines if not re.match(r'^[.!?,]', line.strip())]
    cleaned = '\n'.join(cleaned_lines)
    
    cleaned = cleaned.strip()
    
    return cleaned


def _remove_single_letters(text):
    apostrophes = "'''"
    result = []
    i = 0
    while i < len(text):
        if text[i].isalpha() and text[i].lower() not in ('a', 'i'):
            before_ok = (i == 0) or (not text[i-1].isalpha() and text[i-1] not in apostrophes)
            after_ok = (i == len(text) - 1) or (not text[i+1].isalpha() and text[i+1] not in apostrophes)
            
            if before_ok and after_ok:
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


def _fuzzy_match_string(s1, s2, threshold=0.85):
    if s1 == s2:
        return True
    
    if len(s1) == 0 or len(s2) == 0:
        return False
    
    lcs_len = _lcs_length(s1, s2)
    max_len = max(len(s1), len(s2))
    
    return lcs_len / max_len >= threshold


def _lcs_length(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]


RAW_BASE = "Raw Data/BBC News TV"
CLEAN_BASE = "Clean Data/BBC News TV"

for year_dir in os.listdir(RAW_BASE):
    raw_year_path = os.path.join(RAW_BASE, year_dir)
    
    if not os.path.isdir(raw_year_path):
        continue
    
    clean_year_path = os.path.join(CLEAN_BASE, year_dir)
    os.makedirs(clean_year_path, exist_ok=True)
    
    for filename in os.listdir(raw_year_path):
        if not filename.lower().endswith(".txt"):
            continue
        
        raw_file_path = os.path.join(raw_year_path, filename)
        clean_file_path = os.path.join(clean_year_path, filename)
        
        with open(raw_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        cleaned_text = clean_transcript(raw_text)
        
        with open(clean_file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        
        print(f"Cleaned: {raw_file_path} -> {clean_file_path}")