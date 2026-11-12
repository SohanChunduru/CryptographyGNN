import re, subprocess, glob, sys, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

def run(path, timeout=600):
    t0 = time.time()
    try:
        p = subprocess.run(["cryptominisat5", path], capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(file=path, result="TIMEOUT", wall=timeout)
    out = p.stdout
    def grab(pat):
        m = re.search(pat, out)
        return float(m.group(1)) if m else None
    res = ("UNSAT" if "s UNSATISFIABLE" in out
           else "SAT" if "s SATISFIABLE" in out else "UNKNOWN")
    return dict(file=path, result=res, wall=time.time() - t0,
                cpu=grab(r"c Total time \(this thread\)\s*:\s*([\d.]+)"),
                decisions=grab(r"c decisions\s*:\s*(\d+)"),
                conflicts=grab(r"c conflicts\s*:\s*(\d+)"),
                xors=grab(r"c xors added by user\s*:\s*(\d+)"),
                matrices=grab(r"c matrix inits\s*:\s*(\d+)"))

pattern, outfile = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(pattern))
with ThreadPoolExecutor(8) as ex:
    rows = list(ex.map(run, files))
df = pd.DataFrame(rows)
df.to_csv(outfile, index=False)
print(df.result.value_counts())
print(df.mean(numeric_only=True))
