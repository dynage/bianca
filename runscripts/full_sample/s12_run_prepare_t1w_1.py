"""
screen -L \
docker run --rm -ti \
-v /data.nfs/dynage/lhab_data_ro:/home/fliem/lhab_data \
-v /data.nfs/dynage/lhab_collaboration_wmh/:/home/fliem/lhab_collaboration/WMH \
-v /home/ubuntu/bianca_tmp:/data \
-v /data.nfs/dynage/lhab_collaboration_wmh/bianca_code:/code/bianca/ \
bianca:dev \
/code/bianca/runscripts/full_sample/s12_run_prepare_t1w_1.py

"""
from pathlib import Path
from bianca.workflows.prepare_t1w import prepare_t1w
from bianca.utils import get_subject_sessions

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
smriprep_dir = "/home/fliem/lhab_data/LHAB/LHAB_v1.1.1/derivates/fmriprep_1.0.5_wSTC/fmriprep"

name = "prepare_t1w"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")

out_dir = base_dir / name
wd_dir = Path("/data") / "_wd" / name
crash_dir = Path("/data") / "_crash" / name

####
# collect flair subjects-sessions
subjects_sessions = get_subject_sessions(bids_dir, "*")

smriprep_subj = {('lhabX0196', 'tp1'), ('lhabX0196', 'tp2'), ('lhabX0196', 'tp3'), ('lhabX0196', 'tp5'),
                 ('lhabX0196', 'tp6'), ('lhabX0125', 'tp1')}
subjects_sessions = list(set(subjects_sessions) - smriprep_subj)
subjects_sessions.sort()

subjects_sessions = subjects_sessions[:250]
# subjects_sessions = subjects_sessions[250:500]
# subjects_sessions = subjects_sessions[500:750]
# subjects_sessions = subjects_sessions[750:]

print(f"\n{len(subjects_sessions)} subjects-sessions\n")

prepare_t1w(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, subjects_sessions, n_cpu=32, omp_nthreads=1)
