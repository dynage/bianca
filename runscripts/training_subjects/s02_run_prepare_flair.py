from pathlib import Path
from bianca.workflows.prepare_flair import prepare_bianca_data
from variables import info_tpls_2d, info_tpls_3d

# todo update wf image

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
name = "prepare_flair"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")
t1w_prep_dir = base_dir / "prepare_t1w"

####
# 2D
acq = "2D"

out_dir = base_dir / acq / name
wd_dir = base_dir / acq / "_wd" / name
crash_dir = base_dir / acq / "_crash" / name

prepare_bianca_data(bids_dir, t1w_prep_dir, out_dir, wd_dir, crash_dir, info_tpls_2d, n_cpu=20)

####
# 3D
acq = "3D"

out_dir = base_dir / acq / name
wd_dir = base_dir / acq / "_wd" / name
crash_dir = base_dir / acq / "_crash" / name

prepare_bianca_data(bids_dir, t1w_prep_dir, out_dir, wd_dir, crash_dir, info_tpls_3d, n_cpu=25)
