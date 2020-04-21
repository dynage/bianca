# bianca

## 0. Input data
BIDS formatted with ses level
Freesurfer dir
Training data

## 1. Prepare
creates a folder in {out_dir}/sub-{subject}/ses-{session}/anat/ that includes:

### workflow
* The flair image is bias corrected
* Freesurfer: 
    * export T1w and brain extracted t1w image (T1.mgz, brain.mgz)
    * export WM mask from aparc+aseg.mgz
* register T1w to flair space and apply registration to brain extracted T1w and wm mask
* T1w to MNI registration (12 dof), combine with T1w-to-flair --> flair to MNI registration


### output
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

