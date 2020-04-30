from pathlib import Path
from bianca.utils import create_masterfile

training_data_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/masks_training_data")
prep_name = "prepare_flair"
name = "bianca"

####
# 2D
acq = "2D"
space = "flair2D"
base_dir = Path(f"/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")

prep_dir = base_dir / prep_name
bianca_dir = base_dir / name

flair_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_acq-" + acq + "_*_FLAIR_biascorr.nii.gz"
t1w_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_space-" + space + "_desc-t1w_brain.nii.gz"
manual_mask_tmpl = "sub-{subject}/ses-{session}/sub-{subject}_ses-{session}_acq-" + acq + "_run-1_FLAIR_mask_goldstandard_new.nii.gz"
mat_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_desc-12dof_from-" + space + "_to-MNI.mat"

create_masterfile(prep_dir, training_data_dir, bianca_dir,
                  flair_tmpl=flair_tmpl,
                  t1w_tmpl=t1w_tmpl,
                  manual_mask_tmpl=manual_mask_tmpl,
                  mat_tmpl=mat_tmpl)

####
# 3D
acq = "3D"
space = "flair3D"
base_dir = Path(f"/home/fliem/lhab_collaboration/WMH/BIANCA/training_subjects/{acq}")

prep_dir = base_dir / prep_name
bianca_dir = base_dir / name

flair_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_acq-" + acq + "_*_FLAIR_biascorr.nii.gz"
t1w_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_space-" + space + "_desc-t1w_brain.nii.gz"
manual_mask_tmpl = "sub-{subject}/ses-{session}/sub-{subject}_ses-{session}_acq-" + acq + "_run-1_FLAIR_mask_goldstandard_new.nii.gz"
mat_tmpl = "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_desc-12dof_from-" + space + "_to-MNI.mat"

create_masterfile(prep_dir, training_data_dir, bianca_dir,
                  flair_tmpl=flair_tmpl,
                  t1w_tmpl=t1w_tmpl,
                  manual_mask_tmpl=manual_mask_tmpl,
                  mat_tmpl=mat_tmpl)
