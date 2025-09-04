import pandas as pd
import numpy as np
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import re
import nltk

class ShadowTraceNLP:
    def __init__(self):
        # Multi-model approach for better accuracy
        try:
            self.threat_classifier = pipeline("text-classification", 
                                             model="martin-ha/toxic-comment-model")
        except:
            # Fallback if model doesn't work
            self.threat_classifier = None
            
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis")
        except:
            self.sentiment_analyzer = None
        
        # Custom threat detection
        self.threat_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.threat_model = LogisticRegression()
        
        # Misinformation detection keywords
        self.misinfo_keywords = [
            'fake news', 'conspiracy', 'hoax', 'lies', 'false information',
            'deepfake', 'manipulated', 'doctored', 'fabricated'
        ]
        
        # Threat categories
        self.threat_types = {
            'death_threat': ['kill', 'murder', 'die', 'death', 'eliminate', 'destroy'],
            'harassment': ['hate', 'stupid', 'ugly', 'worthless', 'pathetic', 'loser'],
            'impersonation': ['official', 'real', 'authentic', 'verified', 'fake account'],
            'doxxing': ['address', 'phone', 'location', 'home', 'family', 'find you']
        }
        
        # Train with sample data
        self._train_basic_model()
    
    def _train_basic_model(self):
        """Train basic model with sample threat data"""
        training_data = []
        
        # Death threats
        death_threats = [
            "I will kill you if I see you",
            "You deserve to die for what you did", 
            "Someone should eliminate this person",
            "I hope you get murdered"
        ]
        
        # Harassment
        harassment = [
            "You are so ugly and stupid",
            "Nobody likes you, you're worthless", 
            "You should be ashamed of yourself",
            "What a pathetic excuse for a human"
        ]
        
        # Normal content
        normal = [
            "Great performance last night!",
            "Love your new song",
            "Thanks for the inspiration", 
            "Amazing concert, can't wait for the next one",
            "Beautiful photos from your vacation",
            "Congratulations on your success"
        ]
        
        # Build training set
        texts = death_threats + harassment + normal
        labels = [1] * len(death_threats) + [1] * len(harassment) + [0] * len(normal)
        
        try:
            X = self.threat_vectorizer.fit_transform(texts)
            self.threat_model.fit(X, labels)
        except:
            pass
    
    def preprocess_instagram_text(self, text):
        """Enhanced preprocessing for Instagram content"""
        # Handle Instagram-specific elements
        text = re.sub(r'@[\w.]+', '[USER]', text)  # Replace mentions
        text = re.sub(r'#\w+', '[HASHTAG]', text)  # Replace hashtags
        text = re.sub(r'http\S+|www\S+', '[URL]', text)  # Replace URLs
        text = re.sub(r'[^\w\s\[\]]', ' ', text)  # Keep only words and our tokens
        
        return text.lower().strip()
    
    def detect_threat_type(self, text):
        """Classify specific threat types"""
        text_lower = text.lower()
        detected_types = []
        
        for threat_type, keywords in self.threat_types.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_types.append(threat_type)
        
        return detected_types if detected_types else ['general_threat']
    
    def analyze_content(self, text):
        """Comprehensive content analysis"""
        processed_text = self.preprocess_instagram_text(text)
        
        # Multiple detection layers
        results = {
            'original_text': text,
            'processed_text': processed_text,
            'threat_score': 0.0,
            'is_threat': False,
            'threat_types': [],
            'confidence': 0.0,
            'evidence': []
        }
        
        # 1. Toxic content detection (if available)
        if self.threat_classifier:
            try:
                toxic_result = self.threat_classifier(processed_text)[0]
                if toxic_result['label'] == 'TOXIC':
                    results['threat_score'] += toxic_result['score'] * 0.4
                    results['evidence'].append(f"Toxic content detected: {toxic_result['score']:.3f}")
            except:
                pass
        
        # 2. Sentiment analysis (if available)
        if self.sentiment_analyzer:
            try:
                sentiment = self.sentiment_analyzer(processed_text)[0]
                if sentiment['label'] == 'NEGATIVE' and sentiment['score'] > 0.8:
                    results['threat_score'] += 0.3
                    results['evidence'].append(f"Highly negative sentiment: {sentiment['score']:.3f}")
            except:
                pass
        
        # 3. Keyword-based detection
        threat_keywords_found = 0
        for threat_type, keywords in self.threat_types.items():
            found_keywords = [kw for kw in keywords if kw in processed_text]
            if found_keywords:
                threat_keywords_found += len(found_keywords)
                results['threat_types'].extend([threat_type] * len(found_keywords))
                results['evidence'].append(f"{threat_type}: {', '.join(found_keywords)}")
        
        if threat_keywords_found > 0:
            results['threat_score'] += min(threat_keywords_found * 0.15, 0.5)
        
        # 4. Custom ML model prediction
        try:
            X = self.threat_vectorizer.transform([processed_text])
            ml_prob = self.threat_model.predict_proba(X)[0][1]
            results['threat_score'] += ml_prob * 0.3
            results['evidence'].append(f"ML model score: {ml_prob:.3f}")
        except:
            pass
        
        # 5. Misinformation detection
        misinfo_score = sum(1 for keyword in self.misinfo_keywords 
                           if keyword in processed_text.lower())
        if misinfo_score > 0:
            results['threat_score'] += min(misinfo_score * 0.05, 0.2)
            results['evidence'].append(f"Misinformation indicators: {misinfo_score}")
        
        # Final assessment
        results['threat_score'] = min(results['threat_score'], 1.0)
        results['is_threat'] = results['threat_score'] > 0.6
        results['confidence'] = results['threat_score']
        results['threat_types'] = list(set(results['threat_types']))
        
        if not results['threat_types']:
            results['threat_types'] = ['low_risk'] if results['threat_score'] < 0.3 else ['general_threat']
        
        return results

# Quick test
if __name__ == "__main__":
    nlp = ShadowTraceNLP()
    
    test_texts = [
        "I will kill this celebrity if I ever see them",
        "Great performance last night! Loved it",
        "This celebrity is spreading fake news",
        "You are so ugly and worthless"
    ]
    
    for text in test_texts:
        result = nlp.analyze_content(text)
        print(f"Text: {text}")
        print(f"Threat: {result['is_threat']}, Score: {result['threat_score']:.3f}")
        print(f"Types: {result['threat_types']}")
        print("-" * 50)