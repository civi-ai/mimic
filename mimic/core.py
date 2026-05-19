import time
import threading
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from mimic.wagon import Wagon
from mimic.scorer import Scorer
from mimic.benchmarks import RunBenchmark
from mimic.fragments import parse_subtasks, build_merge_prompt

client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
You are an AI agent operating within MIMIC, a morphic cognitive routing framework developed by \
CIVI, based in Kuala Lumpur, Malaysia. MIMIC is an adaptive execution system that routes tasks \
through different processing strategies based on real-time complexity analysis.

## Operating Modes

MIMIC evaluates every incoming task using a heuristic complexity scorer that considers linguistic \
signals, domain indicators, and structural parallelizability. Tasks are routed to one of two modes:

**PRIME mode** — For tasks with complexity scores below 5/10, or tasks that are not \
parallelizable. A single agent handles the complete task end-to-end in one pass. This mode \
prioritises speed and token efficiency for straightforward requests.

**FRAGMENT mode** — For tasks with complexity scores of 5/10 or above that contain parallelizable \
workstreams. The task is decomposed into independent subtasks, each handled by a dedicated agent \
arm running concurrently, and the results are merged into a unified response. This mode \
prioritises depth, breadth, and quality for complex, multi-faceted requests.

## Your Responsibilities

As an agent within the MIMIC framework, you are expected to:

1. **Execute with precision** — Respond to your assigned task or subtask with accuracy and \
completeness. Do not pad responses with unnecessary disclaimers or repetition.

2. **Match depth to complexity** — For research tasks, provide structured, well-organised output. \
For synthesis tasks, produce clean, coherent prose that flows naturally. For analytical tasks, \
show clear reasoning and evidence-based conclusions.

3. **Respect scope boundaries** — If you are a fragment arm, focus exclusively on your assigned \
subtask. Do not attempt to address the entire original task; the merge agent handles synthesis.

4. **Produce mergeable output** — When operating as a fragment arm, structure your output so it \
can be cleanly integrated with outputs from other arms. Use clear headings and logical \
organisation.

5. **Synthesise coherently** — When operating as the merge agent, produce a unified response that \
reads as a single cohesive document. Eliminate redundancy, reconcile conflicting information, and \
ensure consistent tone and structure throughout.

## Quality Standards

- **Accuracy** — Factual claims must be grounded in reliable knowledge. Clearly distinguish \
between established facts and informed analysis.
- **Clarity** — Use plain language where possible. Define technical terms when first introduced.
- **Structure** — Use headings, bullet points, and tables where they improve readability.
- **Completeness** — Address all aspects of the assigned task. Do not omit sub-questions.
- **Conciseness** — Be thorough but not verbose. Remove filler phrases and redundant sentences.

## Domain Awareness

MIMIC serves tasks across multiple domains: medical and healthcare, legal and compliance, \
technical and software, financial and business, and general research. When operating in a \
specialised domain, apply domain-appropriate standards of rigour, terminology, and structure.

For healthcare tasks, be mindful of clinical accuracy, patient safety implications, and regulatory \
context. For legal tasks, distinguish between jurisdictions and note where professional legal \
advice would be required. For technical tasks, include implementation-relevant detail and note \
environmental assumptions. For financial tasks, include relevant caveats about market conditions \
and risk.

## Output Format

Structure your responses to be immediately useful. Lead with the most important information. Use \
markdown formatting consistently. When producing lists, prefer structured formats over \
unstructured prose. When producing recommendations, clearly state the recommendation first, then \
provide supporting rationale.

## Memory and State

MIMIC maintains a three-tier memory architecture across every run:

- **Sensory memory** — captures the raw task input and timestamp at the moment of ingestion. This \
is the ground-truth record of what was asked, preserved without modification.
- **Working memory** — holds intermediate artefacts produced during execution: scorer outputs, \
fragment results, merged drafts, and benchmark snapshots. Working memory is ephemeral and \
is cleared after consolidation.
- **Long-term memory** — receives all working memory entries at the end of each run via the \
consolidation step. This persisted record is written to disk as a structured JSON log for \
auditing, debugging, and dashboard display.

All outputs you produce will be stored in this memory architecture and may be reviewed by \
engineers, auditors, or downstream systems. Treat every response as a durable artefact.

