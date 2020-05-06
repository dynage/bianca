from nipype import Node, Workflow
from nipype.interfaces import utility as niu, fsl, ants
from niworkflows.interfaces.bids import DerivativesDataSink
from pathlib import Path
from warnings import warn
from ..utils import export_version


def prepare_bianca_data(bids_dir, template_prep_dir, t1w_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions,
                        flair_acq, n_cpu=-1,
                        omp_nthreads=1, run_wf=True, graph=False):
    out_dir.mkdir(exist_ok=True, parents=True)
    export_version(out_dir)

    wf = Workflow(name="meta_prepare")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    subjects, sessions = list(zip(*subjects_sessions))
    infosource = Node(niu.IdentityInterface(fields=["subject", "session", "flair_acq"]), name="infosource")
    infosource.iterables = [("subject", subjects),
                            ("session", sessions),
                            ]
    infosource.synchronize = True

    def subject_info_fnc(bids_dir, template_prep_dir, t1w_prep_dir, subject, session, flair_acq):
        from pathlib import Path
        sub_ses = f"sub-{subject}_ses-{session}"
        sub = f"sub-{subject}"

        flair_files = list(Path(bids_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_acq-{flair_acq}_*_FLAIR.nii.gz"))
        assert len(flair_files) > 0, f"Expected at least one file, but found {flair_files}"
        if len(flair_files) > 1:
            warn(f"{len(flair_files)} FLAIR files found. Taking first")
        flair_file = flair_files[0]

        generic_bids_file = Path(bids_dir) / f"sub-{subject}/ses-{session}/anat/{sub_ses}_T1w.nii.gz"
        flair_space = f"flair{flair_acq}"

        t1w_sub = t1w_prep_dir / f"sub-{subject}/ses-{session}/anat"
        t1w = t1w_sub / f"{sub_ses}_space-tpl_T1w.nii.gz"
        t1w_brain = t1w_sub / f"{sub_ses}_space-tpl_desc-brain_T1w.nii.gz"

        template_sub = Path(template_prep_dir) / f"sub-{subject}/anat/"
        t1w_brainmask = template_sub / f"{sub}_desc-brain_mask.nii.gz"
        t1w_to_MNI_xfm = template_sub / f"{sub}_from-tpl_to-MNI_xfm.mat"
        vent_mask = template_sub / f"{sub}_desc-bianca_ventmask.nii.gz"
        wm_mask = template_sub / f"{sub}_desc-bianca_wmmask.nii.gz"
        distancemap = template_sub / f"{sub}_desc-bianca_ventdistmap.nii.gz"
        perivent_mask = template_sub / f"{sub}_desc-periventmask.nii.gz"
        deepWM_mask = template_sub / f"{sub}_desc-deepWMmask.nii.gz"

        out_list = [flair_file, generic_bids_file, flair_space, t1w, t1w_brain, t1w_brainmask, t1w_to_MNI_xfm,
                    vent_mask, wm_mask, distancemap, perivent_mask, deepWM_mask]
        for f in [flair_file, t1w, t1w_brain, t1w_brainmask, t1w_to_MNI_xfm, vent_mask, wm_mask, distancemap]:
            if not f.is_file():
                raise FileNotFoundError(f)
        return [str(o) for o in out_list]  # as Path is not taken everywhere

    grabber = Node(niu.Function(input_names=["bids_dir", "template_prep_dir", "t1w_prep_dir", "subject", "session",
                                             "flair_acq"],
                                output_names=["flair_file", "generic_bids_file", "flair_space", "t1w", "t1w_brain",
                                              "t1w_brainmask", "t1w_to_MNI_xfm", "vent_mask", "wm_mask",
                                              "distancemap", "perivent_mask", "deepWM_mask"],
                                function=subject_info_fnc),
                   name="grabber"
                   )
    grabber.inputs.bids_dir = bids_dir
    grabber.inputs.t1w_prep_dir = t1w_prep_dir
    grabber.inputs.template_prep_dir = template_prep_dir
    grabber.inputs.flair_acq = flair_acq

    wf.connect([(infosource, grabber, [("subject", "subject"),
                                       ("session", "session"),
                                       ]
                 )
                ]
               )
    prep_flair_wf = get_prep_flair_wf(omp_nthreads=omp_nthreads)
    wf.connect([(grabber, prep_flair_wf, [("flair_file", "inputnode.flair_file"),
                                          ("t1w", "inputnode.t1w"),
                                          ("t1w_brain", "inputnode.t1w_brain"),
                                          ("t1w_brainmask", "inputnode.t1w_brainmask"),
                                          ("t1w_to_MNI_xfm", "inputnode.t1w_to_MNI_xfm"),
                                          ("vent_mask", "inputnode.vent_mask"),
                                          ("wm_mask", "inputnode.wm_mask"),
                                          ("distancemap", "inputnode.distancemap"),
                                          ("perivent_mask", "inputnode.perivent_mask"),
                                          ("deepWM_mask", "inputnode.deepWM_mask"),
                                          ]
                 )
                ]
               )

    ds_wf = get_ds_wf(out_dir)
    wf.connect([(prep_flair_wf, ds_wf, [("outputnode.flair_biascorr", "inputnode.flair_biascorr"),
                                        ("outputnode.t1w_brain", "inputnode.t1w_brain"),
                                        ("outputnode.brainmask", "inputnode.brainmask"),
                                        ("outputnode.wm_mask", "inputnode.wm_mask"),
                                        ("outputnode.vent_mask", "inputnode.vent_mask"),
                                        ("outputnode.distancemap", "inputnode.distancemap"),
                                        ("outputnode.perivent_mask", "inputnode.perivent_mask"),
                                        ("outputnode.deepWM_mask", "inputnode.deepWM_mask"),
                                        ("outputnode.t1w_to_flair", "inputnode.t1w_to_flair"),
                                        ("outputnode.flair_mniSp", "inputnode.flair_mniSp"),
                                        ("outputnode.flair_to_mni", "inputnode.flair_to_mni"),
                                        ]
                 ),
                (grabber, ds_wf, [("flair_file", "inputnode.bids_flair_file"),
                                  ("flair_space", "inputnode.space"),
                                  ("generic_bids_file", "inputnode.generic_bids_file"),
                                  ]
                 )
                ]
               )

    if graph:
        wf.write_graph("workflow_graph.png", graph2use="exec")
        wf.write_graph("workflow_graph_c.png", graph2use="colored")
    if run_wf:
        wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})


