from pathlib import Path

from nipype.pipeline import engine as pe
from nipype import Workflow

from nipype.interfaces import utility as niu, fsl, io, ants
from niworkflows.interfaces.images import ValidateImage
# from niworkflows.utils.misc import fix_multi_T1w_source_name, add_suffix
from niworkflows.anat.ants import init_brain_extraction_wf

import smriprep
from smriprep.workflows.anatomical import init_anat_template_wf
from smriprep.workflows.outputs import _apply_default_bids_lut

import niworkflows
from niworkflows.utils.spaces import Reference
from niworkflows.interfaces.bids import DerivativesDataSink

from .interfaces import MakeBiancaMask
from ..utils import export_version
from warnings import warn


def get_t1w(bids_dir, subject, session):
    t1w_files = list(Path(bids_dir).glob(f"sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_*_T1w.nii.gz"))
    assert len(t1w_files) > 0, f"Expected at least one file, but found {t1w_files}"
    return t1w_files


def _check_versions():
    if smriprep.__version__ != '0.5.2':
        warn(f"tested with smriprep version 0.5.2. but {smriprep.__version__} is installed")

    if niworkflows.__version__ != '1.1.12':
        warn(f"tested with niworkflows version 0.5.2. but {niworkflows.__version__} is installed")


def prepare_t1w(bids_dir, out_dir, wd_dir, crash_dir, info_tpls, n_cpu=1, omp_nthreads=1, run_wf=True, graph=False):
    _check_versions()
    export_version(out_dir)

    out_dir.mkdir(exist_ok=True, parents=True)

    wf = Workflow(name="meta_prepare_t1")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    for subject, session in info_tpls:
        t1w_files = get_t1w(bids_dir, subject, session)
        name = f"anat_preproc_{subject}_{session}"
        single_ses_wf = init_single_ses_anat_preproc_wf(subject=subject,
                                                        session=session,
                                                        t1w=t1w_files,
                                                        bids_dir=bids_dir,
                                                        out_dir=out_dir,
                                                        name=name,
                                                        omp_nthreads=omp_nthreads)
        wf.add_nodes([single_ses_wf])
    if graph:
        wf.write_graph("workflow_graph.png", graph2use="exec")
        wf.write_graph("workflow_graph_c.png", graph2use="colored")
    if run_wf:
        wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})


def _pop(inlist):
    if isinstance(inlist, (list, tuple)):
        return inlist[0]
    return inlist


