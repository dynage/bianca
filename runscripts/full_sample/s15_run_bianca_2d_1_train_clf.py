""""""
from pathlib import Path
from bianca.workflows.bianca import run_bianca
import pandas as pd
import numpy as np
from shutil import copyfile

training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_data")
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample")

name = "bianca"
n_cpu = 32

####
# 2D
acq = "2D"

bianca_dir = base_dir / acq / name
wd_dir = Path("/tmp/fl") / "_wd" / acq / name
crash_dir = Path("/tmp/fl") / "_crash" / acq / name
clf_dir = bianca_dir / "clf"
clf_dir.mkdir(exist_ok=True)

df = pd.read_csv(bianca_dir / "masterfile_wHeader.txt", sep=" ")
test_subs = (df.manual_mask == "XXX")
training_subs = ~test_subs
training_subs_idx = np.where(training_subs)[0]
test_subs_idx = np.where(test_subs)[0]

query_sub_idx = test_subs_idx[:1]
run_bianca(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True, training_subject_idx=training_subs_idx,
           query_subject_idx=query_sub_idx)

dd = df.iloc[query_sub_idx[0]]
in_dir = bianca_dir / f"sub-{dd.subject}" / f"ses-{dd.session}" / "anat"
in_files = list(in_dir.glob("sub*"))
for f in in_files:
    o_name = clf_dir / (f.name.replace(f"sub-{dd.subject}_ses-{dd.session}_", ""))
    copyfile(f, o_name)
