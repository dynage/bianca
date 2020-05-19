from pathlib import Path
from glob import glob
import os


def _format_path(p, subject, session, acq):
    sub_ses = f"sub-{subject}ses-{session}"
    pf = str(p).format(subject=subject, session=session, acq=acq, sub_ses=sub_ses)
    return Path(pf)


def _format_glob_path(p, subject, session, acq, raise_empty=True):
    pf = str(_format_path(p, subject, session, acq))
    files = glob(pf)
    if len(files) > 1:
        raise Exception(f"more than one file found {files}")
    if raise_empty and len(files) == 0:
        raise FileNotFoundError(p)
    if files:
        return Path(files[0])
    else:
        return None


def prepare_locate(flair_dir, bianca_dir, training_data_dir, locate_out_dir, subjects_sessions, acq):
    training_out_dir = locate_out_dir / "training_subjects"
    test_out_dir = locate_out_dir / "test_subjects"
    training_out_dir.mkdir(exist_ok=True, parents=True)
    test_out_dir.mkdir(exist_ok=True, parents=True)

    mapping_manual_labels = (
        training_data_dir / "sub-{subject}_ses-{session}_acq-{acq}_*_FLAIR_mask_goldstandard_new.nii.gz",
        "{sub_ses}_manualmask.nii.gz"
    )
    mapping = [
        (bianca_dir / "*_FLAIR_LPM.nii.gz", "{sub_ses}_BIANCA_LPM.nii.gz"),
        (flair_dir / "*_FLAIR_biascorr.nii.gz", "{sub_ses}_feature_FLAIR.nii.gz"),
        (flair_dir / "*_desc-t1w_brain.nii.gz", "{sub_ses}_feature_t1w.nii.gz"),
        (flair_dir / "*_desc-distanceVent.nii.gz", "{sub_ses}_ventdistmap.nii.gz"),
        (flair_dir / "*_desc-brainmask.nii.gz", "{sub_ses}_brainmask.nii.gz"),
        (flair_dir / "*_desc-wmmask.nii.gz", "{sub_ses}_biancamask.nii.gz")
    ]

    def _create_symlink(f_in, f_out):
        f_in_rel = os.path.relpath(f_in, f_out.parent)
        f_out.symlink_to(f_in_rel)

    for subject, session in subjects_sessions:
        # training subjects
        if _format_glob_path(mapping_manual_labels[0], subject, session, acq, raise_empty=False):
            subject_out_dir = training_out_dir

            f_in = _format_glob_path(mapping_manual_labels[0], subject, session, acq)
            f_out = _format_path(subject_out_dir / mapping_manual_labels[1], subject, session, acq)
            _create_symlink(f_in, f_out)
        # test subjects
        else:
            subject_out_dir = test_out_dir

        for f_in_tpl, f_out_tpl in mapping:
            f_in = _format_glob_path(f_in_tpl, subject, session, acq)
            f_out = _format_path(subject_out_dir / f_out_tpl, subject, session, acq)
            _create_symlink(f_in, f_out)
