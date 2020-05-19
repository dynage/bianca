from pathlib import Path
from bianca.prepare_locate import prepare_locate
from bianca.utils import get_subject_sessions

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample")
training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/masks_training_data/sub-{subject}/ses-{session}")

####
# 2D
acq = "2D"

flair_dir = base_dir / acq / "prepare_flair/sub-{subject}/ses-{session}/anat"
bianca_dir = base_dir / acq / "bianca/sub-{subject}/ses-{session}/anat"
locate_out_dir = base_dir / acq / "locate"

subjects_sessions = get_subject_sessions(bids_dir, acq)


prepare_locate(flair_dir, bianca_dir, training_data_dir, locate_out_dir, subjects_sessions, acq)

####
# 3D
acq = "3D"

flair_dir = base_dir / acq / "prepare_flair/sub-{subject}/ses-{session}/anat"
bianca_dir = base_dir / acq / "bianca/sub-{subject}/ses-{session}/anat"
locate_out_dir = base_dir / acq / "locate"

subjects_sessions = get_subject_sessions(bids_dir, acq)

prepare_locate(flair_dir, bianca_dir, training_data_dir, locate_out_dir, subjects_sessions, acq)
