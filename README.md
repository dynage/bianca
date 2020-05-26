# bianca

# Input data
BIDS formatted with ses level
Freesurfer dir
Training data


# Workflows
1. Prepare template: uses smriprep-preprocessed template and creates distancemap and masks in template space of each
 subject
1. Prepare T1w: Brings session T1w image into template space
1. Prepare FLAIR: Brings t1w, distancemap and masks from template space into flair space. Runs biascorrection on 
flair images.
1. Prepare Masterfile
1. Run Bianca

## 1. Prepare template

### workflow

Uses smriprep template to generate bianca masks and distancemap. 


* smriprep t1w template is normalized with fsl
* results + CSF-pve are fed to `MakeBiancaMask`
* resulting ventricle mask is fed to `distancemap`
* distancemap is thresholded into perivent and deep WM (cut-off = 10mm)

### outputs
creates a folder in `prepare_template/sub-{subject}/anat/`
All outputs (except space-MNI) are in smriprep template space.

|  file                              | info                                          |
|  -------------                     | -------------                                 |
| _desc-bianca_ventdistmap.nii.gz    | distancemap from ventricles                   |
| _desc-bianca_ventmask.nii.gz       | ventricle mask (MakeBiancaMask)               |
| _desc-bianca_wmmask.nii.gz         | WM Mask  (MakeBiancaMask)                     |
| _desc-brain_mask.nii.gz            | smriprep brain mask                           |
| _desc-deepWMmask.nii.gz            | deep WM mask                                  |
| _desc-periventmask.nii.gz          | periventricular mask                          |
| _desc-preproc_T1w.nii.gz           | preprocessed smriprep template                |
| _from-tpl_to-MNI_warpfield.nii.gz  | warp from template to MNI                     |
| _from-tpl_to-MNI_xfm.mat           | transformation matrix from template to MNI    |
| _space-MNI_desc-warped2mm.nii.gz   | template in MNI space                         |



## 2. Prepare T1w

### workflow
Bias corrects session T1w images, brings them to template space and averages them.

### outputs
creates a folder in `prepare_t1w/sub-{subject}/ses-{session}/anat/`
that include files to be fed into prepare_flair (among other files):

|  file                              | info                              |
|  -------------                     | -------------                     |
| _space-tpl_T1w.nii.gz              | preprocessed t1w                  |
| space-tpl_desc-brain_T1w.nii.gz    | brain extracted preprocessed t1w  |


## 3. Prepare FLAIR


### workflow
* The flair image is bias corrected
* bring template-space images to flair space
* combine  T1w-to-MNI registration (12 dof) with tpl-to-flair --> flair to MNI registration


### output
creates a folder in `prepare_flair/{acq}/sub-{subject}/ses-{session}/anat/` that includes:

*for bianca:*

| file                                          | info                                      | LOCATE                                                |
| -------------                                 | -------------                             |-------------                                          |
| _FLAIR_biascorr.nii.gz 		                | biascorrected flair                       | <subject_name>_feature_<base_modality_name>.nii.gz    |
| _desc-12dof_from-{flairSpace}_to-MNI.mat  	| transformation matrix flair space to MNI  |                                                       |
| _space-{flairSpace}_desc-t1w_brain.nii.gz     | brain extracted t1w in flair space        | <subject_name>_feature_<modality_name>.nii.gz         |
| _space-{flairSpace}_desc-wmmask.nii.gz	    | wm mask in flair space                    |                                                       |


*for LOCATE:*

| file                                          | info                      | LOCATE                            |
| -------------                                 | -------------             |-------------                      |
| _space-{flairSpace}_desc-distanceVent.nii.gz  | ventricular distance map  | <subject_name>_ventdistmap.nii.gz |
| _space-{flairSpace}_desc-brainmask.nii.gz     | brainmask                 | <subject_name>_brainmask.nii.gz   |
| _space-{flairSpace}_desc-wmmask.nii.gz        | wm mask                   | <subject_name>_biancamask.nii.gz  |


*misc:*

| file                                          | info                                          |
| -------------                                 | -------------                                 |
| _space-MNI_desc-12dof_FLAIR.nii.gz            | flair in mni space                            |
| _from-t1w_to-{flairSpace}.mat                 | transformation matrix t1w-tpl to flair space  |
| _space-{flairSpace}_desc-deepWMmask.nii.gz    | deep WM mask                                  |
| _space-{flairSpace}_desc-periventmask.nii.gz  | periventricular WM mask                       |


## 4. Prepare Masterfile
Creates a masterfile for bianca in `{acq}/bianca`

## 5. Run Bianca

### workflow
Runs bianca.

### output

| file                      | info                          | LOCATE                            |
| -------------             | -------------                 |-------------                      |
| _FLAIR_LPM.nii.gz         | bianca lesion prob. mask      | <subject_name>_BIANCA_LPM.nii.gz  |
| _FLAIR_LPM.json           | LPM information               |                                   |
| _FLAIR_classifier         | classifier (if saved)         |                                   |
| _FLAIR_classifier_labels  | classifier labels (if saved)  |                                   |


LOCATE also needs the <subject_name>_manualmask.nii.gz


## 6. prepare locate
names files that can be used for locate (symlinks)

## 7. bianca threshold
### workflow

masks bianca LPM with bianca-wm-mask and applies threshold(s).
Runs `bianca_cluster_stats`

if `run_BiancaOverlapMeasures=True`, runs `bianca_overlap_measures` vs manual masks

### output
| file                                                          | info                                                                                              |
| -------------                                                 | -------------                                                                                     |
| _FLAIR_desc-biancamasked.nii.gz                               | bianca LPM masked with bianca-wm-mask                                                             |
| _FLAIR_desc-thresh{threshold}_biancaLPMmaskedThrBin.nii.gz    | bianca LPM masked with bianca-wm-mask, thresholdedand binarized                                   |
| _FLAIR_desc-thresh{threshold}_ClusterStatsTotal.txt           | output of `bianca_cluster_stats` bianca LPM masked with bianca-wm-mask                            |
| _FLAIR_desc-thresh{threshold}_ClusterStatsdeepwm.txt          | output of `bianca_cluster_stats` within deep wm mask (bianca LPM masked with bianca-wm-mask)      |
| _FLAIR_desc-thresh{threshold}_ClusterStatsperventwm.txt       | output of `bianca_cluster_stats` within perivent wm mask (bianca LPM masked with bianca-wm-mask)  |
| _FLAIR_desc-thresh{threshold}_overlap.txt                     | output of `bianca_overlap_measures` (bianca LPM masked with bianca-wm-mask)                       |

## 8. Post-locate-masking

takes binary outputs from locate and applies bianca-wm-mask again 
(due to some resampling within locate, locate labels some voxels outside the bianca-wm-mask).
