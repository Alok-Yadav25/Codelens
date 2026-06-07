import os
import re
import requests

# ── Config ────────────────────────────────────────────────────────────────────
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/codebert-base"

SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "go", "ruby", "php", "cpp", "rust", "swift"]

# Regex signatures for fast rule-based language detection
LANGUAGE_SIGNATURES: dict[str, list[str]] = {
    "python":     [r"\bdef \w+\(", r"\bimport \w+", r"\bclass \w+\("],
    "javascript": [r"\bconst \w+", r"=>\s*{", r"\brequire\("],
   "cpp": [
    r"#include\s*<",           
    r"::\w+\(",                
    r"\bstd::",                
    r"\bint\s+main\s*\(",      
    r"\bvector\s*<",          
    r"\bcout\b",                
    r"\bcin\b",                
    r"\bclass\s+\w+\s*\{",     
    r"->",                     
    r"\bnullptr\b",           
    r"\bauto\s+\w+\s*=",       
    r"\bpublic:",              
],
    "java":       [r"\bpublic\s+class\b", r"\bSystem\.out\.", r"@Override", r"HashMap<", r"new int\[\]", r"\bimport java\."],
    "go":         [r"\bfunc \w+\(", r":=", r'\bpackage\s+\w+'],
    "ruby":       [r"\bdef \w+", r"\bend\b", r"\bputs\b"],
    "typescript": [r"\binterface \w+", r":\s*string\b", r":\s*number\b", r"\btype \w+\s*="],
    "rust":       [r"\bfn \w+\(", r"\blet mut\b", r"\bimpl \w+", r"println!"],
    "swift":      [r"\bfunc \w+\(", r"\bvar \w+\s*:", r"\blet \w+\s*:", r"print\("],
    "php":        [r"<\?php", r"\$\w+\s*=", r"\becho\b"],

}


class CodeBERTAnalyzer:
    """
    Calls the HuggingFace Inference API to get CodeBERT embeddings.
    No local model download or PyTorch required.
    """

    def __init__(self):
      
        self.token = os.environ.get("HF_TOKEN")
        if not self.token:
            raise EnvironmentError(
                "HF_TOKEN environment variable is not set.\n"
                "Get a free token at https://huggingface.co/settings/tokens\n"
                "Then run: export HF_TOKEN=hf_your_token_here"
            )
        self.headers = {"Authorization": f"Bearer {self.token}"}
        print("CodeBERTAnalyzer ready — using HuggingFace Inference API")

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, code: str, declared_language: str = "auto") -> dict:
        """
        Detect language and extract semantic features for the given code.

        Returns:
            {
              "language": "python",
              "features": {
                  "cls_embedding": [...],    # 768-dim float list
                  "token_count":   42,
                  "complexity_hint": 0.63,
              }
            }
        """
        # 1. Language detection using regex — no API call needed for this
        if declared_language == "auto":
            language = self._detect_language(code)
        else:
            language = declared_language.lower()

        # 2. Get mean-pooled embedding from HuggingFace API
        cls_embedding = self._get_embedding(code)

        # 3. Build feature dict passed on to the Groq prompt
        features = {
            "cls_embedding":   cls_embedding,
            "token_count":     len(code.split()),
            "complexity_hint": self._complexity_hint(code),
        }

        return {"language": language, "features": features}

    def supported_languages(self) -> list[str]:
        return SUPPORTED_LANGUAGES

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_embedding(self, code: str) -> list[float]:
        """
        Call the HuggingFace feature-extraction API and return a
        mean-pooled 768-dim embedding vector.

        Uses wait_for_model=True so we don't get 503 on cold starts.
        Returns a zero vector as a safe fallback if the API fails.
        """
        truncated = code[:2000] 
        payload = {
            "inputs": truncated,
            "options": {"wait_for_model": True}, 
        }

        try:
            response = requests.post(
                HF_API_URL,
                headers=self.headers,
                json=payload,
                timeout=30,  
            )
        except requests.exceptions.RequestException as e:
            print(f"HuggingFace API request failed: {e}")
            return [0.0] * 768  

        if response.status_code != 200:
            print(f"HuggingFace API warning: {response.status_code} — {response.text[:200]}")
            return [0.0] * 768

        raw = response.json()
        try:
            if isinstance(raw, list) and isinstance(raw[0], list) and isinstance(raw[0][0], list):
                token_vectors = raw[0]   
            elif isinstance(raw, list) and isinstance(raw[0], list):
                token_vectors = raw      
            else:
                return [0.0] * 768       

          
            num_tokens = len(token_vectors)
            pooled = [
                sum(token_vectors[t][d] for t in range(num_tokens)) / num_tokens
                for d in range(len(token_vectors[0]))
            ]
            return pooled
        except (IndexError, TypeError, ZeroDivisionError) as e:
            print(f"Embedding parse error: {e}")
            return [0.0] * 768

    def _detect_language(self, code: str) -> str:
        """Rule-based language detector — counts regex signature matches."""
        scores: dict[str, int] = {lang: 0 for lang in LANGUAGE_SIGNATURES}
        for lang, patterns in LANGUAGE_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, code):
                    scores[lang] += 1
        best_lang  = max(scores, key=scores.get)
        best_score = scores[best_lang]
        return best_lang if best_score > 0 else "unknown"

    def _complexity_hint(self, code: str) -> float:
        """
        Rough complexity proxy: count decision keywords / line count.
        Normalised to [0, 1] — above 0.5 is considered complex.
        """
        decision_keywords = r'\b(if|elif|else|for|while|case|catch|except|switch)\b'
        decisions  = len(re.findall(decision_keywords, code))
        line_count = max(code.count("\n"), 1)
        return min(decisions / line_count, 1.0)