def init_single_ses_anat_preproc_wf(subject,
                                    session,
                                    t1w,
                                    bids_dir,
                                    out_dir,
                                    omp_nthreads=1,
                                    name='anat_preproc_wf'):
    """
    This is based on the smriprep workflow.
    Changes:
    - it creates a session template (averaging all t1w of a session)
    - it normalizes using FNIRT
    - it runs make_bianca_mask
    """
    wf = Workflow(name=name)

    # 1. Anatomical reference generation - average input T1w images.
    num_t1w = len(t1w)
    anat_template_wf = init_anat_template_wf(longitudinal=False, omp_nthreads=omp_nthreads, num_t1w=num_t1w)
    anat_template_wf.inputs.inputnode.t1w = t1w

    anat_validate = pe.Node(ValidateImage(), name='anat_validate', run_without_submitting=True)
    wf.connect(anat_template_wf, 'outputnode.t1w_ref', anat_validate, 'in_file')

    # 2. Brain-extraction and INU (bias field) correction.
    brain_extraction_wf = init_brain_extraction_wf(
        in_template=Reference.from_string("OASIS30ANTs")[0].space,
        template_spec=Reference.from_string("OASIS30ANTs")[0].spec,
        atropos_use_random_seed=True,
        omp_nthreads=omp_nthreads,
        normalization_quality='precise')
    wf.connect(anat_validate, 'out_file', brain_extraction_wf, 'inputnode.in_files')

    buffernode = pe.Node(niu.IdentityInterface(fields=['t1w', 't1w_brain', 't1w_mask']), name='buffernode')
    wf.connect(brain_extraction_wf, 'outputnode.bias_corrected', buffernode, 't1w')
    wf.connect(brain_extraction_wf, ('outputnode.out_file', _pop), buffernode, 't1w_brain')
    wf.connect(brain_extraction_wf, 'outputnode.out_mask', buffernode, 't1w_mask')

    # 3. Brain tissue segmentation
    t1w_dseg = pe.Node(fsl.FAST(segments=True, no_bias=True, probability_maps=True), name='t1w_dseg', mem_gb=3)
    wf.connect(buffernode, 't1w_brain', t1w_dseg, 'in_files')

    norm_wf = get_norm_wf()
    wf.connect(buffernode, 't1w', norm_wf, "inputnode.t1w")
    wf.connect(buffernode, 't1w_brain', norm_wf, "inputnode.t1w_brain")

    MNI_2_t1w_warp = pe.Node(fsl.InvWarp(), name='MNI_2_t1w_warp')
    wf.connect(buffernode, 't1w', MNI_2_t1w_warp, 'reference')
    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_warp', MNI_2_t1w_warp, 'warp')

    bianca_mask = pe.Node(MakeBiancaMask(), name='bianca_mask')
    bianca_mask.inputs.keep_intermediate_files = 0

    wf.connect(buffernode, 't1w', bianca_mask, 'structural_image')
    wf.connect(t1w_dseg, ('partial_volume_files', _pop), bianca_mask, 'CSF_pve')
    wf.connect(MNI_2_t1w_warp, 'inverse_warp', bianca_mask, 'warp_file_MNI2structural')
    wf.connect(buffernode, 't1w_brain', bianca_mask, 'structural_image_brainextracted')
    wf.connect(buffernode, 't1w_mask', bianca_mask, 'brainmask')

    # distancemap
    distancemap = pe.Node(fsl.DistanceMap(), name="distancemap")
    wf.connect(bianca_mask, 'vent_file', distancemap, "in_file")
    wf.connect(buffernode, 't1w_mask', distancemap, "mask_file")

    perivent_mask = pe.Node(fsl.maths.MathsCommand(), name="perivent_mask")
    perivent_mask.inputs.args = "-uthr 10 -bin"
    wf.connect(distancemap, "distance_map", perivent_mask, "in_file")

    deepWM_mask = pe.Node(fsl.maths.MathsCommand(), name="deepWM_mask")
    deepWM_mask.inputs.args = "-thr 10 -bin"
    wf.connect(distancemap, "distance_map", deepWM_mask, "in_file")

    ds = init_anat_derivatives_wf(bids_dir, out_dir)
    ds.inputs.inputnode.subject = subject
    ds.inputs.inputnode.session = session

    wf.connect(buffernode, 't1w', ds, 'inputnode.t1w_preproc')
    wf.connect(buffernode, 't1w_brain', ds, 'inputnode.t1w_brain')
    wf.connect(buffernode, 't1w_mask', ds, 'inputnode.t1w_mask')

    wf.connect(t1w_dseg, 'tissue_class_map', ds, 'inputnode.t1w_dseg')
    wf.connect(t1w_dseg, 'probability_maps', ds, 'inputnode.t1w_tpms')

    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_warp', ds, 'inputnode.t1w_2_MNI_warp')
    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_mat', ds, 'inputnode.t1w_2_MNI_xfm')
    wf.connect(norm_wf, 'outputnode.t1w_MNIspace', ds, 'inputnode.t1w_MNIspace')

    wf.connect(bianca_mask, 'mask_file', ds, 'inputnode.bianca_wm_mask_file')
    wf.connect(bianca_mask, 'vent_file', ds, 'inputnode.bianca_vent_mask_file')
    wf.connect(distancemap, "distance_map", ds, 'inputnode.distance_map')
    wf.connect(perivent_mask, "out_file", ds, 'inputnode.perivent_mask')
    wf.connect(deepWM_mask, "out_file", ds, 'inputnode.deepWM_mask')
    return wf


