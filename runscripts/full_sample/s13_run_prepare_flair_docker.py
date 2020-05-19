"""
screen -L \
docker run --rm -ti \
-v /data.nfs/dynage/lhab_data_ro:/home/fliem/lhab_data \
-v /data.nfs/dynage/lhab_collaboration_wmh/:/home/fliem/lhab_collaboration/WMH \
-v /home/ubuntu/bianca_tmp:/data \
-v /data.nfs/dynage/lhab_collaboration_wmh/bianca_code:/code/bianca/ \
-v /data.nfs/dynage/lhab_collaboration_wmh/fsldata:/usr/share/fsl/5.0/data \
bianca:dev \
/code/bianca/runscripts/full_sample/s13_run_prepare_flair_docker.py
"""
from pathlib import Path
from bianca.workflows.prepare_flair import prepare_bianca_data
from bianca.utils import get_subject_sessions

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
name = "prepare_flair"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")
t1w_prep_dir = base_dir / "prepare_t1w"
template_prep_dir = base_dir / "prepare_template"

####
# 2D
acq = "2D"
#
subjects_sessions = get_subject_sessions(bids_dir, acq)
subjects_sessions.sort()


print(f"\n{len(subjects_sessions)} subjects-sessions for {acq}\n")

out_dir = base_dir / acq / name
wd_dir = Path("/data") / "_wd" / acq / name
crash_dir = Path("/data") / "_crash" / acq / name

prepare_bianca_data(bids_dir, template_prep_dir, t1w_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions,
                    flair_acq=acq, n_cpu=32, omp_nthreads=1)
