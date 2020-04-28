from pathlib import Path
from bianca.workflows.prepare_flair import prepare_bianca_data
from variables import info_tpls_2d, info_tpls_3d

# todo update wf image

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
fs_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/derivates/freesurfer_v6.0.1-5"
name = "prepare_flair"

####
# 2D
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/2D")

out_dir = base_dir / name
wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

prepare_bianca_data(bids_dir, out_dir, fs_dir, wd_dir, crash_dir, info_tpls_2d, n_cpu=13)

####
# 3D
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/3D")

out_dir = base_dir / name
wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

prepare_bianca_data(bids_dir, out_dir, fs_dir, wd_dir, crash_dir, info_tpls_3d, n_cpu=16)