def init_anat_derivatives_wf(bids_root, output_dir, name='anat_derivatives_wf'):
    """Set up a battery of datasinks to store derivatives in the right location."""
    base_directory = str(output_dir.parent)
    out_path_base = str(output_dir.name)

    wf = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['subject', 'session', 't1w_preproc', 't1w_brain', 't1w_mask', 't1w_dseg', 't1w_tpms',
                    't1w_2_MNI_xfm', 't1w_2_MNI_warp', 't1w_MNIspace', 'bianca_wm_mask_file', 'bianca_vent_mask_file',
                    "distance_map", "perivent_mask", "deepWM_mask"
                    ]),
        name='inputnode')

    def generic_bids_file_fct(bids_root, subject, session):
        from pathlib import Path
        return Path(bids_root) / f"sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w.nii.gz"

    generic_bids_file = pe.Node(niu.Function(
        input_names=["bids_root", "subject", "session"],
        output_names=["out_file"],
        function=generic_bids_file_fct), name='generic_bids_file')
    generic_bids_file.inputs.bids_root = bids_root
    wf.connect(inputnode, "subject", generic_bids_file, "subject")
    wf.connect(inputnode, "session", generic_bids_file, "session")

    ds_t1w_preproc = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='preproc',
                            keep_dtype=True, compress=True),
        name='ds_t1w_preproc', run_without_submitting=True)
    ds_t1w_preproc.inputs.SkullStripped = False
    wf.connect(generic_bids_file, "out_file", ds_t1w_preproc, "source_file")
    wf.connect(inputnode, "t1w_preproc", ds_t1w_preproc, "in_file")

    ds_t1w_brain = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='brain',
                            keep_dtype=True, compress=True),
        name='ds_t1w_brain', run_without_submitting=True)
    ds_t1w_brain.inputs.SkullStripped = True
    wf.connect(generic_bids_file, "out_file", ds_t1w_brain, "source_file")
    wf.connect(inputnode, "t1w_brain", ds_t1w_brain, "in_file")

    ds_t1w_mask = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='brain', suffix='mask',
                            compress=True), name='ds_t1w_mask', run_without_submitting=True)
    ds_t1w_mask.inputs.Type = 'Brain'
    wf.connect(generic_bids_file, "out_file", ds_t1w_mask, "source_file")
    wf.connect(inputnode, "t1w_mask", ds_t1w_mask, "in_file")

    lut_t1w_dseg = pe.Node(niu.Function(function=_apply_default_bids_lut),
                           name='lut_t1w_dseg')
    wf.connect(inputnode, "t1w_dseg", lut_t1w_dseg, "in_file")

    ds_t1w_dseg = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, suffix='dseg', compress=True),
        name='ds_t1w_dseg', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_dseg, "source_file")
    wf.connect(lut_t1w_dseg, 'out', ds_t1w_dseg, 'in_file')

    ds_t1w_tpms = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, suffix='probseg',
                            compress=True),
        name='ds_t1w_tpms', run_without_submitting=True)
    ds_t1w_tpms.inputs.extra_values = ['label-CSF', 'label-GM', 'label-WM']
    wf.connect(generic_bids_file, "out_file", ds_t1w_tpms, "source_file")
    wf.connect(inputnode, "t1w_tpms", ds_t1w_tpms, "in_file")

    # Bianca masks
    ds_bianca_wm_mask = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='bianca', suffix='wmmask',
                            compress=True), name='ds_bianca_wm_mask', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_bianca_wm_mask, "source_file")
    wf.connect(inputnode, "bianca_wm_mask_file", ds_bianca_wm_mask, "in_file")

    ds_bianca_vent_mask = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='bianca',
                            suffix='ventmask', compress=True), name='ds_bianca_vent_mask', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_bianca_vent_mask, "source_file")
    wf.connect(inputnode, "bianca_vent_mask_file", ds_bianca_vent_mask, "in_file")

    ds_distance_map = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='bianca',
                            suffix='ventdistmap', compress=True), name='ds_distance_map', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_distance_map, "source_file")
    wf.connect(inputnode, "distance_map", ds_distance_map, "in_file")

    ds_perivent_mask = pe.Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                               name="ds_perivent_mask")
    ds_perivent_mask.inputs.desc = "periventmask"
    wf.connect(generic_bids_file, "out_file", ds_perivent_mask, "source_file")
    wf.connect(inputnode, "perivent_mask", ds_perivent_mask, "in_file")

    ds_deepWM_mask = pe.Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                             name="ds_deepWM_mask")
    ds_deepWM_mask.inputs.desc = "deepWMmask"
    wf.connect(generic_bids_file, "out_file", ds_deepWM_mask, "source_file")
    wf.connect(inputnode, "deepWM_mask", ds_deepWM_mask, "in_file")

    # MNI
    ds_t1w_to_MNI_xfm = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                            allowed_entities=['from', 'to'], suffix='xfm', **{'from': 'T1w', 'to': 'MNI'}),
        name='ds_t1w_to_MNI_xfm', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_to_MNI_xfm, "source_file")
    wf.connect(inputnode, "t1w_2_MNI_xfm", ds_t1w_to_MNI_xfm, "in_file")

    ds_t1w_to_MNI_warp = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                            allowed_entities=['from', 'to'], suffix='warpfield', **{'from': 'T1w', 'to': 'MNI'}),
        name='ds_t1w_to_MNI_warp', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_to_MNI_warp, "source_file")
    wf.connect(inputnode, "t1w_2_MNI_warp", ds_t1w_to_MNI_warp, "in_file")

    df_t1w_MNIspace = pe.Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                                                  space="MNI", desc="warped2mm"),
                              name="df_t1w_MNIspace")
    wf.connect(generic_bids_file, "out_file", df_t1w_MNIspace, "source_file")
    wf.connect(inputnode, "t1w_MNIspace", df_t1w_MNIspace, "in_file")
    return wf


