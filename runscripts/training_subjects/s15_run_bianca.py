from pathlib import Path
from bianca.workflows.bianca import run_bianca

training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_data")
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")

name = "bianca"
n_cpu = 32

####
# 2D
acq = "2D"

bianca_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

run_bianca(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)

####
# 3D
acq = "3D"

bianca_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

run_bianca(bianca_dir, wd_dir, crash_dir, n_cpu=n_cpu, save_classifier=True)
