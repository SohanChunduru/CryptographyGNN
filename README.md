# GNN-guided SAT solving on HiTag2: milestone code

CS224W Fall 2026 project milestone. Research question: do more expressive GNNs
(symmetry breaking beyond 1-WL, XOR-aware graphs) guide SAT solvers better on
cryptanalysis instances than RLAF's literal-clause GNN?

This repository holds the scripts and results produced so far:

| File | Purpose |
|---|---|
| `build_graph.py` | Converts a DIMACS CNF into a PyG `HeteroData` literal-clause graph (node types `lit`, `clause`; edges lit->clause, clause->lit, lit<->negated lit; features `log(deg+1)`) |
| `run_cms.py` | Runs CryptoMiniSat 5.17.0 on a glob of CNF files (8 parallel workers, 600 s limit) and writes decisions, conflicts, CPU time, XOR and matrix counts to a CSV |
| `wl_diag.py` | 1-WL color refinement on one instance, printing classes per round |
| `wl_batch2.py` | Same refinement over a set of instances, excluding variables that occur in no clause; writes a CSV |
| `results/` | `glucose_crypto{20,15,10}_mac.csv`, `cms_crypto{20,15,10}_mac.csv`, `wl2_crypto{20,15,10}.csv` |

Not included: the authors' code and data. The unguided-Glucose baseline was
produced with their evaluation script, run unmodified.

## Setup (macOS, Apple M1)

Everything below was run on one Apple M1 laptop. Do not compare these timings with
numbers from other machines.

1. Clone the RLAF code: `git clone https://github.com/toenshoff/RLAF.git` and
   copy the scripts from this repository into its root.
2. Download `data.zip` from the figshare link in RLAF's README and unzip it in the
   RLAF root, so that files are at `data/test/crypto/{20,15,10}/*.cnf`.
3. Build Glucose. `build_solvers.sh` fails on macOS (the March Makefile needs
   `gcc-10`, and the static Glucose link is rejected by the macOS linker), so build
   only the Glucose binaries, dynamically, and give the repo the name it expects:

   ```bash
   cd solvers/glucose/simp && make && cd ../../..
   cd solvers/glucose_weighted/simp && make && cd ../../..
   ln -s glucose solvers/glucose/simp/glucose_static
   ln -s glucose solvers/glucose_weighted/simp/glucose_static
   ```

4. Python environment. `pip install -e .` fails on macOS (RLAF pins
   `triton==3.1.0`, which has no Mac wheel), so install only what the scripts need:

   ```bash
   conda create -n rlaf python=3.12 -y && conda activate rlaf
   pip install joblib hydra-core omegaconf pandas numpy==1.26.4 tqdm python-sat
   pip install torch==2.5.0 torch_geometric
   ```

5. CryptoMiniSat: `brew install cryptominisat` (installs `cryptominisat5`).

## Reproducing the results

Run from the RLAF root, one job at a time (parallel jobs distort timings). The
CRYPTO(10) Glucose run takes about an hour.

```bash
mkdir -p results
for n in 20 15 10; do
  python evaluate_base_solver.py solver.solver=glucose "dataset.eval_path=data/test/crypto/$n/*.cnf"
  cp runs/glucose/solver_stats.csv results/glucose_crypto${n}_mac.csv
  python run_cms.py "data/test/crypto/$n/*.cnf" results/cms_crypto${n}_mac.csv
  python wl_batch2.py "data/test/crypto/$n/*.cnf" results/wl2_crypto${n}.csv
done
python build_graph.py data/test/crypto/20/hitag2-20-56-8-0xce7d1f1345b1e0-68.cnf
```

## Results so far

Unguided solvers, 100 UNSAT instances per set. Means over instances solved by both
solvers; Glucose time is CPU time.

| Set | Glucose time (s) | Glucose decisions | CryptoMiniSat time (s) | CryptoMiniSat decisions | Solved (Glucose / CMS) |
|---|---|---|---|---|---|
| CRYPTO(20) | 1.20 | 51,294 | 0.53 | 11,753 | 100 / 100 |
| CRYPTO(15) | 5.74 | 225,447 | 2.13 | 78,318 | 100 / 100 |
| CRYPTO(10) | 156.3 | 3.72M | 136.6 | 3.07M | 100 / 99 |

- The Glucose means match those reported in the RLAF paper (51,294 / 225,447 /
  3,753,850 decisions over all 100 instances).
- At n=10 the CryptoMiniSat mean is slightly lower, but the median is not (Glucose
  90.0 s vs. CryptoMiniSat 115.9 s on the 99 shared instances; CryptoMiniSat is
  faster on 29 of 99). Glucose's mean is inflated by a heavy tail. One instance hit
  CryptoMiniSat's 600 s limit; Glucose solved it in 262 s.
- The CNFs contain no native XOR lines, yet CryptoMiniSat builds Gaussian-elimination
  matrices on them (mean 1.0, 1.65 and 9.2 per instance at n=20, 15, 10), which
  suggests it detects XORs itself. Not yet verified.

1-WL diagnostic (variables occurring in no clause excluded; mean over 100 instances):

| Set | Unused vars | Used vars | Color classes | Used vars in a shared class | Largest class |
|---|---|---|---|---|---|
| CRYPTO(20) | 40.8 | 492.6 | 402.6 | 18.7% | 49.9 |
| CRYPTO(15) | 27.2 | 515.7 | 439.3 | 15.2% | 42.9 |
| CRYPTO(10) | 15.3 | 535.7 | 469.5 | 12.7% | 37.1 |

Refinement uses four rounds; on the instances inspected the partition stopped
changing after round 1.

## Limitations

- One run per instance on one laptop; no confidence intervals.
- CryptoMiniSat used default settings and a 600 s limit, while the repository's
  Glucose configuration allows far longer runs.
- The training code in the RLAF repository needs Linux and CUDA, so nothing here
  trains a model yet.

## Next steps

Train the RLAF baseline, an XOR-aware heterogeneous model and a symmetry-breaking
variant on a GCP VM; combine the best two; evaluate against unguided Glucose and
CryptoMiniSat on harder HiTag2 sets and on Simon; release instances and PyG graphs
on Hugging Face.

## References

- J. Tönshoff and M. Grohe. Learning from algorithm feedback: One-shot SAT solver
  guidance with GNNs. ICLR 2026. https://github.com/toenshoff/RLAF
- M. Soos, K. Nohl, C. Castelluccia. Extending SAT solvers to cryptographic
  problems. SAT 2009 (CryptoMiniSat).
- M. Soos. Grain of Salt. Tools'10 Workshop, 2010.
