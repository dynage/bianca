from pathlib import Path
from bianca.utils import get_subject_sessions
import pandas as pd


def get_file_counts(d, f):
    return len(list(d.glob(f)))


#
#
# ####################################################
# # 1. prepare template
# bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
# name = "prepare_template"
# base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")
# out_dir = base_dir / name
#
# # collect flair subjects
# subjects_sessions = get_subject_sessions(bids_dir, "*")
# subjects, _ = list(zip(*subjects_sessions))
# subjects = list(set(subjects))
#
# df = pd.DataFrame()
# for subject in subjects:
#     f = f"sub-{subject}/anat/*nii.gz"
#     c = get_file_counts(out_dir, f)
#     df = df.append(pd.DataFrame({"subject": subject, "c": c}, index=[0]))
# missing = df.loc[(df["c"] < df["c"].max())]
#
# missingsub = missing.subject.tolist()
# print(missingsub)
# print(len(missing))
# if len(missing) > 0:
#     raise Exception(missing)
# print(f"\n{len(subjects)} subjects-sessions\n")
#
# ###################################################
# # 2. prepare t1w DONE
# bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
# name = "prepare_t1w"
# base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")
# out_dir = base_dir / name
#
# ####
# # collect flair subjects-sessions
# subjects_sessions = get_subject_sessions(bids_dir, "*")
#
# df = pd.DataFrame()
# for subject, session in subjects_sessions:
#     f = f"sub-{subject}/ses-{session}/anat/*nii.gz"
#     c = get_file_counts(out_dir, f)
#     df = df.append(pd.DataFrame({"subject": subject, "session": session, "c": c}, index=[0]))
# missing = df.loc[(df["c"] < df["c"].max())]
# missingsub = missing[["subject", "session"]].values.tolist()
#
# if len(missing) > 0:
#     raise Exception(missing)
# print(f"\n{len(subjects_sessions)} subjects-sessions\n")
#
#
# ####################################################
# # 3a. prepare flair2d
# bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
# name = "prepare_flair"
# base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")
#
# ####
# # 2D
# acq = "2D"
# out_dir = base_dir / acq / name
# subjects_sessions = get_subject_sessions(bids_dir, acq)
#
# df = pd.DataFrame()
# for subject, session in subjects_sessions:
#     f = f"sub-{subject}/ses-{session}/anat/*nii.gz"
#     c = get_file_counts(out_dir, f)
#     df = df.append(pd.DataFrame({"subject": subject, "session": session, "c": c}, index=[0]))
# missing = df.loc[(df["c"] < df["c"].max())]
# missingsub = missing[["subject", "session"]].values.tolist()
# if len(missing) > 0:
#     raise Exception(missing)
# print(f"\n{len(subjects_sessions)} subjects-sessions\n")
#
#
# ####################################################
# # 3b. prepare flair2d
# bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
# name = "prepare_flair"
# base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")
#
# ####
# # 3D
# acq = "3D"
# out_dir = base_dir / acq / name
# subjects_sessions = get_subject_sessions(bids_dir, acq)
#
# df = pd.DataFrame()
# for subject, session in subjects_sessions:
#     f = f"sub-{subject}/ses-{session}/anat/*nii.gz"
#     c = get_file_counts(out_dir, f)
#     df = df.append(pd.DataFrame({"subject": subject, "session": session, "c": c}, index=[0]))
# missing = df.loc[(df["c"] < df["c"].max())]
# missingsub = missing[["subject", "session"]].values.tolist()
# if len(missing) > 0:
#     raise Exception(missing)
# print(f"\n{len(subjects_sessions)} subjects-sessions\n")

####################################################
# 4a. bianca flair2d
bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
name = "bianca"
base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")

####
# 2D
acq = "2D"
out_dir = base_dir / acq / name
subjects_sessions = get_subject_sessions(bids_dir, acq)

df = pd.DataFrame()
for subject, session in subjects_sessions:
    f = f"sub-{subject}/ses-{session}/anat/*LPM*"
    c = get_file_counts(out_dir, f)
    df = df.append(pd.DataFrame({"subject": subject, "session": session, "c": c}, index=[0]))
missing = df.loc[(df["c"] < df["c"].max())]
missingsub = missing[["subject", "session"]].values.tolist()
if len(missing) > 0:
    raise Exception(missing)
print(f"\n{len(subjects_sessions)} subjects-sessions\n")


####
# 3D
acq = "3D"
out_dir = base_dir / acq / name
subjects_sessions = get_subject_sessions(bids_dir, acq)

df = pd.DataFrame()
for subject, session in subjects_sessions:
    f = f"sub-{subject}/ses-{session}/anat/*LPM*"
    c = get_file_counts(out_dir, f)
    df = df.append(pd.DataFrame({"subject": subject, "session": session, "c": c}, index=[0]))
missing = df.loc[(df["c"] < df["c"].max())]
missingsub = missing[["subject", "session"]].values.tolist()
if len(missing) > 0:
    raise Exception(missing)
print(f"\n{len(subjects_sessions)} subjects-sessions\n")