"""Reproduce Phase 6 figures from JSON metrics (requires matplotlib)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "experiments"
METRICS = ROOT / "metrics"
PLOTS = ROOT / "plots"


def read(name):
    return json.loads((METRICS / name).read_text(encoding="utf-8"))


def save(name):
    plt.tight_layout()
    plt.savefig(PLOTS / name, dpi=180, bbox_inches="tight")
    plt.close()


def run():
    PLOTS.mkdir(parents=True, exist_ok=True)
    nlp = read("phase6_nlp.json")
    retrieval = read("phase6_retrieval.json")
    fig, ax = plt.subplots(figsize=(7, 4))
    language = nlp["language"]
    ax.bar(["Prior script policy", "Phase 6 dominance policy"],
           [language["legacyPolicyOnSameSplit"]["overallAccuracy"], language["overallAccuracy"]],
           color=["#a8752b", "#071b3a"])
    ax.set_ylim(0, 1); ax.set_ylabel("Accuracy including abstentions")
    ax.set_title(f"Language classification, grouped test n={nlp['counts']['test']}")
    save("language_policy.png")

    labels = language["labels"]
    fig, ax = plt.subplots(figsize=(6, 5))
    matrix = np.asarray(language["confusion"])
    heat = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=35, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Recorded label")
    ax.set_title("Language confusion with abstentions")
    for row in range(len(labels)):
        for column in range(len(labels)):
            ax.text(column, row, str(matrix[row, column]), ha="center", va="center", fontsize=9)
    fig.colorbar(heat, ax=ax, label="Utterances")
    save("language_confusion.png")

    variants = retrieval["variants"]
    labels = ["BM25", "Semantic", "Hybrid"]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(7, 4))
    for offset, metric, color in [(-.22, "recall@1", "#a8752b"), (0, "recall@3", "#577590"), (.22, "mrr", "#071b3a")]:
        ax.bar(x + offset, [variants[v][metric] for v in ("bm25", "semantic", "hybrid")],
               width=.22, label=metric, color=color)
    ax.set_xticks(x, labels); ax.set_ylim(0, 1.05); ax.legend()
    ax.set_title(f"Admitted positives, n={variants['hybrid']['answerable']} (4 provisions)")
    save("retrieval_comparison.png")

    ablation = read("phase6_ablations.json")
    aq = ablation["adaptiveQuestioning"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["Initial utterance", "Recorded final context"],
           [aq["withoutAdaptiveCapturedRate"], aq["recordedFinalCapturedRate"]],
           color=["#a8752b", "#071b3a"])
    ax.set_ylim(0, 1); ax.set_ylabel("Recorded required-slot coverage")
    ax.set_title(f"Conversation dataset proxy, n={aq['n']}")
    save("adaptive_context.png")

    available = [(label, METRICS / f"phase6_llm_{label}.json") for label in ("llama3.2-3b", "mistral-7b")]
    present = [(label, read(path.name)) for label, path in available if path.exists()]
    if present:
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))
        axes[0].bar([label for label, _ in present], [d["overall"]["acceptedRate"] for _, d in present], color="#071b3a")
        axes[0].set_ylim(0, 1); axes[0].set_ylabel("Structural acceptance rate")
        axes[1].bar([label for label, _ in present], [d["overall"]["latencyMs"]["median"] / 1000 for _, d in present], color="#a8752b")
        axes[1].set_ylabel("Median generation seconds")
        fig.suptitle("Frozen synthetic evidence, 9 outputs per model")
        save("llm_comparison.png")


if __name__ == "__main__":
    run()
