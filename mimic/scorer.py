import re

COMPLEXITY_KEYWORDS = {
    "analyze": 2.0, "analyse": 2.0, "compare": 2.5, "contrast": 1.5,
    "design": 2.0, "research": 2.0, "strategy": 2.0, "architecture": 2.0,
    "evaluate": 2.0, "plan": 1.5, "investigate": 2.0, "assess": 1.5,
    "recommend": 1.5, "diagnose": 2.0, "synthesize": 2.5, "explore": 1.0,
    "implement": 1.5, "develop": 1.5, "build": 1.0,
}

SIMPLE_KEYWORDS = {
    "summarize": -1.5, "rewrite": -1.5, "shorten": -1.5,
    "fix grammar": -2.0, "translate": -1.0, "define": -1.0,
    "explain briefly": -2.0, "what is": -0.5, "list": -0.5,
    "paraphrase": -1.5, "simplify": -1.0,
}

PARALLEL_INDICATORS = {
    "vs", "versus", "compare", "contrast", "each", "multiple", "both",
}

DOMAIN_SIGNALS = {
    "medical":    ["health", "medical", "clinical", "patient", "disease", "treatment", "drug", "hospital"],
    "legal":      ["law", "legal", "contract", "compliance", "regulation", "court", "liability", "policy"],
    "technical":  ["code", "software", "api", "database", "architecture", "system", "deploy", "infrastructure"],
    "research":   ["research", "study", "analysis", "survey", "literature", "investigate", "academic"],
    "financial":  ["revenue", "cost", "budget", "invest", "profit", "market", "financial", "startup"],
}


class Scorer:
    def __init__(self):
        self.complexity_threshold = 5

    def score(self, task: str) -> dict:
        text = task.lower()

        complexity = self._base_complexity(text)
        complexity += self._keyword_score(text)
        complexity = round(max(1.0, min(10.0, complexity)), 1)

        parallelizable = self._is_parallelizable(text, complexity)
        fragments = self._suggest_fragments(text, complexity, parallelizable)
        domain = self._detect_domain(text)

        morph_decision = (
            "FRAGMENT"
            if complexity >= self.complexity_threshold and parallelizable
            else "PRIME"
        )

        return {
            "complexity": complexity,
            "domain": domain,
            "parallelizable": parallelizable,
            "suggested_fragments": fragments,
            "morph_decision": morph_decision,
            "reason": self._explain(complexity, parallelizable, morph_decision),
        }

    def _base_complexity(self, text: str) -> float:
        words = len(text.split())
        sentences = max(1, len(re.findall(r'[.?!]', text)))
        word_score = min(3.0, words / 20)
        sentence_score = min(2.0, sentences * 0.4)
        return 1.0 + word_score + sentence_score

    def _keyword_score(self, text: str) -> float:
        score = 0.0
        for kw, weight in COMPLEXITY_KEYWORDS.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                score += weight
        for kw, weight in SIMPLE_KEYWORDS.items():
            if kw in text:
                score += weight
        return score

    def _is_parallelizable(self, text: str, complexity: float) -> bool:
        if complexity < self.complexity_threshold:
            return False
        for indicator in PARALLEL_INDICATORS:
            if re.search(r'\b' + re.escape(indicator) + r'\b', text):
                return True
        # multiple entities joined by "and" (e.g. "A, B, and C")
        if len(re.findall(r'\band\b', text)) >= 2:
            return True
        return False

    def _suggest_fragments(self, text: str, complexity: float, parallelizable: bool) -> int:
        if not parallelizable:
            return 1
        if complexity >= 8:
            return 3
        return 2

    def _detect_domain(self, text: str) -> str:
        for domain, signals in DOMAIN_SIGNALS.items():
            if any(s in text for s in signals):
                return domain
        return "general"

    def _explain(self, complexity: float, parallelizable: bool, decision: str) -> str:
        if decision == "FRAGMENT":
            return f"Complexity {complexity}/10 with parallel workstreams detected — fragmenting."
        return f"Complexity {complexity}/10 — single-pass execution sufficient."
