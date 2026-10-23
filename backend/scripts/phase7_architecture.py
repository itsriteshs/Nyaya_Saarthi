"""Render actual implementation layers; no measured performance implied."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.config import BACKEND_DIR

def render(out):
    out.mkdir(parents=True,exist_ok=False)
    fig,ax=plt.subplots(figsize=(7.1,6));ax.set(xlim=(0,10),ylim=(0,10));ax.axis("off")
    boxes=[(2.5,9,"DATA\nSynthetic multilingual narratives\nSources, provisions, rule metadata"),
           (2.5,7.3,"NLP\nLanguage policy · SVM intent\nLocal SLM facts · normalization"),
           (2.5,5.6,"CONVERSATION\nAdaptive questions · conflicts\nFact review · revision invalidation"),
           (2.5,3.9,"LEGAL INTELLIGENCE\nEligibility · BM25 + semantic RRF\nStructured rule matching"),
           (2.5,2.2,"LOCAL EXPLANATION\nEvidence package · Llama / Mistral\nSchema + safety gate · fallback"),
           (2.5,.5,"USER OUTPUT\nSource-linked guidance · uncertainty\nPersisted handoff summary"),
           (7.7,7.8,"OFFLINE RESEARCH\nFrozen train/dev manifests\nDataset/reference audit\nSVM / LR / Naive Bayes\nToken-deletion surrogate\nRetrieval and R0–R3 probes\nBackend / browser checks\nJSON → dashboard / exports")]
    for x,y,text in boxes:ax.text(x,y,text,ha="center",va="center",fontsize=8,bbox=dict(boxstyle="round,pad=.55",facecolor="#eff3f8" if x<5 else "#f5eddf",edgecolor="#17385c"))
    for y in (9,7.3,5.6,3.9,2.2):ax.annotate("",xy=(2.5,y-1.07),xytext=(2.5,y-.6),arrowprops=dict(arrowstyle="->",color="#17385c"))
    ax.annotate("versioned artifacts",xy=(6,6.2),xytext=(5.5,4),fontsize=7,arrowprops=dict(arrowstyle="->",linestyle="dashed"))
    ax.set_title("NyayaSaarthi: implemented citizen path and offline research",fontsize=10)
    fig.tight_layout()
    for ext in ("png","svg","pdf"):fig.savefig(out/("architecture."+ext),dpi=300,bbox_inches="tight")
    plt.close(fig)
if __name__=="__main__":render(BACKEND_DIR/"experiments/phase7/architecture-20261023")