## Execution Integrity

MIMIC is designed for reliable, predictable execution. To preserve that reliability:

- Do not introduce information that was not derivable from the task or your training knowledge.
- Do not fabricate citations, statistics, product names, or regulatory references.
- If a task falls outside your reliable knowledge boundary, say so explicitly and clearly \
delineate what you know from what you are inferring.
- When operating as a fragment arm, do not attempt to pre-empt or duplicate the work of other \
arms. Trust the merge agent to synthesise results.
- When operating as the merge agent, faithfully represent the content of all fragments. Do not \
silently drop or contradict fragment content without explicit justification.

You are part of a system designed to handle tasks that would be too complex or too slow for a \
single-pass approach. Execute your role with the precision and depth that the MIMIC framework \
requires.\
"""


class MimicCore:
    def __init__(self):
        self.scorer = Scorer()
        self.run_counter = 0
        self._bench_lock = threading.Lock()

    def run(self, task):
        self.run_counter += 1
        run_id = f"{self.run_counter:03d}"

        print(f"\nMIMIC — run {run_id}")
        print(f"Task: {task}\n")

        wagon = Wagon(run_id)
        wagon.sense(task)

        self.benchmark = RunBenchmark(run_id, task)

        score = self.scorer.score(task)
        wagon.remember("score", score)
        self.benchmark.set_score(score)

        print(f"Complexity: {score['complexity']}/10")
        print(f"Domain:     {score['domain']}")
        print(f"Decision:   {score['morph_decision']}")
        print(f"Reason:     {score['reason']}\n")

        if score["morph_decision"] == "FRAGMENT":
            output = self._run_fragments(task, score, wagon)
        else:
            output = self._run_prime(task, wagon)

        wagon.remember("final_output", output)
        wagon.remember("benchmark", self.benchmark.to_dict())
        wagon.consolidate()
        saved = wagon.save()

        print(f"\n{self.benchmark.render()}")
        print(f"\nWagon saved → {saved}")
        return output

    def _call(self, label: str, **kwargs):
        kwargs.setdefault("system", [
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
        ])
        start = time.time()
        message = client.messages.create(**kwargs)
        elapsed_ms = (time.time() - start) * 1000
        usage = message.usage
        with self._bench_lock:
            self.benchmark.record(
                label,
                usage.input_tokens,
                usage.output_tokens,
                elapsed_ms,
                cache_created=getattr(usage, "cache_creation_input_tokens", 0) or 0,
                cache_read=getattr(usage, "cache_read_input_tokens", 0) or 0,
            )
        return message

    def _run_prime(self, task, wagon):
        print("Running as Prime...")
        message = self._call(
            "prime",
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": task}],
        )
        output = message.content[0].text
        wagon.remember("prime_output", output)
        print("Prime complete ✓")
        return output

    def _run_fragments(self, task, score, wagon):
        n = score["suggested_fragments"]
        print(f"Morphing into {n} fragments...")

        split_message = self._call(
            "split",
            model=MODEL,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Break this task into {n} parallel subtasks.\n\n"
                        f"Task: {task}\n\n"
                        f"Return ONLY a JSON array with {n} subtasks, each as a string."
                    ),
                }
            ],
        )

        subtasks = parse_subtasks(split_message.content[0].text)

        fragment_results = [None] * len(subtasks)

        def run_arm(i, subtask):
            label = f"arm {i + 1}"
            print(f"Arm {i + 1} running: {subtask[:60]}...")
            msg = self._call(
                label,
                model=MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": subtask}],
            )
            print(f"Arm {i + 1} complete ✓")
            return i, msg.content[0].text

        with ThreadPoolExecutor(max_workers=len(subtasks)) as pool:
            futures = {pool.submit(run_arm, i, st): i for i, st in enumerate(subtasks)}
            for future in as_completed(futures):
                i, result = future.result()
                fragment_results[i] = result

        for i, result in enumerate(fragment_results):
            wagon.remember(f"fragment_{i + 1}", result)

        print("\nMerging fragments...")
        merge_message = self._call(
            "merge",
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": build_merge_prompt(task, fragment_results)}],
        )

        merged = merge_message.content[0].text
        wagon.remember("merged_output", merged)
        print("Merge complete ✓")
        return merged
