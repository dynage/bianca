from pathlib import Path
from bianca.workflows.post_locate_masking import post_locate_masking

name = "post_locate_masking"
thresholds = [.7, .9, .95, .99]

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
locate_dir = base_dir / acq / "locate"
out_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

post_locate_masking(locate_dir, wd_dir, crash_dir, out_dir, subjects_sessions, n_cpu=25)

####
# 3D
acq = "3D"
locate_dir = base_dir / acq / "locate"
out_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

post_locate_masking(locate_dir, wd_dir, crash_dir, out_dir, subjects_sessions, n_cpu=25)
