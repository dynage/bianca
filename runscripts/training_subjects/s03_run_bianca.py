from pathlib import Path
from bianca.workflows.bianca import run_bianca_loo

training_data_dir = Path("/Volumes/lhab_collaboration/WMH/BIANCA/training_data")

####
# 2D
acq = "2D"
base_dir = Path(f"/Volumes/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")
name = "bianca"
bianca_dir = base_dir / name

wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=4, save_classifier=True)

####
# 3D
acq = "3D"
base_dir = Path(f"/Volumes/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")
name = "bianca"
bianca_dir = base_dir / name

wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

run_bianca_loo(bianca_dir, wd_dir, crash_dir, n_cpu=4, save_classifier=True)
