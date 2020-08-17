from pathlib import Path
from bianca.workflows.bianca_threshold import bianca_threshold
from bianca.utils import get_subject_sessions

name = "bianca_threshold"
thresholds = [.99]

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample")
base_dir_wd = Path("/tmp/fl")
mask_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/masks_training_data")
bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"

####
# 2D
acq = "2D"
bianca_dir = base_dir / acq / "bianca"
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = base_dir / acq / name
wd_dir = base_dir_wd / "_wd" / acq / name
crash_dir = base_dir_wd / "_crash" / acq / name

subjects_sessions = get_subject_sessions(bids_dir, acq)

bianca_threshold(bianca_dir, mask_dir, flair_prep_dir, wd_dir, crash_dir, out_dir, subjects_sessions, acq,
                 thresholds, run_BiancaOverlapMeasures=False, n_cpu=25)

####
# 3D
acq = "3D"
bianca_dir = base_dir / acq / "bianca"
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = base_dir / acq / name
wd_dir = base_dir_wd / "_wd" / acq / name
crash_dir = base_dir_wd / "_crash" / acq / name

subjects_sessions = get_subject_sessions(bids_dir, acq)

bianca_threshold(bianca_dir, mask_dir, flair_prep_dir, wd_dir, crash_dir, out_dir, subjects_sessions, acq,
                 thresholds, run_BiancaOverlapMeasures=False, n_cpu=25)
