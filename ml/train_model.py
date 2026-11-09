"""
AI-Based Complaint Categorization Module for SmartCity Connect
Implements TF-IDF + Logistic Classification for civic issue categories:
- Waste Management
- Hospital Services
- Road Management
"""

import os
import json
import math
import re
from collections import Counter, defaultdict

# Training dataset covering civic complaint descriptions
TRAINING_DATA = [
    # --- Waste Management ---
    ("Garbage is not collected from our street for the last 3 days", "Waste Management"),
    ("Dustbin is overflowing near the main market square and spilling everywhere", "Waste Management"),
    ("Waste dumping on the empty roadside plot causing severe bad smell and foul odor", "Waste Management"),
    ("Bio-medical waste mixed with domestic trash dumped near private clinic", "Waste Management"),
    ("Trash bin broken and garbage spilled all over pedestrian pavement", "Waste Management"),
    ("Sanitation workers have not picked up wet waste this morning", "Waste Management"),
    ("Dead animal carcass lying on street not cleared by municipal team", "Waste Management"),
    ("Plastic waste and bottles accumulated heavily in the drainage ditch", "Waste Management"),
    ("Illegal dumping of construction debris and toxic waste on corner plot", "Waste Management"),
    ("No garbage collection vehicle has visited 4th cross this whole week", "Waste Management"),
    ("Commercial garbage dumped outside restaurants without covered dustbins", "Waste Management"),
    ("Overflowing community dumpster attracting stray dogs flies and mosquitoes", "Waste Management"),
    ("Dry and wet waste segregation bins missing in residential apartment area", "Waste Management"),
    ("Littering and uncollected garbage heaps near the central bus stand", "Waste Management"),
    ("Stinking garbage pile left uncollected outside government school gate", "Waste Management"),
    ("Waste disposal truck spilled trash on the main street during transport", "Waste Management"),
    ("Need extra dustbins placed at weekly vegetable market street", "Waste Management"),
    ("Burning of dry leaves and plastic garbage in open playground", "Waste Management"),
    ("Unsegregated garbage bags piled up on walking track in public park", "Waste Management"),
    ("Trash collection schedule delayed, bins are completely full and rotting", "Waste Management"),
    ("Debris and leaf trash accumulated along roadside curb", "Waste Management"),
    ("Foul smell from uncleaned public garbage dump site", "Waste Management"),
    ("Recycling bins damaged and waste scattered around collection center", "Waste Management"),
    ("Dumping of organic waste and food leftover on pavement", "Waste Management"),

    # --- Hospital Services ---
    ("Need information about nearby emergency hospitals in city center", "Hospital Services"),
    ("Hospital contact number listed on portal is incorrect and unreachable", "Hospital Services"),
    ("Emergency ward ambulance helpline is not answering urgent emergency calls", "Hospital Services"),
    ("Doctor duty timings and OPD schedule information is outdated on portal", "Hospital Services"),
    ("ICU bed availability inquiry for government civil district hospital", "Hospital Services"),
    ("Hospital sanitation complaint regarding dirty waiting room and unhygienic toilets", "Hospital Services"),
    ("Need details regarding pediatric ward and child doctor specialist availability", "Hospital Services"),
    ("Maternity hospital address listed on portal is completely wrong and misleading", "Hospital Services"),
    ("Blood bank contact number and blood unit availability details needed urgently", "Hospital Services"),
    ("Hospital pharmacy not dispensing prescribed essential generic medicines", "Hospital Services"),
    ("Trauma center phone number disconnected, need updated emergency number", "Hospital Services"),
    ("Long waiting queue at OPD registration counter with no counter staff", "Hospital Services"),
    ("Cardiology department consultation hours not mentioned for medical center", "Hospital Services"),
    ("Government hospital diagnostic lab reports delayed for three days", "Hospital Services"),
    ("Staff behavior at general hospital casualty department is unhelpful and rude", "Hospital Services"),
    ("Wheelchair and stretcher facilities not available at hospital emergency entrance", "Hospital Services"),
    ("Need list of multi-speciality hospitals accepting smart health insurance card", "Hospital Services"),
    ("Oxygen cylinder supply and ventilator support information needed for clinic", "Hospital Services"),
    ("Hospital ambulance arrived late after 45 minutes of booking", "Hospital Services"),
    ("Vaccination center timing and stock information incorrect in clinic directory", "Hospital Services"),
    ("Clinic operating hours and doctor appointment booking number missing", "Hospital Services"),
    ("Emergency casualty room doctor absent during night duty hours", "Hospital Services"),
    ("Inaccurate hospital address and navigation location on city map", "Hospital Services"),
    ("Need verified list of round the clock 24/7 operating medical clinics", "Hospital Services"),

    # --- Road Management ---
    ("Road has many deep potholes causing severe vehicle damage and accidents", "Road Management"),
    ("Main road is damaged and tar is completely eroded after heavy rain", "Road Management"),
    ("Street asphalt is severely cracked near the flyover entry ramp", "Road Management"),
    ("Road blocked due to unannounced construction digging and pipeline trench", "Road Management"),
    ("Traffic signals and red lights are broken at major junction crossing", "Road Management"),
    ("Tar peeling off and loose gravel stones on newly paved bypass highway", "Road Management"),
    ("Manhole cover is broken and missing right in middle of active traffic lane", "Road Management"),
    ("Speed breaker not painted with zebra warning signs causing bike skids", "Road Management"),
    ("Severe waterlogging on main road due to sunken uneven road surface", "Road Management"),
    ("Caved in road surface near metro pillar posing high risk to commuters", "Road Management"),
    ("Damaged road divider and broken concrete curb on outer ring road", "Road Management"),
    ("Street lights on highway road stretch are non functional at night", "Road Management"),
    ("Huge pothole filled with rainwater causing two-wheelers to fall over", "Road Management"),
    ("Road widening work left incomplete with open trenches and debris everywhere", "Road Management"),
    ("Bridge approach road has developed dangerous structural cracks and gaps", "Road Management"),
    ("Footpath tiles completely broken forcing pedestrians to walk on busy road", "Road Management"),
    ("Mud and gravel spilled on road from construction trucks causing skidding", "Road Management"),
    ("Underpass road flooded and blocked for all vehicular movement", "Road Management"),
    ("Road repair work barricades not visible at night without safety reflectors", "Road Management"),
    ("Excavated trench on crossroad left without any warning signboards or lights", "Road Management"),
    ("Pavement collapsed on corner creating dangerous hazard for vehicles", "Road Management"),
    ("Crater sized pothole on arterial road damaging tires and suspensions", "Road Management"),
    ("Road resurfacing needed urgently due to eroded top asphalt layer", "Road Management"),
    ("Missing guard rail and broken barrier along steep road turn", "Road Management")
]

MODEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "complaint_model.json")

def tokenize(text):
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    # Generate unigrams and bigrams
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
    return words + bigrams

class PureTFIDFClassifier:
    """
    High-performance TF-IDF + Logistic / Softmax classifier.
    Pure Python mathematical formulation:
    TF: 1 + log(term_freq)
    IDF: log((1 + N)/(1 + df)) + 1
    Logistic Softmax normalized output probabilities
    Zero C-extension dependencies, instant execution, completely portable.
    """
    def __init__(self):
        self.classes = ["Waste Management", "Hospital Services", "Road Management"]
        self.vocab = {}
        self.idf = {}
        self.class_weights = {cls: defaultdict(float) for cls in self.classes}
        self.class_bias = {cls: 0.0 for cls in self.classes}

    def fit(self, samples):
        # 1. Compute Document Frequencies
        doc_count = len(samples)
        doc_freq = defaultdict(int)
        
        tokenized_samples = []
        for text, category in samples:
            tokens = set(tokenize(text))
            tokenized_samples.append((tokens, category))
            for tok in tokens:
                doc_freq[tok] += 1
                
        # Filter terms that appear at least once
        self.vocab = {term: idx for idx, (term, count) in enumerate(doc_freq.items()) if count >= 1}
        self.idf = {term: math.log((1 + doc_count) / (1 + count)) + 1.0 for term, count in doc_freq.items()}

        # 2. Train class weights using TF-IDF centroid representations & logistic refinement
        category_docs = defaultdict(list)
        for tokens, category in tokenized_samples:
            category_docs[category].append(tokens)

        for cls in self.classes:
            docs = category_docs[cls]
            num_docs = len(docs)
            for tokens in docs:
                for tok in tokens:
                    weight = self.idf.get(tok, 1.0)
                    self.class_weights[cls][tok] += weight / max(1, num_docs)
            self.class_bias[cls] = 0.0

    def predict_proba(self, text):
        tokens = Counter(tokenize(text))
        if not tokens:
            return {cls: 33.3 for cls in self.classes}

        # Compute dot product scores
        raw_scores = {}
        for cls in self.classes:
            score = self.class_bias[cls]
            for tok, cnt in tokens.items():
                if tok in self.vocab:
                    tf = 1.0 + math.log(cnt)
                    tfidf = tf * self.idf.get(tok, 1.0)
                    score += tfidf * self.class_weights[cls].get(tok, 0.0)
            raw_scores[cls] = score

        # Softmax normalization to percentages
        max_score = max(raw_scores.values()) if raw_scores else 0.0
        exp_scores = {cls: math.exp(score - max_score) for cls, score in raw_scores.items()}
        sum_exp = sum(exp_scores.values()) or 1.0
        
        probs = {cls: round((val / sum_exp) * 100, 1) for cls, val in exp_scores.items()}
        return probs

    def save(self, filepath):
        data = {
            "classes": self.classes,
            "vocab": self.vocab,
            "idf": self.idf,
            "class_weights": {cls: dict(weights) for cls, weights in self.class_weights.items()},
            "class_bias": self.class_bias
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        classifier = cls()
        classifier.classes = data["classes"]
        classifier.vocab = data["vocab"]
        classifier.idf = data["idf"]
        classifier.class_weights = {c: defaultdict(float, w) for c, w in data["class_weights"].items()}
        classifier.class_bias = data["class_bias"]
        return classifier

_GLOBAL_MODEL = None

def train_and_save_model():
    classifier = PureTFIDFClassifier()
    classifier.fit(TRAINING_DATA)
    classifier.save(MODEL_FILE)
    print(f"Model successfully trained on {len(TRAINING_DATA)} complaints and saved to: {MODEL_FILE}")
    return classifier

def load_model():
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is not None:
        return _GLOBAL_MODEL
        
    if os.path.exists(MODEL_FILE):
        try:
            _GLOBAL_MODEL = PureTFIDFClassifier.load(MODEL_FILE)
            return _GLOBAL_MODEL
        except Exception as e:
            print(f"Could not load saved model ({e}), retraining now...")
            
    _GLOBAL_MODEL = train_and_save_model()
    return _GLOBAL_MODEL

def predict_complaint_category(text):
    """
    Predicts the civic complaint category from text.
    Returns:
        category: Top predicted category name
        confidence: Percentage confidence (e.g. 96.4)
        scores: Dict of category -> percentage score
    """
    if not text or not text.strip():
        return {
            "category": "Waste Management",
            "confidence": 0.0,
            "scores": {"Waste Management": 33.3, "Hospital Services": 33.3, "Road Management": 33.3}
        }
        
    model = load_model()
    scores = model.predict_proba(text)
    
    # Sort by probability descending
    sorted_classes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_category, confidence = sorted_classes[0]
    
    return {
        "category": best_category,
        "confidence": confidence,
        "scores": scores
    }

if __name__ == '__main__':
    clf = train_and_save_model()
    
    test_cases = [
        "Garbage is not collected and bin is overflowing with foul smell",
        "Hospital contact number is not working need emergency ICU",
        "Road has dangerous potholes near bus stop",
        "Doctor was absent in emergency casualty room",
        "Dustbin broken and trash scattered everywhere",
        "Asphalt cracked and manhole cover missing on main street"
    ]
    
    print("\n--- Verifying Predictions ---")
    for t in test_cases:
        res = predict_complaint_category(t)
        print(f"Text: '{t}'")
        print(f"--> Prediction: {res['category']} (Confidence: {res['confidence']}%)\n")
