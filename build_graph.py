import sys
import torch
from torch_geometric.data import HeteroData


def read_cnf(path):
    """Parse DIMACS. Returns (num_vars, clauses, num_xor_lines)."""
    n_vars, clauses, cur, n_xor = 0, [], [], 0
    with open(path) as f:
        for line in f:
            if not line.strip() or line[0] == "c":
                continue
            if line[0] == "p":
                n_vars = int(line.split()[2])
                continue
            if line[0] == "x":  # native XOR line (CryptoMiniSat format)
                n_xor += 1
                continue
            for tok in line.split():
                v = int(tok)
                if v == 0:
                    clauses.append(cur)
                    cur = []
                else:
                    cur.append(v)
    return n_vars, clauses, n_xor


def lit_index(l):
    """+v -> 2(v-1), -v -> 2(v-1)+1, so a literal's negation is index ^ 1."""
    return 2 * (abs(l) - 1) + (1 if l < 0 else 0)


def build_graph(path):
    n_vars, clauses, n_xor = read_cnf(path)
    n_lit, n_cls = 2 * n_vars, len(clauses)

    src, dst = [], []
    for c, clause in enumerate(clauses):
        for l in clause:
            src.append(lit_index(l))
            dst.append(c)
    lit_to_cls = torch.tensor([src, dst], dtype=torch.long)

    pos = torch.arange(0, n_lit, 2)  # positive literal of each variable
    neg_edges = torch.stack([torch.cat([pos, pos + 1]),
                             torch.cat([pos + 1, pos])])

    # Initial features as in the paper: log(degree + 1)
    lit_deg = torch.bincount(lit_to_cls[0], minlength=n_lit).float()
    cls_deg = torch.bincount(lit_to_cls[1], minlength=n_cls).float()

    data = HeteroData()
    data["lit"].x = torch.log(lit_deg + 1).unsqueeze(1)
    data["clause"].x = torch.log(cls_deg + 1).unsqueeze(1)
    data["lit", "in", "clause"].edge_index = lit_to_cls
    data["clause", "contains", "lit"].edge_index = lit_to_cls.flip(0)
    data["lit", "neg", "lit"].edge_index = neg_edges
    data.n_vars = n_vars
    data.n_xor_lines = n_xor
    return data


if __name__ == "__main__":
    d = build_graph(sys.argv[1])
    d.validate()
    print(d)
    print("variables:          ", d.n_vars)
    print("literal nodes:      ", d["lit"].num_nodes)
    print("clause nodes:       ", d["clause"].num_nodes)
    print("lit->clause edges:  ", d["lit", "in", "clause"].num_edges)
    print("lit<->lit neg edges:", d["lit", "neg", "lit"].num_edges)
    print("XOR lines in file:  ", d.n_xor_lines)
    print("mean clause length: ",
          d["lit", "in", "clause"].num_edges / d["clause"].num_nodes)
