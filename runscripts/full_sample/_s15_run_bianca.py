# fixme


"""
full sample:

1. train clf (traing subs + 1 query sub)
2. run loo with training subs
3. run non-training subs with pretrained clf
"""
from pathlib import Path
from bianca.workflows.bianca import run_bianca_loo

training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_data")
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")

name = "bianca"
n_cpu = 32

####
# 2D
acq = "2D"

bianca_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)

####
# 3D
acq = "3D"

bianca_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)
