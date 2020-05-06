from pathlib import Path
from bianca.workflows.prepare_t1w import prepare_t1w
from bianca.utils import get_subject_sessions

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
smriprep_dir = "/home/fliem/lhab_data/LHAB/LHAB_v1.1.1/derivates/fmriprep_1.0.5_wSTC/fmriprep"

name = "prepare_t1w"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")

out_dir = base_dir / name
wd_dir = base_dir / "_wd" / name
crash_dir = base_dir / "_crash" / name

####
# collect flair subjects-sessions
subjects_sessions = get_subject_sessions(bids_dir, "*")
print(f"\n{len(subjects_sessions)} subjects-sessions\n")

prepare_t1w(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, subjects_sessions, n_cpu=25, omp_nthreads=1)
