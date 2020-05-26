from pathlib import Path
from bianca.workflows.prepare_flair_intNorm import prepare_flair_intNorm

name = "prep_flair_intNorm"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")

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
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = flair_prep_dir
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name
prepare_flair_intNorm(flair_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions, acq, n_cpu=25)

####
# 3D
acq = "3D"
flair_prep_dir = base_dir / acq / "prepare_flair"
out_dir = flair_prep_dir
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name
prepare_flair_intNorm(flair_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions, acq, n_cpu=25)
