from pathlib import Path
from bianca.workflows.prepare_t1w import prepare_t1w

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
name = "prepare_t1w"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/")

out_dir = base_dir / name
wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

info_tpls = [
    ('lhabX0017', 'tp2'),
    ('lhabX0061', 'tp2'),
    ('lhabX0064', 'tp3'),
    ('lhabX0098', 'tp2'),
    ('lhabX0148', 'tp3'),
    ('lhabX0150', 'tp2'),
    ('lhabX0159', 'tp2'),
    ('lhabX0166', 'tp2'),
    ('lhabX0175', 'tp3'),
    ('lhabX0176', 'tp1'),
    ('lhabX0178', 'tp2'),
    ('lhabX0183', 'tp2'),
    ('lhabX0185', 'tp2'),
    ('lhabX0188', 'tp5'),
    ('lhabX0219', 'tp5'),
    ('lhabX0220', 'tp5')
]

prepare_t1w(bids_dir, out_dir, wd_dir, crash_dir, info_tpls, n_cpu=20, omp_nthreads=1)
