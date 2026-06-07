import os
import json
from groq import Groq


SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of
software security, best practices, and common bug patterns.

When you receive a code snippet you MUST respond with ONLY a valid JSON object
— no markdown, no commentary outside the JSON — in exactly this shape:

{
  "bugs": [
    {"line": 12, "description": "division by zero possible if b is 0"}
  ],
  "security_issues": ["<description>", ...],
  "improvements":    ["<description>", ...],
  "fixes": [
    {"original": "return a / b", "suggested": "return a / b if b != 0 else None"}
  ],
  "performance_scores": {
    "before": {
      "readability":     <0-100>,
      "security":        <0-100>,
      "performance":     <0-100>,
      "maintainability": <0-100>,
      "best_practices":  <0-100>
    },
    "after": {
      "readability":     <0-100>,
      "security":        <0-100>,
      "performance":     <0-100>,
      "maintainability": <0-100>,
      "best_practices":  <0-100>
    }
  },
  "severity": "low" | "medium" | "high",
  "summary":  "<one paragraph>"
}

Rules:
- bugs is a list of objects with line (integer) and description (string).
- fixes is a list of objects with original and suggested strings.
- security_issues and improvements are plain string lists.
- performance_scores.before reflects the submitted code as-is.
- performance_scores.after reflects the code IF all improvements were applied.
- Scores are integers 0-100. Realistic scoring — perfect code is around 85.
- severity reflects the worst issue found.
- summary is 2-3 sentences for the developer.
- If a list has no items, return an empty array [].
"""

USER_PROMPT_TEMPLATE = """Language: {language}
Complexity hint (0-1, higher = more complex): {complexity_hint:.2f}
Token count: {token_count}

Code to review:
```
{code}
```

Review the code and return the JSON object described in the system prompt."""


class GroqReviewer:
    """Sends code to the Groq API and parses the structured JSON review."""

    def __init__(self, model: str = "llama-3.1-8b-instant"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set.\n"
                "Get a free key at https://console.groq.com"
            )
        self.client = Groq(api_key=api_key)
        self.model  = model

    def review(self, code: str, language: str, features: dict) -> dict:
        """Request a code review from the LLM."""
        user_message = USER_PROMPT_TEMPLATE.format(
            language        = language,
            complexity_hint = features.get("complexity_hint", 0.0),
            token_count     = features.get("token_count", 0),
            code            = code,
        )
        response = self.client.chat.completions.create(
            model       = self.model,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature = 0.2,
            max_tokens  = 1500,
        )
        raw_text = response.choices[0].message.content.strip()
        return self._parse_review(raw_text)

    def _parse_review(self, raw_text: str) -> dict:
        """Parse LLM response. FIX: includes performance_scores in return."""
        cleaned = raw_text
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "bugs":               [],
                "security_issues":    [],
                "improvements":       [],
                "fixes":              [],
                "performance_scores": {},
                "severity":           "low",
                "summary":            f"Could not parse LLM response — try again. Raw: {raw_text[:300]}",
            }

        # Normalise bugs — handle dict and plain string formats
        bugs = []
        for bug in data.get("bugs", []):
            if isinstance(bug, dict):
                bugs.append({"line": bug.get("line", "?"), "description": bug.get("description", str(bug))})
            else:
                bugs.append({"line": "?", "description": str(bug)})

        # Normalise fixes
        fixes = []
        for fix in data.get("fixes", []):
            if isinstance(fix, dict):
                fixes.append({"original": fix.get("original", ""), "suggested": fix.get("suggested", "")})

        # FIX: performance_scores now included — was missing in your version
        return {
            "bugs":               bugs,
            "security_issues":    data.get("security_issues",    []),
            "improvements":       data.get("improvements",       []),
            "fixes":              fixes,
            "performance_scores": data.get("performance_scores", {}),
            "severity":           data.get("severity",           "low"),
            "summary":            data.get("summary",            ""),
        }
