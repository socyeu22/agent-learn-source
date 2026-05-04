import time
from agents.react_agent import run_react_agent, run_with_reflexion
from tools.basic_tools import TOOLS


class TokenTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, usage):
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens

    def reset(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def cost_usd(self):
        # Haiku 4.5: $1/M input, $5/M output
        return (self.input_tokens * 1 + self.output_tokens * 5) / 1_000_000


TEST_CASES = [
    {
        "name": "simple_factual",
        "task": "Bây giờ là mấy giờ? Trả lời ngắn gọn.",
    },
    {
        "name": "analytical",
        "task": "Phân tích ưu nhược điểm của việc học online vs offline",
    },
    {
        "name": "intermediate",
        "task": (
            "Nếu mỗi năm tôi tiết kiệm 100 triệu VND và gửi ngân hàng với lãi suất 8%/năm "
            "(lãi gộp), sau bao nhiêu năm tôi tích lũy đủ 10 tỉ VND? Hãy tính từng năm."
        ),
    },
]


def measure_quality_proxies(answer: str) -> dict:
    return {
        "word_count": len(answer.split()),
        "has_numbers": any(c.isdigit() for c in answer),
        "has_conclusion": any(
            kw in answer.lower()
            for kw in ["kết luận", "tóm lại", "khuyến nghị", "vậy", "do đó"]
        ),
        "num_paragraphs": answer.count("\n\n") + 1,
    }


def measure_run(label: str, runner_fn, task: str) -> dict:
    tracker = TokenTracker()
    start = time.time()
    raw = runner_fn(task, tracker)
    duration = round(time.time() - start, 2)

    # runner_fn trả về 3 dạng:
    # - str: run_react_agent không có trace
    # - {"answer", "trace"}: run_react_agent với return_trace=True
    # - {"final_answer", "history"}: run_with_reflexion với return_history=True
    if isinstance(raw, dict) and "final_answer" in raw:
        answer = raw["final_answer"]
        history = raw["history"]
        trace = []
    elif isinstance(raw, dict) and "answer" in raw:
        answer = raw["answer"]
        history = []
        trace = raw["trace"]
    else:
        answer = raw
        history = []
        trace = []

    return {
        "label": label,
        "answer": answer,
        "history": history,
        "trace": trace,
        "duration_s": duration,
        "input_tokens": tracker.input_tokens,
        "output_tokens": tracker.output_tokens,
        "cost_usd": round(tracker.cost_usd(), 6),
        "quality_proxies": measure_quality_proxies(answer),
    }


def compare_for_task(test_case: dict) -> dict:
    print(f"\n{'='*60}")
    print(f"[Task: {test_case['name']}] {test_case['task'][:60]}...")

    print("\n>> Running WITHOUT Reflexion...")
    result_a = measure_run(
        "without_reflexion",
        lambda t, tr: run_react_agent(t, TOOLS, tracker=tr, return_trace=True),
        test_case["task"],
    )

    print("\n>> Running WITH Reflexion...")
    result_b = measure_run(
        "with_reflexion",
        lambda t, tr: run_with_reflexion(t, TOOLS, max_retries=2, tracker=tr, return_history=True),
        test_case["task"],
    )

    return {"task": test_case, "without": result_a, "with": result_b}


def write_markdown_report(all_results: list, path: str):
    from datetime import datetime

    lines = []
    lines.append("# Reflexion Comparison Report")
    lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Summary table
    lines.append("## Summary Table")
    lines.append("| Task | Without Reflexion | With Reflexion | Token overhead |")
    lines.append("|---|---|---|---|")
    for r in all_results:
        wo = r["without"]
        wi = r["with"]
        total_wo = wo["input_tokens"] + wo["output_tokens"]
        total_wi = wi["input_tokens"] + wi["output_tokens"]
        overhead = f"{total_wi / total_wo:.1f}x" if total_wo > 0 else "N/A"
        lines.append(
            f"| {r['task']['name']} "
            f"| {total_wo} tokens, {wo['duration_s']}s, ${wo['cost_usd']} "
            f"| {total_wi} tokens, {wi['duration_s']}s, ${wi['cost_usd']} "
            f"| {overhead} |"
        )

    lines.append("")

    # Detailed results
    lines.append("## Detailed Results")
    for r in all_results:
        tc = r["task"]
        wo = r["without"]
        wi = r["with"]

        lines.append(f"\n### Task: {tc['name']}")
        lines.append(f"**Question:** {tc['task']}\n")

        for result in [wo, wi]:
            label = result["label"].replace("_", " ").title()
            p = result["quality_proxies"]
            lines.append(
                f"**{label}** "
                f"({result['input_tokens']}+{result['output_tokens']} tokens, "
                f"{result['duration_s']}s, ${result['cost_usd']}):"
            )
            lines.append(
                f"- Proxy metrics: {p['word_count']} words, "
                f"has_numbers={p['has_numbers']}, "
                f"has_conclusion={p['has_conclusion']}, "
                f"paragraphs={p['num_paragraphs']}"
            )

            # Hiển thị trace trực tiếp (without_reflexion — không có Reflexion loop)
            if result["trace"]:
                for step in result["trace"]:
                    lines.append(f"\n*Iteration {step['iteration']}*")
                    lines.append("```")
                    lines.append(step["llm_output"])
                    lines.append("```")
                    if step["observation"]:
                        lines.append(f"→ Observation: `{step['observation']}`")

            # Hiển thị từng attempt trong Reflexion loop (nếu có)
            if result["history"]:
                for h in result["history"]:
                    status = "✅ passed" if h["passed"] else "🔄 retry"
                    lines.append(f"\n**Attempt {h['attempt']}** — {status}")
                    lines.append(f"- Scores: {h['scores']}")
                    lines.append(f"- Feedback: {h['feedback']}")
                    for step in h["trace"]:
                        lines.append(f"\n*Iteration {step['iteration']}*")
                        lines.append("```")
                        lines.append(step["llm_output"])
                        lines.append("```")
                        if step["observation"]:
                            lines.append(f"→ Observation: `{step['observation']}`")
                    lines.append("\n*Answer được critique:*")
                    lines.append("```")
                    lines.append(h["answer"])
                    lines.append("```")

            lines.append("\n**Final Answer:**")
            lines.append("```")
            lines.append(result["answer"])
            lines.append("```\n")

        lines.append("**Analysis:** *(tự điền nhận xét sau khi đọc kết quả)*\n")
        lines.append("---")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n[Report saved to {path}]")


if __name__ == "__main__":
    results = [compare_for_task(tc) for tc in TEST_CASES]
    write_markdown_report(results, "notes/reflexion-comparison.md")
