import pandas as pd
from pathlib import Path
import subprocess
from bianca import __version__


def get_subject_sessions(bids_dir, flair_acq):
    def _get_suse_from_path(p):
        session = p.parents[1].name.replace("ses-", "")
        subject = p.parents[2].name.replace("sub-", "")
        return subject, session

    flair_files = list(Path(bids_dir).glob(f"sub-*/ses-*/anat/*_acq-{flair_acq}_*_FLAIR.nii.gz"))
    t1w_files = list(Path(bids_dir).glob(f"sub-*/ses-*/anat/*_T1w.nii.gz"))
    flair_suse = set([_get_suse_from_path(p) for p in flair_files])
    t1w_suse = set([_get_suse_from_path(p) for p in t1w_files])
    subject_sessions = list(flair_suse & t1w_suse)
    subject_sessions.sort()
    return subject_sessions


def export_version(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        version_label = subprocess.check_output(["git", "describe", "--tags"]).strip()
        (out_dir / "pipeline_version.txt").write_text(f"git: {version_label.decode()}")
    except:
        (out_dir / "pipeline_version.txt").write_text(__version__)


def create_masterfile(prep_dir, training_data_dir, bianca_dir, flair_tmpl, t1w_tmpl, manual_mask_tmpl,
                      mat_tmpl):
    bianca_dir.mkdir(exist_ok=True, parents=True)

    # get flair files
    flair_globs = list(prep_dir.glob(flair_tmpl.format(subject="*", session="*")))
    print(f"{len(flair_globs)} flair files found")

    # get remaining files
    df = pd.DataFrame({"flair": [str(f) for f in flair_globs]})
    df["subject"] = df.flair.str.split("sub-").str[1].str.split("/").str[0]
    df["session"] = df.flair.str.split("ses-").str[1].str.split("/").str[0]

    complete_files = {"t1w": str(prep_dir / t1w_tmpl),
                      "manual_mask": str(training_data_dir / manual_mask_tmpl),
                      "mat": str(prep_dir / mat_tmpl)
                      }
    for var in complete_files.keys():
        df[var] = None
    for i in range(len(df)):
        for var in complete_files.keys():
            df[var].iloc[i] = complete_files[var].format(**df.iloc[i])

    df = df[['flair', 't1w', 'manual_mask', 'mat', 'subject', 'session']]

    # only include masks from training subjects
    training_subject_index = df.manual_mask.apply(lambda s: Path(s).is_file())
    df.loc[~training_subject_index, "manual_mask"] = None
    training_subjects = df[training_subject_index]

    # check if files exist
    files = df[['flair', 't1w', 'manual_mask', 'mat']].melt()["value"].to_list()
    for f in files:
        if f:
            assert Path(f).is_file(), f"{f} is missing"

    # save
    df.to_csv(bianca_dir / "masterfile.txt", index=False, header=False, sep=" ")
    df.to_csv(bianca_dir / "masterfile_wHeader.txt", index=False, sep=" ")
    training_subjects.to_csv(bianca_dir / "masterfile_training_subjects.txt", index=False, sep=" ")
