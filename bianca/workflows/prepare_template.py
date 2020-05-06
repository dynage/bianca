from nipype.pipeline import engine as pe
from nipype import Workflow
from nipype.interfaces import utility as niu, fsl
from niworkflows.interfaces.bids import DerivativesDataSink
from .interfaces import MakeBiancaMask
from ..utils import export_version


def prepare_template(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, subjects, n_cpu=1, omp_nthreads=1,
                     run_wf=True, graph=False):
    export_version(out_dir)

    out_dir.mkdir(exist_ok=True, parents=True)

    wf = Workflow(name="meta_prepare_template")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    infosource = pe.Node(niu.IdentityInterface(fields=["subject"]), name="infosource")
    infosource.iterables = [("subject", subjects)
                            ]

    def subject_info_fnc(smriprep_dir, subject):
        from pathlib import Path
        tpl_t1w = Path(smriprep_dir, f"sub-{subject}/anat/sub-{subject}_T1w_preproc.nii.gz")
        tpl_t1w_brainmask = Path(smriprep_dir, f"sub-{subject}/anat/sub-{subject}_T1w_brainmask.nii.gz")
        CSF_pve = Path(smriprep_dir, f"sub-{subject}/anat/sub-{subject}_T1w_class-CSF_probtissue.nii.gz")

        out_list = [tpl_t1w, tpl_t1w_brainmask, CSF_pve]
        for f in out_list:
            if not f.is_file():
                raise FileNotFoundError(f)
        return [str(o) for o in out_list]  # as Path is not taken everywhere

    grabber = pe.Node(niu.Function(input_names=["smriprep_dir", "subject"],
                                   output_names=["tpl_t1w", "tpl_t1w_brainmask", "CSF_pve"],
                                   function=subject_info_fnc),
                      name="grabber"
                      )
    grabber.inputs.smriprep_dir = smriprep_dir
    wf.connect(infosource, "subject", grabber, "subject")

    prepare_template = prepare_template_wf()
    wf.connect(grabber, "tpl_t1w", prepare_template, "inputnode.tpl_t1w")
    wf.connect(grabber, "tpl_t1w_brainmask", prepare_template, "inputnode.tpl_t1w_brainmask")
    wf.connect(grabber, "CSF_pve", prepare_template, "inputnode.CSF_pve")

    ds = init_template_derivatives_wf(bids_dir, out_dir)

    wf.connect([
        (infosource, ds, [("subject", "inputnode.subject")]),
        (grabber, ds, [
            ("tpl_t1w", "inputnode.t1w_preproc"),
            ("tpl_t1w_brainmask", "inputnode.t1w_mask"),
        ]),
        (prepare_template, ds, [
            ("outputnode.t1w_MNIspace", "inputnode.t1w_MNIspace"),
            ("outputnode.t1w_2_MNI_mat", "inputnode.t1w_2_MNI_xfm"),
            ("outputnode.t1w_2_MNI_warp", "inputnode.t1w_2_MNI_warp"),
            ("outputnode.bianca_wm_mask_file", "inputnode.bianca_wm_mask_file"),
            ("outputnode.vent_file", "inputnode.bianca_vent_mask_file"),
            ("outputnode.distance_map", "inputnode.distance_map"),
            ("outputnode.perivent_mask", "inputnode.perivent_mask"),
            ("outputnode.deepWM_mask", "inputnode.deepWM_mask")
        ]
         )
    ]
    )

    if graph:
        wf.write_graph("workflow_graph.png", graph2use="exec")
        wf.write_graph("workflow_graph_c.png", graph2use="colored")
    if run_wf:
        wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})


