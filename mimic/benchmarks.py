import time
from dataclasses import dataclass, field


@dataclass
class CallRecord:
    label: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cache_created: int = 0
    cache_read: int = 0

    @property
    def total_tokens(self):
        return self.input_tokens + self.output_tokens


class RunBenchmark:
    def __init__(self, run_id: str, task: str):
        self.run_id = run_id
        self.task = task
        self.calls: list[CallRecord] = []
        self.complexity: float = 0.0
        self.execution_mode: str = ""
        self.fragment_count: int = 0
        self._run_start = time.time()

    def set_score(self, score: dict):
        self.complexity = score["complexity"]
        self.execution_mode = score["morph_decision"]
        self.fragment_count = score["suggested_fragments"] if score["morph_decision"] == "FRAGMENT" else 0

    def record(self, label: str, input_tokens: int, output_tokens: int, latency_ms: float,
               cache_created: int = 0, cache_read: int = 0):
        self.calls.append(CallRecord(label, input_tokens, output_tokens, latency_ms, cache_created, cache_read))

    @property
    def total_tokens(self):
        return sum(c.total_tokens for c in self.calls)

    @property
    def total_input_tokens(self):
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self):
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_latency_ms(self):
        return (time.time() - self._run_start) * 1000

    @property
    def model_calls(self):
        return len(self.calls)

    @property
    def total_cache_created(self):
        return sum(c.cache_created for c in self.calls)

    @property
    def total_cache_read(self):
        return sum(c.cache_read for c in self.calls)

    def render(self):
        w = 50
        lines = []

        def row(left, right=""):
            content = f"  {left:<28}{right:>16}" if right else f"  {left}"
            lines.append(f"║{content:<{w}}║")

        def divider():
            lines.append(f"╠{'═' * w}╣")

        lines.append(f"╔{'═' * w}╗")
        lines.append(f"║{'  MIMIC BENCHMARK — run ' + self.run_id:<{w}}║")
        divider()
        row(f"Task Complexity:", f"{self.complexity}/10")
        row(f"Execution Mode:", self.execution_mode)
        if self.fragment_count:
            row(f"Fragments Spawned:", str(self.fragment_count))
        divider()
        row(f"Model Calls:", str(self.model_calls))
        row(f"Total Tokens:", f"{self.total_tokens:,}")
        row(f"  └─ Input:", f"{self.total_input_tokens:,}")
        row(f"  └─ Output:", f"{self.total_output_tokens:,}")
        if self.total_cache_created or self.total_cache_read:
            row(f"  └─ Cache Created:", f"{self.total_cache_created:,}")
            row(f"  └─ Cache Read:", f"{self.total_cache_read:,}")
            saved = self.total_cache_read
            row(f"  └─ Tokens Saved:", f"~{saved:,}")
        row(f"Total Latency:", f"{self.total_latency_ms:,.0f}ms")
        divider()
        row("EXECUTION TREE")
        for i, call in enumerate(self.calls):
            is_last = i == len(self.calls) - 1
            prefix = "└──" if is_last else "├──"
            row(f"{prefix} {call.label}", f"{call.latency_ms:,.0f}ms  {call.total_tokens} tok")
        lines.append(f"╚{'═' * w}╝")

        return "\n".join(lines)

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "complexity": self.complexity,
            "execution_mode": self.execution_mode,
            "fragment_count": self.fragment_count,
            "model_calls": self.model_calls,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_created": self.total_cache_created,
            "total_cache_read": self.total_cache_read,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "calls": [
                {
                    "label": c.label,
                    "input_tokens": c.input_tokens,
                    "output_tokens": c.output_tokens,
                    "cache_created": c.cache_created,
                    "cache_read": c.cache_read,
                    "latency_ms": round(c.latency_ms, 1),
                }
                for c in self.calls
            ],
        }
