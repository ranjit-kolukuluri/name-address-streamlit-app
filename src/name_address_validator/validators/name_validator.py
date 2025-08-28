# src/name_address_validator/validators/name_validator.py
"""
Complete Working Enhanced Name Validator with US Census data and intelligent suggestions
"""

import re
from typing import Dict, List

class EnhancedNameValidator:
    def __init__(self):
        self.min_length = 1
        self.max_length = 50
        self.valid_chars = re.compile(r"^[a-zA-Z\s\-'\.]+$")
        
        # Comprehensive name databases (from US Census data)
        self.common_first_names = [
            'james', 'robert', 'john', 'michael', 'william', 'david', 'richard', 'joseph',
            'thomas', 'christopher', 'charles', 'daniel', 'matthew', 'anthony', 'mark', 'donald',
            'steven', 'paul', 'andrew', 'joshua', 'kenneth', 'kevin', 'brian', 'george',
            'timothy', 'ronald', 'jason', 'edward', 'jeffrey', 'ryan', 'jacob', 'gary',
            'nicholas', 'eric', 'jonathan', 'stephen', 'larry', 'justin', 'scott', 'brandon',
            'benjamin', 'samuel', 'gregory', 'frank', 'raymond', 'alexander', 'patrick', 'jack',
            'dennis', 'jerry', 'tyler', 'aaron', 'jose', 'henry', 'adam', 'douglas',
            'nathan', 'zachary', 'noah', 'antonio', 'walter', 'carlos', 'wayne', 'juan',
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica',
            'sarah', 'karen', 'nancy', 'lisa', 'betty', 'helen', 'sandra', 'donna',
            'carol', 'ruth', 'sharon', 'michelle', 'laura', 'emily', 'kimberly', 'deborah',
            'dorothy', 'amy', 'angela', 'ashley', 'brenda', 'emma', 'olivia', 'cynthia',
            'marie', 'janet', 'catherine', 'frances', 'christine', 'samantha', 'debra', 'rachel',
            'carolyn', 'virginia', 'maria', 'heather', 'diane', 'julie', 'joyce'
        ]
        
        self.common_last_names = [
            'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis',
            'rodriguez', 'martinez', 'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson',
            'thomas', 'taylor', 'moore', 'jackson', 'martin', 'lee', 'perez', 'thompson',
            'white', 'harris', 'sanchez', 'clark', 'ramirez', 'lewis', 'robinson', 'walker',
            'young', 'allen', 'king', 'wright', 'scott', 'torres', 'nguyen', 'hill',
            'flores', 'green', 'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell',
            'mitchell', 'carter', 'roberts', 'gomez', 'phillips', 'evans', 'turner', 'diaz',
            'parker', 'cruz', 'edwards', 'collins', 'reyes', 'stewart', 'morris', 'morales',
            'murphy', 'cook', 'rogers', 'gutierrez', 'ortiz', 'morgan', 'cooper', 'peterson',
            'bailey', 'reed', 'kelly', 'howard', 'ramos', 'kim', 'cox', 'ward',
            'richardson', 'watson', 'brooks', 'chavez', 'wood', 'james', 'bennett', 'gray',
            'mendoza', 'ruiz', 'hughes', 'price', 'alvarez', 'castillo', 'sanders', 'patel',
            'myers', 'long', 'ross', 'foster', 'jimenez', 'powell', 'jenkins', 'perry',
            'russell', 'sullivan', 'bell', 'coleman', 'butler', 'henderson', 'barnes', 'gonzales',
            'fisher', 'vasquez', 'simmons', 'romero', 'jordan', 'patterson', 'alexander', 'hamilton'
        ]
        
        # Common typo corrections
        self.common_typos = {
            # First name typos
            'jon': 'john', 'jhon': 'john', 'johnn': 'john',
            'mike': 'michael', 'mik': 'michael', 'micheal': 'michael', 'michal': 'michael',
            'rob': 'robert', 'bob': 'robert', 'robrt': 'robert',
            'bill': 'william', 'will': 'william', 'willam': 'william',
            'dave': 'david', 'davd': 'david', 'daivd': 'david',
            'chris': 'christopher', 'cris': 'christopher', 'christofer': 'christopher',
            'matt': 'matthew', 'mathew': 'matthew', 'matth': 'matthew',
            'andy': 'andrew', 'andre': 'andrew', 'andew': 'andrew',
            'steve': 'steven', 'stephan': 'stephen', 'stefen': 'stephen',
            'tom': 'thomas', 'thom': 'thomas', 'tomas': 'thomas',
            
            # Last name typos
            'smyth': 'smith', 'smithe': 'smith', 'smth': 'smith', 'smiht': 'smith',
            'jonson': 'johnson', 'johsnon': 'johnson', 'jonhson': 'johnson',
            'willams': 'williams', 'willaims': 'williams', 'wiliams': 'williams',
            'browne': 'brown', 'braun': 'brown', 'brow': 'brown',
            'davies': 'davis', 'daviss': 'davis', 'devis': 'davis',
            'garsia': 'garcia', 'garciaa': 'garcia',
            'millar': 'miller', 'miler': 'miller', 'miiller': 'miller',
            'andersen': 'anderson', 'andersson': 'anderson'
        }
        
        # Cultural name variations
        self.cultural_variations = {
            'jose': ['josé', 'jose', 'josep'],
            'maria': ['maría', 'maria', 'mary'],
            'carlos': ['carlos', 'karl', 'charles'],
            'juan': ['juan', 'john', 'joão'],
            'antonio': ['antonio', 'anthony', 'antônio']
        }
        
        # Name prefixes and suffixes
        self.prefixes = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'rev', 'fr', 'sr', 'sra'}
        self.suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v', 'phd', 'md', 'esq', 'cpa'}
    
    def clean_name(self, name: str) -> str:
        """Clean and normalize name"""
        if not name:
            return ""
        
        # Remove extra spaces and normalize
        cleaned = re.sub(r'\s+', ' ', name.strip().lower())
        
        # Remove common prefixes/suffixes for validation
        words = cleaned.split()
        filtered_words = []
        
        for word in words:
            if word not in self.prefixes and word not in self.suffixes:
                filtered_words.append(word)
        
        return ' '.join(filtered_words) if filtered_words else cleaned
    
    def find_name_suggestions(self, name: str, name_list: List[str], max_suggestions: int = 5) -> List[Dict]:
        """Find similar names with multiple algorithms"""
        if not name:
            return []
        
        name_clean = self.clean_name(name)
        suggestions = []
        
        # 1. Exact typo corrections (highest priority)
        if name_clean in self.common_typos:
            suggestions.append({
                'suggestion': self.common_typos[name_clean].title(),
                'confidence': 0.98,
                'reason': 'common_typo_correction'
            })
        
        # 2. Cultural variations
        for base_name, variations in self.cultural_variations.items():
            if name_clean in variations and base_name in name_list:
                suggestions.append({
                    'suggestion': base_name.title(),
                    'confidence': 0.95,
                    'reason': 'cultural_variation'
                })
        
        # 3. Simple similarity matching
        for real_name in name_list:
            if real_name == name_clean:
                continue
            
            # Check if starts with same letters
            if len(name_clean) >= 3 and len(real_name) >= 3:
                if name_clean[:3] == real_name[:3]:
                    len_diff = abs(len(name_clean) - len(real_name))
                    confidence = max(0.6, 1.0 - (len_diff * 0.1))
                    suggestions.append({
                        'suggestion': real_name.title(),
                        'confidence': confidence,
                        'reason': 'similar_prefix'
                    })
        
        # Sort by confidence and remove duplicates
        seen = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda x: x['confidence'], reverse=True):
            if suggestion['suggestion'] not in seen:
                seen.add(suggestion['suggestion'])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:max_suggestions]
    
    def get_name_info(self, name: str, name_type: str) -> Dict:
        """Get detailed information about a name"""
        name_clean = self.clean_name(name)
        name_list = self.common_first_names if name_type == 'first' else self.common_last_names
        
        info = {
            'is_common': name_clean in name_list,
            'rank': None,
            'frequency': 'unknown'
        }
        
        if info['is_common']:
            try:
                rank = name_list.index(name_clean) + 1
                info['rank'] = rank
                if rank <= 10:
                    info['frequency'] = 'very_common'
                elif rank <= 50:
                    info['frequency'] = 'common'
                elif rank <= 100:
                    info['frequency'] = 'moderately_common'
                else:
                    info['frequency'] = 'less_common'
            except ValueError:
                pass
        
        return info
    
    def validate(self, first_name: str, last_name: str) -> Dict:
        """Enhanced validation with comprehensive analysis"""
        errors = []
        warnings = []
        suggestions = {}
        analysis = {}
        
        # Clean inputs
        first_clean = first_name.strip() if first_name else ''
        last_clean = last_name.strip() if last_name else ''
        
        # Basic validation
        if not first_clean:
            errors.append("First name is required")
        elif len(first_clean) > self.max_length:
            errors.append(f"First name exceeds {self.max_length} characters")
        elif not self.valid_chars.match(first_clean):
            errors.append("First name contains invalid characters")
        else:
            # Detailed first name analysis
            first_info = self.get_name_info(first_clean, 'first')
            analysis['first_name'] = first_info
            
            if not first_info['is_common']:
                warnings.append(f"'{first_clean.title()}' is not in our database of common first names")
                suggestions['first_name'] = self.find_name_suggestions(first_clean, self.common_first_names)
        
        if not last_clean:
            errors.append("Last name is required")
        elif len(last_clean) > self.max_length:
            errors.append(f"Last name exceeds {self.max_length} characters")
        elif not self.valid_chars.match(last_clean):
            errors.append("Last name contains invalid characters")
        else:
            # Detailed last name analysis
            last_info = self.get_name_info(last_clean, 'last')
            analysis['last_name'] = last_info
            
            if not last_info['is_common']:
                warnings.append(f"'{last_clean.title()}' is not in our database of common last names")
                suggestions['last_name'] = self.find_name_suggestions(last_clean, self.common_last_names)
        
        # Calculate confidence score
        is_valid = len(errors) == 0
        confidence = self._calculate_confidence(first_clean, last_clean, analysis, len(warnings))
        
        return {
            'valid': is_valid,
            'confidence': confidence,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions,
            'analysis': analysis,
            'normalized': {
                'first_name': first_clean.title() if first_clean else '',
                'last_name': last_clean.title() if last_clean else ''
            },
            'metadata': {
                'validation_method': 'enhanced_dictionary',
                'database_size': {
                    'first_names': len(self.common_first_names),
                    'last_names': len(self.common_last_names)
                }
            }
        }
    
    def _calculate_confidence(self, first_name: str, last_name: str, analysis: Dict, warning_count: int) -> float:
        """Calculate detailed confidence score"""
        if not first_name or not last_name:
            return 0.0
        
        base_confidence = 0.95
        
        # Reduce confidence for warnings
        confidence = base_confidence - (warning_count * 0.15)
        
        # Boost confidence for very common names
        first_info = analysis.get('first_name', {})
        last_info = analysis.get('last_name', {})
        
        if first_info.get('frequency') == 'very_common':
            confidence += 0.05
        if last_info.get('frequency') == 'very_common':
            confidence += 0.05
        
        # Reduce confidence for very uncommon combinations
        if (first_info.get('frequency') == 'unknown' and 
            last_info.get('frequency') == 'unknown'):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))