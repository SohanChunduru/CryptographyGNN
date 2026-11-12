import sys, collections
from build_graph import build_graph


def intern(table, key):
    return table.setdefault(key, len(table))


def wl_classes(data, rounds=10):
    n_lit = data["lit"].num_nodes
    n_cls = data["clause"].num_nodes
    n_var = n_lit // 2
    lit_nb = [[] for _ in range(n_lit)]   # clauses containing each literal
    cls_nb = [[] for _ in range(n_cls)]   # literals in each clause
    for l, c in data["lit", "in", "clause"].edge_index.t().tolist():
        lit_nb[l].append(c)
        cls_nb[c].append(l)

    # initial colors: node degree (the paper's initial feature is log(deg+1))
    lit = [len(lit_nb[l]) for l in range(n_lit)]
    cls = [len(cls_nb[c]) for c in range(n_cls)]

    history = []
    for r in range(rounds + 1):
        if r > 0:
            t = {}
            new_cls = [intern(t, (cls[c], tuple(sorted(lit[l] for l in cls_nb[c]))))
                       for c in range(n_cls)]
            t = {}
            new_lit = [intern(t, (lit[l], lit[l ^ 1],
                                  tuple(sorted(new_cls[c] for c in lit_nb[l]))))
                       for l in range(n_lit)]
            cls, lit = new_cls, new_lit
        var_color = [(lit[2 * v], lit[2 * v + 1]) for v in range(n_var)]
        sizes = collections.Counter(var_color)
        in_shared = sum(s for s in sizes.values() if s > 1)
        history.append((r, len(sizes), max(sizes.values()), in_shared))
    return n_var, history


if __name__ == "__main__":
    n_var, hist = wl_classes(build_graph(sys.argv[1]))
    print(f"variables: {n_var}")
    print("round  classes  largest_class  vars_in_shared_class")
    for r, k, big, shared in hist:
        print(f"{r:5d}  {k:7d}  {big:13d}  {shared:20d}")