def get_prep_flair_wf(name="prep_flair", omp_nthreads=1):
    wf = Workflow(name=name)

    inputnode = Node(niu.IdentityInterface(
        fields=["t1w", "t1w_brain", "t1w_brainmask", "t1w_to_MNI_xfm", "flair_file", "vent_mask", "wm_mask",
                "distancemap", "perivent_mask", "perivent_mask", "deepWM_mask"]),
        name='inputnode')

    # t1w -> flair
    flair = Node(fsl.Reorient2Std(), name="flair")
    wf.connect(inputnode, "flair_file", flair, "in_file")

    flair_biascorr = Node(ants.N4BiasFieldCorrection(save_bias=False, num_threads=omp_nthreads), name="flair_biascorr")
    wf.connect(flair, "out_file", flair_biascorr, "input_image")

    flirt_t1w_to_flair = Node(fsl.FLIRT(dof=6), name="flirt_t1w_to_flair")
    wf.connect(inputnode, "t1w", flirt_t1w_to_flair, "in_file")
    wf.connect(flair_biascorr, "output_image", flirt_t1w_to_flair, "reference")

    # bring t1w data to flair space
    t1w_brain_flairSp = Node(fsl.ApplyXFM(), name="t1w_brain_flairSp")
    wf.connect(inputnode, "t1w_brain", t1w_brain_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", t1w_brain_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", t1w_brain_flairSp, "reference")

    brainmask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="brainmask_flairSp")
    wf.connect(inputnode, "t1w_brainmask", brainmask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", brainmask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", brainmask_flairSp, "reference")

    wm_mask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="wm_mask_flairSp")
    wf.connect(inputnode, "wm_mask", wm_mask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", wm_mask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", wm_mask_flairSp, "reference")

    vent_mask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="vent_mask_flairSp")
    wf.connect(inputnode, "vent_mask", vent_mask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", vent_mask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", vent_mask_flairSp, "reference")

    # since there might be some missalignment between the (nn resampled) brain mask and the distancemap, there might
    # be some distance values outside the flair space brain mask --> re-threshold to get rid of them
    # also, the distancemap was created with a dilated brainmaks
    distancemap_flairSp_init = Node(fsl.ApplyXFM(), name="distancemap_flairSp_init")
    wf.connect(inputnode, "distancemap", distancemap_flairSp_init, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", distancemap_flairSp_init, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", distancemap_flairSp_init, "reference")

    distancemap_flairSp = Node(fsl.ApplyMask(), name="distancemap_flairSp")
    wf.connect(distancemap_flairSp_init, "out_file", distancemap_flairSp, "in_file")
    wf.connect(brainmask_flairSp, "out_file", distancemap_flairSp, "mask_file")

    perivent_mask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="perivent_mask_flairSp")
    wf.connect(inputnode, "perivent_mask", perivent_mask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", perivent_mask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", perivent_mask_flairSp, "reference")

    deepWM_mask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="deepWM_mask_flairSp")
    wf.connect(inputnode, "deepWM_mask", deepWM_mask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", deepWM_mask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", deepWM_mask_flairSp, "reference")

    # MNI
    flair_to_t1w = Node(fsl.ConvertXFM(invert_xfm=True), name="flair_to_t1w")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", flair_to_t1w, "in_file")

    flair_to_mni = Node(fsl.ConvertXFM(concat_xfm=True), name="flair_to_mni")
    wf.connect(flair_to_t1w, "out_file", flair_to_mni, "in_file")
    wf.connect(inputnode, "t1w_to_MNI_xfm", flair_to_mni, "in_file2")

    flair_mniSp = Node(fsl.ApplyXFM(), name="flair_mniSp")
    wf.connect(flair_biascorr, "output_image", flair_mniSp, "in_file")
    wf.connect(flair_to_mni, "out_file", flair_mniSp, "in_matrix_file")
    flair_mniSp.inputs.reference = fsl.Info.standard_image("MNI152_T1_1mm.nii.gz")

    #
    outputnode = Node(niu.IdentityInterface(
        fields=["flair_biascorr", "t1w", "t1w_brain", "brain_mask", "brainmask", "wm_mask", "vent_mask",
                "distancemap", "perivent_mask", "deepWM_mask", "distancemap", "t1w_to_flair", "flair_mniSp",
                "flair_to_mni"]),
        name='outputnode')

    wf.connect(flair_biascorr, "output_image", outputnode, "flair_biascorr")

    wf.connect(t1w_brain_flairSp, "out_file", outputnode, "t1w_brain")
    wf.connect(brainmask_flairSp, "out_file", outputnode, "brainmask")
    wf.connect(wm_mask_flairSp, "out_file", outputnode, "wm_mask")
    wf.connect(vent_mask_flairSp, "out_file", outputnode, "vent_mask")

    wf.connect(distancemap_flairSp, "out_file", outputnode, "distancemap")
    wf.connect(perivent_mask_flairSp, "out_file", outputnode, "perivent_mask")
    wf.connect(deepWM_mask_flairSp, "out_file", outputnode, "deepWM_mask")

    wf.connect(flirt_t1w_to_flair, "out_matrix_file", outputnode, "t1w_to_flair")

    wf.connect(flair_mniSp, "out_file", outputnode, "flair_mniSp")
    wf.connect(flair_to_mni, "out_file", outputnode, "flair_to_mni")

    return wf


