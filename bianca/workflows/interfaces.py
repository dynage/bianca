from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath, OutputMultiPath,
                                    Undefined, traits, isdefined)
from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
import os

from bianca import workflows
from pathlib import Path

"""bianca --singlefile=/Users/franzliem/Desktop/bianca/bianca/masterfile.txt 
--brainmaskfeaturenum=2 --labelfeaturenum=3 --matfeaturenum=4 
--trainingnums=all --querysubjectnum=1 --saveclassifierdata=/Users/franzliem/Desktop/bianca/bianca/classifier -v
"""


class BIANCAInputSpec(FSLCommandInputSpec):
    # We use position args here as list indices - so a negative number
    # will put something on the end

    masterfile = File(desc='Masterfile', argstr='--singlefile=%s')

    featuresubset = traits.Str(desc="featuresubset", argstr="--featuresubset=%s")
    brainmaskfeaturenum = traits.Str(desc="brainmaskfeaturenum", argstr="--brainmaskfeaturenum=%s")
    labelfeaturenum = traits.Str(desc="labelfeaturenum", argstr="--labelfeaturenum=%s")
    matfeaturenum = traits.Str(desc="matfeaturenum", argstr="--matfeaturenum=%s")

    trainingnums = traits.Str(desc="trainingnums", default_value="all", argstr="--trainingnums=%s")
    querysubjectnum = traits.Int(desc="querysubjectnum", argstr="--querysubjectnum=%s")
    verbose = traits.Bool(desc='verbose', argstr='-v', default_value=True)

    save_classifier = traits.Bool(argstr='--saveclassifierdata classifier', desc="save classifier to file",
                                  default_value=False)
    trained_classifier_file = traits.Str(desc="trained_classifier_file for loadclassifierdata",
                                         argstr="--loadclassifierdata=%s")


class BIANCAOutputSpec(TraitedSpec):
    out_file = File(desc="bianca output mask")
    classifier_file = File(desc="file with classifier")
    classifier_labels_file = File(desc="classifier labels")


class BIANCA(FSLCommand):
    _cmd = 'bianca'  # ''
    input_spec = BIANCAInputSpec
    output_spec = BIANCAOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath("output_bianca.nii.gz")
        outputs['classifier_file'] = os.path.abspath("classifier")
        outputs['classifier_labels_file'] = os.path.abspath("classifier_labels")
        return outputs


"""
 make_bianca_mask <structural_image> <CSF pve> <warp_file_MNI2structural> <keep_intermediate_files>
 expects 
 brain extracted image would be called <structural image>_brain.nii.gz
 + ${strucimg}_brain_mask.nii.gz
 Output: the script creates two files called <structural image>_bianca_mask.nii.gz , <structural image>_ventmask.nii.gz
 
 <structural_image> <CSF pve> <warp_file_MNI2structural> <keep_intermediate_files>
  <structural_image_brainextracted> <brainmask>"
  
 """


class MakeBiancaMaskInputSpec(FSLCommandInputSpec):
    structural_image = File(position=0, argstr="%s", exists=True, mandatory=True, desc="non-extracted t1w")
    CSF_pve = File(position=1, argstr="%s", exists=True, mandatory=True, desc="CSF pve")
    warp_file_MNI2structural = File(position=2, argstr="%s", exists=True, mandatory=True, desc="FNIRT warp")
    keep_intermediate_files = traits.Int(position=3, argstr="%s", mandatory=True, desc="0: no, 1: yes")
    structural_image_brainextracted = File(
        position=4, argstr="%s", exists=True, mandatory=True, desc="brain extracted t1w")
    brainmask = File(position=5, argstr="%s", exists=True, mandatory=True, desc="brian mask")


class MakeBiancaMaskOutputSpec(TraitedSpec):
    mask_file = File(desc="bianca output mask")
    vent_file = File(desc="ventricle mask")


class MakeBiancaMask(FSLCommand):
    exec = str(Path(workflows.__file__).parent / "make_bianca_mask_nipypefriendly")
    _cmd = f"bash {exec}"
    input_spec = MakeBiancaMaskInputSpec
    output_spec = MakeBiancaMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['mask_file'] = os.path.abspath("out_bianca_mask.nii.gz")
        outputs['vent_file'] = os.path.abspath("out_ventmask.nii.gz")
        return outputs