def init_template_derivatives_wf(bids_root, output_dir, name='template_derivatives_wf'):
    """Set up a battery of datasinks to store derivatives in the right location."""
    base_directory = str(output_dir.parent)
    out_path_base = str(output_dir.name)

    wf = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['subject', 't1w_preproc', 't1w_mask', 't1w_2_MNI_xfm', 't1w_2_MNI_warp',
                    't1w_MNIspace', 'bianca_wm_mask_file', 'bianca_vent_mask_file', "distance_map", "perivent_mask",
                    "deepWM_mask"
                    ]),
        name='inputnode')

    def generic_bids_file_fct(bids_root, subject):
        from pathlib import Path
        return Path(bids_root) / f"sub-{subject}/anat/sub-{subject}_T1w.nii.gz"

    generic_bids_file = pe.Node(niu.Function(
        input_names=["bids_root", "subject"],
        output_names=["out_file"],
        function=generic_bids_file_fct), name='generic_bids_file')
    generic_bids_file.inputs.bids_root = bids_root
    wf.connect(inputnode, "subject", generic_bids_file, "subject")

    ds_t1w_preproc = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='preproc',
                            keep_dtype=True, compress=True),
        name='ds_t1w_preproc', run_without_submitting=True)
    ds_t1w_preproc.inputs.SkullStripped = False
    wf.connect(generic_bids_file, "out_file", ds_t1w_preproc, "source_file")
    wf.connect(inputnode, "t1w_preproc", ds_t1w_preproc, "in_file")

    ds_t1w_mask = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, desc='brain', suffix='mask',
                            compress=True), name='ds_t1w_mask', run_without_submitting=True)
    ds_t1w_mask.inputs.Type = 'Brain'
    wf.connect(generic_bids_file, "out_file", ds_t1w_mask, "source_file")
    wf.connect(inputnode, "t1w_mask", ds_t1w_mask, "in_file")

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
    ds_t1w_to_MNI_warp = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                            allowed_entities=['from', 'to'], suffix='warpfield', **{'from': 'tpl', 'to': 'MNI'}),
        name='ds_t1w_to_MNI_warp', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_to_MNI_warp, "source_file")
    wf.connect(inputnode, "t1w_2_MNI_warp", ds_t1w_to_MNI_warp, "in_file")

    df_t1w_MNIspace = pe.Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                                                  space="MNI", desc="warped2mm"),
                              name="df_t1w_MNIspace")
    wf.connect(generic_bids_file, "out_file", df_t1w_MNIspace, "source_file")
    wf.connect(inputnode, "t1w_MNIspace", df_t1w_MNIspace, "in_file")

    ds_t1w_to_MNI_xfm = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                            allowed_entities=['from', 'to'], suffix='xfm', **{'from': 'tpl', 'to': 'MNI'}),
        name='ds_t1w_to_MNI_xfm', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_to_MNI_xfm, "source_file")
    wf.connect(inputnode, "t1w_2_MNI_xfm", ds_t1w_to_MNI_xfm, "in_file")

    return wf