def get_ds_wf(out_dir, name="get_ds_wf"):
    out_dir = Path(out_dir)
    wf = Workflow(name=name)

    base_directory = str(out_dir.parent)
    out_path_base = str(out_dir.name)

    inputnode = Node(niu.IdentityInterface(
        fields=['flair_biascorr', 't1w_brain', 'brainmask', 'wm_mask', 'vent_mask', 'distancemap', 'perivent_mask',
                'deepWM_mask', 'bids_flair_file', "generic_bids_file", "space", "t1w_to_flair", "flair_mniSp",
                "flair_to_mni"]),
        name='inputnode')

    ds_flair_biascorr = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                             name="ds_flair_biascorr")
    ds_flair_biascorr.inputs.suffix = "FLAIR_biascorr"
    wf.connect(inputnode, "flair_biascorr", ds_flair_biascorr, "in_file")
    wf.connect(inputnode, "bids_flair_file", ds_flair_biascorr, "source_file")

    ds_wmmask = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base), name="ds_wmmask")
    ds_wmmask.inputs.desc = "wmmask"
    wf.connect(inputnode, "wm_mask", ds_wmmask, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_wmmask, "source_file")
    wf.connect(inputnode, "space", ds_wmmask, "space")

    ds_ventmask = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                       name="ds_ventmask")
    ds_ventmask.inputs.desc = "ventmask"
    wf.connect(inputnode, "vent_mask", ds_ventmask, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_ventmask, "source_file")
    wf.connect(inputnode, "space", ds_ventmask, "space")

    ds_distancemap = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                          name="ds_distancemap")
    ds_distancemap.inputs.desc = "distanceVent"
    wf.connect(inputnode, "distancemap", ds_distancemap, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_distancemap, "source_file")
    wf.connect(inputnode, "space", ds_distancemap, "space")

    ds_perivent_mask = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                            name="ds_perivent_mask")
    ds_perivent_mask.inputs.desc = "periventmask"
    wf.connect(inputnode, "perivent_mask", ds_perivent_mask, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_perivent_mask, "source_file")
    wf.connect(inputnode, "space", ds_perivent_mask, "space")

    ds_deepWM_mask = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                          name="ds_deepWM_mask")
    ds_deepWM_mask.inputs.desc = "deepWMmask"
    wf.connect(inputnode, "deepWM_mask", ds_deepWM_mask, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_deepWM_mask, "source_file")
    wf.connect(inputnode, "space", ds_deepWM_mask, "space")

    ds_t1w_brain = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                        name="ds_t1w_brain")
    ds_t1w_brain.inputs.desc = "t1w_brain"
    wf.connect(inputnode, "t1w_brain", ds_t1w_brain, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_t1w_brain, "source_file")
    wf.connect(inputnode, "space", ds_t1w_brain, "space")

    ds_brainmask = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                        name="ds_brainmask")
    ds_brainmask.inputs.desc = "brainmask"
    wf.connect(inputnode, "brainmask", ds_brainmask, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_brainmask, "source_file")
    wf.connect(inputnode, "space", ds_brainmask, "space")

    ds_t1w_to_flair = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                                               allowed_entities=['from', 'to'], **{'from': 't1w'}),
                           name="ds_t1w_to_flair")

    wf.connect(inputnode, "t1w_to_flair", ds_t1w_to_flair, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_t1w_to_flair, "source_file")
    wf.connect(inputnode, "space", ds_t1w_to_flair, "to")

    # MNI outputs
    ds_flair_mniSp = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                          name="ds_flair_mniSp")
    ds_flair_mniSp.inputs.suffix = "FLAIR"
    ds_flair_mniSp.inputs.space = "MNI"
    ds_flair_mniSp.inputs.desc = "12dof"
    wf.connect(inputnode, "flair_mniSp", ds_flair_mniSp, "in_file")
    wf.connect(inputnode, "bids_flair_file", ds_flair_mniSp, "source_file")

    ds_flair_to_mni = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base,
                                               allowed_entities=['from', 'to'], **{'to': 'MNI'}),
                           name="ds_flair_to_mni")
    ds_flair_to_mni.inputs.desc = "12dof"
    wf.connect(inputnode, "flair_to_mni", ds_flair_to_mni, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_flair_to_mni, "source_file")
    wf.connect(inputnode, "space", ds_flair_to_mni, "from")
    return wf
