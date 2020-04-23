from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath, OutputMultiPath,
                                    Undefined, traits, isdefined)
from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
import os

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
