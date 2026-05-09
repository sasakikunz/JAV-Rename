import difflib
import re


class FuzzyMatcher:
    def __init__(self, movie_list=None, threshold=0.7):
        self.movie_list = movie_list if movie_list else []
        self.threshold = threshold
    
    def load_movie_list(self, movie_list):
        self.movie_list = movie_list
    
    def _clean_string(self, s):
        s = s.upper()
        s = re.sub(r'[^A-Z0-9]', '', s)
        return s
    
    def _clean_movie_name(self, s):
        match = re.search(r'\[([^\]]+)\]', s)
        if match:
            s = match.group(1)
        s = s.upper()
        s = re.sub(r'[^A-Z0-9]', '', s)
        return s
    
    def calculate_similarity(self, str1, str2):
        str1_clean = self._clean_string(str1)
        str2_clean = self._clean_movie_name(str2)
        
        if not str1_clean or not str2_clean:
            return 0.0
        
        similarity = difflib.SequenceMatcher(None, str1_clean, str2_clean).ratio()
        return similarity
    
    def match(self, normalized_name, threshold=None):
        if threshold is None:
            threshold = self.threshold
        
        if not normalized_name:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for movie in self.movie_list:
            score = self.calculate_similarity(normalized_name, movie)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = movie
        
        return best_match, best_score
    
    def batch_match(self, normalized_names, threshold=None):
        results = []
        for name in normalized_names:
            match, score = self.match(name, threshold)
            results.append({
                'input': name,
                'match': match,
                'score': score
            })
        return results