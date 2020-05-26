from pathlib import Path
from bianca.workflows.bianca_threshold import bianca_threshold

name = "bianca_threshold"
thresholds = [.7, .9, .95, .99]

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")
mask_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/masks_training_data")

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

####
# 2D
acq = "2D"
bianca_dir = base_dir / acq / "bianca"
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

bianca_threshold(bianca_dir, mask_dir, flair_prep_dir, wd_dir, crash_dir, out_dir, subjects_sessions, acq,
                 thresholds, n_cpu=25)

####
# 3D
acq = "3D"
bianca_dir = base_dir / acq / "bianca"
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

bianca_threshold(bianca_dir, mask_dir, flair_prep_dir, wd_dir, crash_dir, out_dir, subjects_sessions, acq,
                 thresholds, n_cpu=25)
