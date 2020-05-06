from pathlib import Path
from bianca.workflows.prepare_template import prepare_template

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
smriprep_dir = "/home/fliem/lhab_data/LHAB/LHAB_v1.1.1/derivates/fmriprep_1.0.5_wSTC/fmriprep"
name = "prepare_template"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/")

out_dir = base_dir / name
wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

subjects = ['lhabX0017',
            'lhabX0061',
            'lhabX0064',
            'lhabX0098',
            'lhabX0148',
            'lhabX0150',
            'lhabX0159',
            'lhabX0166',
            'lhabX0175',
            'lhabX0176',
            'lhabX0178',
            'lhabX0183',
            'lhabX0185',
            'lhabX0188',
            'lhabX0219',
            'lhabX0220']

prepare_template(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, subjects, n_cpu=30,
                 omp_nthreads=2)
