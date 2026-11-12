import sys, glob
import pandas as pd
from build_graph import build_graph
from wl_diag import wl_classes

pattern, outfile = sys.argv[1], sys.argv[2]
rows = []
for path in sorted(glob.glob(pattern)):
    n_var, hist = wl_classes(build_graph(path), rounds=4)
    r, k, big, shared = hist[-1]
    rows.append(dict(file=path, n_vars=n_var, classes=k,
                     frac_classes=k / n_var, largest=big,
                     frac_shared=shared / n_var))
df = pd.DataFrame(rows)
df.to_csv(outfile, index=False)
print(df.describe().loc[["mean", "min", "max"]])
