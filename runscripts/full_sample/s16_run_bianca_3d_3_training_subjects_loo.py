from pathlib import Path
from bianca.workflows.bianca import run_bianca
import pandas as pd
import numpy as np
from shutil import copyfile


training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_data")
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample")

name = "bianca"
n_cpu = 30

####
# 3D
acq = "3D"

bianca_dir = base_dir / acq / name
wd_dir = Path("/tmp/fl") / "_wd" / acq / name
crash_dir = Path("/tmp/fl") / "_crash" / acq / name
clf_file = bianca_dir / "clf" / f"acq-{acq}_run-1_FLAIR_classifier"

df = pd.read_csv(bianca_dir / "masterfile_wHeader.txt", sep=" ")
test_subs = (df.manual_mask == "XXX")
training_subs = ~test_subs
training_subs_idx = np.where(training_subs)[0]
test_subs_idx = np.where(test_subs)[0]

query_sub_idx = training_subs_idx
run_bianca(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True, training_subject_idx=training_subs_idx,
           query_subject_idx=query_sub_idx)
