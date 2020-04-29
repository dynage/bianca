from pathlib import Path
from bianca.workflows.bianca import run_bianca_loo

training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_data")
name = "bianca"
n_cpu = 16

####
# 2D
acq = "2D"
base_dir = Path(f"/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")
bianca_dir = base_dir / name

wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)

####
# 3D
acq = "3D"
base_dir = Path(f"/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")
bianca_dir = base_dir / name

wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)
