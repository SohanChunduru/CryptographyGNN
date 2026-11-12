import sys, glob, collections
import pandas as pd
from build_graph import build_graph

def used_var_colors(data, rounds=4):
    n_lit, n_cls = data["lit"].num_nodes, data["clause"].num_nodes
    lit_nb = [[] for _ in range(n_lit)]
    cls_nb = [[] for _ in range(n_cls)]
    for l, c in data["lit", "in", "clause"].edge_index.t().tolist():
        lit_nb[l].append(c); cls_nb[c].append(l)
    lit = [len(x) for x in lit_nb]; cls = [len(x) for x in cls_nb]
    for _ in range(rounds):
        t = {}
        new_cls = [t.setdefault((cls[c], tuple(sorted(lit[l] for l in cls_nb[c]))), len(t))
                   for c in range(n_cls)]
        t = {}
        lit = [t.setdefault((lit[l], lit[l ^ 1], tuple(sorted(new_cls[c] for c in lit_nb[l]))), len(t))
               for l in range(n_lit)]
        cls = new_cls
    used = [v for v in range(n_lit // 2) if lit_nb[2 * v] or lit_nb[2 * v + 1]]
    return n_lit // 2, [(lit[2 * v], lit[2 * v + 1]) for v in used]

rows = []
for path in sorted(glob.glob(sys.argv[1])):
    n_var, cols = used_var_colors(build_graph(path))
    sizes = collections.Counter(cols)
    shared = sum(s for s in sizes.values() if s > 1)
    rows.append(dict(file=path, n_vars=n_var, n_unused=n_var - len(cols),
                     n_used=len(cols), classes=len(sizes),
                     frac_shared=shared / len(cols), largest=max(sizes.values())))
df = pd.DataFrame(rows); df.to_csv(sys.argv[2], index=False)
print(df.describe().loc[["mean", "min", "max"]])