def get_norm_wf(name="norm_wf"):
    wf = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['t1w', 't1w_brain']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['t1w_2_MNI_mat', 't1w_2_MNI_warp', 't1w_MNIspace']),
                         name='outputnode')

    t1w_2_MNI_flirt = pe.Node(fsl.FLIRT(dof=12), name='t1w_2_MNI_flirt')
    t1w_2_MNI_flirt.inputs.reference = fsl.Info.standard_image('MNI152_T1_1mm_brain.nii.gz')
    wf.connect(inputnode, 't1w_brain', t1w_2_MNI_flirt, 'in_file')
    wf.connect(t1w_2_MNI_flirt, 'out_matrix_file', outputnode, 't1w_2_MNI_mat')

    # 2. CALC. WARP STRUCT -> MNI with FNIRT
    # cf. wrt. 2mm
    # https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=ind1311&L=FSL&P=R86108&1=FSL&9=A&J=on&d=No+Match%3BMatch%3BMatches&z=4
    t1w_2_MNI_fnirt = pe.Node(fsl.FNIRT(), name='t1w_2_MNI_fnirt')
    t1w_2_MNI_fnirt.inputs.config_file = 'T1_2_MNI152_2mm'
    t1w_2_MNI_fnirt.inputs.ref_file = fsl.Info.standard_image('MNI152_T1_2mm.nii.gz')
    t1w_2_MNI_fnirt.inputs.field_file = True
    t1w_2_MNI_fnirt.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(inputnode, 't1w', t1w_2_MNI_fnirt, 'in_file')
    wf.connect(t1w_2_MNI_flirt, 'out_matrix_file', t1w_2_MNI_fnirt, 'affine_file')

    wf.connect(t1w_2_MNI_fnirt, 'field_file', outputnode, 't1w_2_MNI_warp')
    wf.connect(t1w_2_MNI_fnirt, 'warped_file', outputnode, 't1w_MNIspace')
    return wf
