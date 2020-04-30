# bianca

## 0. Input data
BIDS formatted with ses level
Freesurfer dir
Training data

## Prepare T1w

### workflow


### outputs
creates a folder in {out_dir}/sub-{subject}/ses-{session}/anat/`
that include files to be fed into prepare_flair (among other files):

| file                          | info           |
| -------------                 | -------------|
|*_desc-preproc_T1w.nii.gz      | preprocessed t1w|
|*_desc-brain_T1w.nii.gz        | brain extracted preprocessed t1w|
|*_desc-brain_mask.nii.gz       | brain mask|
|*_desc-bianca_ventmask.nii.gz  | ventricle mask|
|*_desc-bianca_wmmask.nii.gz    | bianca wm mask|
| *_from-T1w_to-MNI_xfm.mat     |12 dof transormation matrix t1w to MNI|

## 2. Prepare FLAIR

### workflow
* The flair image is bias corrected
* bring T1w-space images to flair space
* combine  T1w-to-MNI registration (12 dof) with T1w-to-flair --> flair to MNI registration


### output
creates a folder in {out_dir}/sub-{subject}/ses-{session}/anat/ that includes:

*important for bianca:*


| file                                          | info           |
| -------------                                 | -------------|
| *_acq-3D_run-1_FLAIR_biascorr.nii.gz 		    | biascorrected flair |
| *_desc-12dof_from-{flairSpace}_to-MNI.mat 	| transformation matrix flair space to MNI |
| *_space-{flairSpace}_desc-t1w_brain.nii.gz    | brain extracted t1w in flair space  |
| *_space-{flairSpace}_desc-wmmask.nii.gz	    | wm mask in flair space |

*misc:*

| file                                                  | info           |
| -------------                                         | -------------|
| *_acq-3D_run-1_space-MNI_desc-12dof_FLAIR.nii.gz      | flair in mni space
| *_from-t1w_to-{flairSpace}.mat                        | transformation matrix t1w to flair space |

