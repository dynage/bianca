from nipype.interfaces.base import (TraitedSpec, File, traits)
from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
import os

from bianca import workflows
from pathlib import Path


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


# BiancaOverlapMeasures

# bianca_overlap_measures <lesionmask> <threshold> <manualmask> <saveoutput>
class BiancaOverlapMeasuresInputSpec(FSLCommandInputSpec):
    lesionmask = File(position=0, argstr="%s", exists=True, mandatory=True,
                      desc="LPM lesion mask calculated by BIANCA")
    threshold = traits.Float(position=1, argstr="%s", mandatory=True,
                             desc="threshold that will be applied to <lesionmask> before calculating the overlap ")
    manualmask = File(position=2, argstr="%s", exists=True, mandatory=True,
                      desc="manual mask, used as reference to calculate the overlap measures")

    saveoutput = traits.Int(position=3, argstr="%s", default_value=1, mandatory=True,
                            desc="If <saveoutput> is set to 0 it will output the measures' names "
                                 "and values on the screen  is set to 1 it will save only the values "
                                 "in a file called Overlap_and_Volumes_<lesionmask>_<threshold>.txt")


class BiancaOverlapMeasuresOutputSpec(TraitedSpec):
    out_file = File(desc="overlap measures")


class BiancaOverlapMeasures(FSLCommand):
    from pathlib import Path
    _cmd = "bash bianca_overlap_measures"
    input_spec = BiancaOverlapMeasuresInputSpec
    output_spec = BiancaOverlapMeasuresOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(Path(self.inputs.lesionmask).parent / ("Overlap_and_Volumes_" + Path(
            self.inputs.lesionmask).name.replace(".nii.gz", f"_{self.inputs.threshold}.txt")))
        return outputs


# bianca_overlap_measures <lesionmask> <threshold> <manualmask> <saveoutput>
class BiancaClusterStatsInputSpec(FSLCommandInputSpec):
    bianca_output_map = File(position=0, argstr="%s", exists=True, mandatory=True,
                             desc="LPM lesion mask calculated by BIANCA")
    threshold = traits.Float(position=1, argstr="%s", mandatory=True,
                             desc="threshold that will be applied to <lesionmask> before calculating the overlap ")
    min_cluster_size = traits.Int(position=2, argstr="%s", mandatory=True,
                                  desc="including clusters bigger than <min_cluster_size>")
    mask_file = File(position=3, argstr="%s", exists=True, desc="mask file ")


class BiancaClusterStatsOutputSpec(TraitedSpec):
    out_stat = traits.Any(desc='stats output')


class BiancaClusterStats(FSLCommand):
    _cmd = "bash bianca_cluster_stats"
    input_spec = BiancaClusterStatsInputSpec
    output_spec = BiancaClusterStatsOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        outputs.out_stat = runtime.stdout
        return outputs