def prepare_template_wf(name="prepare_template"):
    wf = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['tpl_t1w', 'tpl_t1w_brainmask', 'CSF_pve']),
                        name='inputnode')

    tpl_t1w_brain = pe.Node(fsl.ApplyMask(), name='tpl_t1w_brain')
    wf.connect(inputnode, "tpl_t1w", tpl_t1w_brain, "in_file")
    wf.connect(inputnode, "tpl_t1w_brainmask", tpl_t1w_brain, "mask_file")

    norm_wf = get_norm_wf()
    wf.connect(inputnode, 'tpl_t1w', norm_wf, "inputnode.t1w")
    wf.connect(tpl_t1w_brain, 'out_file', norm_wf, "inputnode.t1w_brain")

    MNI_2_t1w_warp = pe.Node(fsl.InvWarp(), name='MNI_2_t1w_warp')
    wf.connect(inputnode, 'tpl_t1w', MNI_2_t1w_warp, 'reference')
    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_warp', MNI_2_t1w_warp, 'warp')

    bianca_mask = pe.Node(MakeBiancaMask(), name='bianca_mask')
    bianca_mask.inputs.keep_intermediate_files = 0

    wf.connect(inputnode, 'tpl_t1w', bianca_mask, 'structural_image')
    wf.connect(inputnode, 'CSF_pve', bianca_mask, 'CSF_pve')
    wf.connect(MNI_2_t1w_warp, 'inverse_warp', bianca_mask, 'warp_file_MNI2structural')
    wf.connect(tpl_t1w_brain, 'out_file', bianca_mask, 'structural_image_brainextracted')
    wf.connect(inputnode, 'tpl_t1w_brainmask', bianca_mask, 'brainmask')

    # distancemap
    # dilate for distancemap to avoid rim effects when resampling distancemap
    brainmask_dil = pe.Node(fsl.DilateImage(operation="max"), name="brainmask_dil")
    wf.connect(inputnode, 'tpl_t1w_brainmask', brainmask_dil, "in_file")

    distancemap = pe.Node(fsl.DistanceMap(), name="distancemap")
    wf.connect(bianca_mask, 'vent_file', distancemap, "in_file")
    wf.connect(brainmask_dil, 'out_file', distancemap, "mask_file")

    perivent_mask_init = pe.Node(fsl.maths.MathsCommand(), name="perivent_mask_init")
    perivent_mask_init.inputs.args = "-uthr 10 -bin"
    wf.connect(distancemap, "distance_map", perivent_mask_init, "in_file")

    perivent_mask = pe.Node(fsl.ApplyMask(), name="perivent_mask")
    wf.connect(perivent_mask_init, "out_file", perivent_mask, "in_file")
    wf.connect(inputnode, "tpl_t1w_brainmask", perivent_mask, "mask_file")

    deepWM_mask_init = pe.Node(fsl.maths.MathsCommand(), name="deepWM_mask_init")
    deepWM_mask_init.inputs.args = "-thr 10 -bin"
    wf.connect(distancemap, "distance_map", deepWM_mask_init, "in_file")

    deepWM_mask = pe.Node(fsl.ApplyMask(), name="deepWM_mask")
    wf.connect(deepWM_mask_init, "out_file", deepWM_mask, "in_file")
    wf.connect(inputnode, "tpl_t1w_brainmask", deepWM_mask, "mask_file")

    outputnode = pe.Node(niu.IdentityInterface(fields=["t1w_2_MNI_mat", "t1w_MNIspace", "t1w_2_MNI_warp",
                                                       "bianca_wm_mask_file", "vent_file", "distance_map",
                                                       "perivent_mask",
                                                       "deepWM_mask"]),
                         name='outputnode')

    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_mat', outputnode, "t1w_2_MNI_mat")
    wf.connect(norm_wf, 'outputnode.t1w_MNIspace', outputnode, "t1w_MNIspace")
    wf.connect(norm_wf, 'outputnode.t1w_2_MNI_warp', outputnode, "t1w_2_MNI_warp")
    wf.connect(bianca_mask, 'mask_file', outputnode, "bianca_wm_mask_file")
    wf.connect(bianca_mask, 'vent_file', outputnode, "vent_file")
    wf.connect(distancemap, "distance_map", outputnode, "distance_map")
    wf.connect(perivent_mask, "out_file", outputnode, "perivent_mask")
    wf.connect(deepWM_mask, "out_file", outputnode, "deepWM_mask")
    return wf


def get_norm_wf(name="norm_wf"):
    wf = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['t1w', 't1w_brain']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['t1w_2_MNI_mat', 't1w_2_MNI_warp', 't1w_MNIspace']),
                         name='outputnode')
    # otherwise fnirt is trying to write to the sourcedata dir
    t1w_dummy = pe.Node(fsl.ImageMaths(), name="t1w_dummy")
    wf.connect(inputnode, "t1w", t1w_dummy, "in_file")

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
    wf.connect(t1w_dummy, 'out_file', t1w_2_MNI_fnirt, 'in_file')
    wf.connect(t1w_2_MNI_flirt, 'out_matrix_file', t1w_2_MNI_fnirt, 'affine_file')

    wf.connect(t1w_2_MNI_fnirt, 'field_file', outputnode, 't1w_2_MNI_warp')
    wf.connect(t1w_2_MNI_fnirt, 'warped_file', outputnode, 't1w_MNIspace')
    return wf
