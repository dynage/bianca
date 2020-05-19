from pathlib import Path
from bianca.workflows.prepare_flair import prepare_bianca_data

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
name = "prepare_flair"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects")
t1w_prep_dir = base_dir / "prepare_t1w"
template_prep_dir = base_dir / "prepare_template"

####
# 2D
acq = "2D"

out_dir = base_dir / acq / name
wd_dir = base_dir / "_wd" / acq / name
crash_dir = base_dir / "_crash" / acq / name

subjects_sessions_2d = [
    # ('lhabX0064', 'tp3'),
    # ('lhabX0098', 'tp2'),
    # ('lhabX0175', 'tp3'),
    # ('lhabX0185', 'tp2'),
    ('lhabX0188', 'tp5'),
    # ('lhabX0219', 'tp5')
]

prepare_bianca_data(bids_dir, template_prep_dir, t1w_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions_2d,
                    flair_acq=acq, n_cpu=32, omp_nthreads=2)
