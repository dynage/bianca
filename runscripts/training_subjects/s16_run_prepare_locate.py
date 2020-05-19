from pathlib import Path
from bianca.prepare_locate import prepare_locate

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")
training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/masks_training_data/sub-{subject}/ses-{session}")

####
# 2D
acq = "2D"

flair_dir = base_dir / acq / "prepare_flair/sub-{subject}/ses-{session}/anat"
bianca_dir = base_dir / acq / "bianca/sub-{subject}/ses-{session}/anat"
locate_out_dir = base_dir / acq / "locate"

subjects_sessions = [("lhabX0017", "tp2"),
                     ("lhabX0061", "tp2"),
                     ("lhabX0148", "tp3"),
                     ("lhabX0150", "tp2"),
                     ("lhabX0159", "tp2"),
                     ("lhabX0166", "tp2"),
                     ("lhabX0176", "tp1"),
                     ("lhabX0178", "tp2"),
                     ("lhabX0183", "tp2"),
                     ("lhabX0220", "tp5"),
                     ]

prepare_locate(flair_dir, bianca_dir, training_data_dir, locate_out_dir, subjects_sessions, acq)

####
# 3D
acq = "3D"

flair_dir = base_dir / acq / "prepare_flair/sub-{subject}/ses-{session}/anat"
bianca_dir = base_dir / acq / "bianca/sub-{subject}/ses-{session}/anat"
locate_out_dir = base_dir / acq / "locate"

subjects_sessions = [("lhabX0017", "tp2"),
                     ("lhabX0061", "tp2"),
                     ("lhabX0064", "tp3"),
                     ("lhabX0098", "tp2"),
                     ("lhabX0148", "tp3"),
                     ("lhabX0150", "tp2"),
                     ("lhabX0159", "tp2"),
                     ("lhabX0166", "tp2"),
                     ("lhabX0175", "tp3"),
                     ("lhabX0176", "tp1"),
                     ("lhabX0178", "tp2"),
                     ("lhabX0183", "tp2"),
                     ("lhabX0185", "tp2"),
                     ("lhabX0188", "tp5"),
                     ("lhabX0219", "tp5"),
                     ("lhabX0220", "tp5"),
                     ]

prepare_locate(flair_dir, bianca_dir, training_data_dir, locate_out_dir, subjects_sessions, acq)
