from nipype import Node, Workflow
from nipype.interfaces import utility as niu, freesurfer as fs, fsl, io, ants
from niworkflows.interfaces.bids import DerivativesDataSink
from pathlib import Path
from warnings import warn


def get_grabber_wf(name="grabber_wf"):
    wf = Workflow(name=name)

    inputnode = Node(niu.IdentityInterface(fields=['subject', 'session', 'bids_dir', 'flair_acq']),
                     name='inputnode')

    def subject_info_fnc(subject, session, bids_dir, flair_acq):
        from pathlib import Path
        sub_ses = f"sub-{subject}_ses-{session}"
        fs_sub = f"{sub_ses}.long.sub-{subject}"

        flair_files = list(Path(bids_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_acq-{flair_acq}_*_FLAIR.nii.gz"))
        assert len(flair_files) > 0, f"Expected at least one file, but found {flair_files}"
        if len(flair_files) > 1:
            warn(f"{len(flair_files)} FLAIR files found. Taking first")
        flair_file = flair_files[0]

        generic_bids_file = Path(bids_dir) / \
                            f"sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w.nii.gz"
        flair_space = f"flair{flair_acq}"

        out_list = [flair_file, generic_bids_file, flair_space, fs_sub]
        return [str(o) for o in out_list]

    outputnode = Node(niu.Function(input_names=["subject", "session", "bids_dir", "flair_acq"],
                                   output_names=["flair_file", "generic_bids_file", "flair_space", "fs_sub"],
                                   function=subject_info_fnc),
                      name="outputnode"
                      )

    wf.connect([(inputnode, outputnode, [("subject", "subject"),
                                         ("session", "session"),
                                         ("bids_dir", "bids_dir"),
                                         ("flair_acq", "flair_acq")
                                         ]
                 )
                ]
               )
    return wf


def get_prep_flair_wf(name="prep_flair"):
    wf = Workflow(name=name)

    inputnode = Node(niu.IdentityInterface(fields=["flair_file", "fs_sub", "fs_dir"]),
                     name='inputnode')

    def fs_info_fnc(fs_sub, fs_dir):
        from pathlib import Path
        fs_mri = Path(fs_dir) / fs_sub / "mri"
        fs_t1 = fs_mri / "T1.mgz"
        fs_brain = fs_mri / "brain.mgz"
        fs_aparcaseg = fs_mri / "aparc+aseg.mgz"

        out_list = [fs_t1, fs_brain, fs_aparcaseg]
        return [str(o) for o in out_list]

    fs_info = Node(niu.Function(input_names=["fs_sub", "fs_dir"],
                                output_names=["fs_t1", "fs_brain", "fs_aparcaseg"],
                                function=fs_info_fnc),
                   name="fs_info")
    wf.connect(inputnode, "fs_sub", fs_info, "fs_sub")
    wf.connect(inputnode, "fs_dir", fs_info, "fs_dir")

    # export from FS
    t1w = Node(fs.MRIConvert(out_type='niigz', out_orientation='LAS'), name="t1w")
    wf.connect(fs_info, "fs_t1", t1w, "in_file")

    brain = Node(fs.MRIConvert(out_type='niigz', out_orientation='LAS'), name="brain")
    wf.connect(fs_info, "fs_brain", brain, "in_file")

    wm_mask_mgz = Node(fs.Binarize(wm=True), name="wm_mask_mgz")
    wf.connect(fs_info, "fs_aparcaseg", wm_mask_mgz, "in_file")
    wm_mask = Node(fs.MRIConvert(out_type='niigz', out_orientation='LAS'), name="wm_mask")
    wf.connect(wm_mask_mgz, "binary_file", wm_mask, "in_file")

    # t1w -> flair
    flair = Node(fsl.Reorient2Std(), name="flair")
    wf.connect(inputnode, "flair_file", flair, "in_file")

    # fixme num_threads
    flair_biascorr = Node(ants.N4BiasFieldCorrection(save_bias=False), name="flair_biascorr")
    wf.connect(flair, "out_file", flair_biascorr, "input_image")

    flirt_t1w_to_flair = Node(fsl.FLIRT(dof=6), name="flirt_t1w_to_flair")
    wf.connect(t1w, "out_file", flirt_t1w_to_flair, "in_file")
    wf.connect(flair_biascorr, "output_image", flirt_t1w_to_flair, "reference")

    # bring fs data to flair space
    t1w_brain_flairSp = Node(fsl.ApplyXFM(), name="t1w_brain_flairSp")
    wf.connect(brain, "out_file", t1w_brain_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", t1w_brain_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", t1w_brain_flairSp, "reference")

    wm_mask_flairSp = Node(fsl.ApplyXFM(interp="nearestneighbour"), name="wm_mask_flairSp")
    wf.connect(wm_mask, "out_file", wm_mask_flairSp, "in_file")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", wm_mask_flairSp, "in_matrix_file")
    wf.connect(flair_biascorr, "output_image", wm_mask_flairSp, "reference")

    # find MNI transformation
    flirt_t1w_to_mni = Node(fsl.FLIRT(dof=12), name="flirt_t1w_to_mni")
    flirt_t1w_to_mni.inputs.reference = fsl.Info.standard_image("MNI152_T1_1mm.nii.gz")
    wf.connect(t1w, "out_file", flirt_t1w_to_mni, "in_file")

    flair_to_t1w = Node(fsl.ConvertXFM(invert_xfm=True), name="flair_to_t1w")
    wf.connect(flirt_t1w_to_flair, "out_matrix_file", flair_to_t1w, "in_file")

    flair_to_mni = Node(fsl.ConvertXFM(concat_xfm=True), name="flair_to_mni")
    wf.connect(flair_to_t1w, "out_file", flair_to_mni, "in_file")
    wf.connect(flirt_t1w_to_mni, "out_matrix_file", flair_to_mni, "in_file2")

    flair_mniSp = Node(fsl.ApplyXFM(), name="flair_mniSp")
    wf.connect(flair_biascorr, "output_image", flair_mniSp, "in_file")
    wf.connect(flair_to_mni, "out_file", flair_mniSp, "in_matrix_file")
    flair_mniSp.inputs.reference = fsl.Info.standard_image("MNI152_T1_1mm.nii.gz")

    #
    # all in flair space and LAS (except flair_to_mni and flair_mniSp)
    outputnode = Node(
        niu.IdentityInterface(
            fields=["flair_biascorr", "t1w", "t1w_brain", "brain_mask", "wm_mask", "fswmh_mask",
                    "t1w_to_flair", "flair_mniSp", "flair_to_mni"]),
        name='outputnode')
    wf.connect(flair_biascorr, "output_image", outputnode, "flair_biascorr")

    wf.connect(t1w_brain_flairSp, "out_file", outputnode, "t1w_brain")
    wf.connect(wm_mask_flairSp, "out_file", outputnode, "wm_mask")

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
        fields=['flair_biascorr', 't1w_brain', 'wm_mask', 'bids_flair_file', "generic_bids_file", "space",
                "t1w_to_flair", "flair_mniSp", "flair_to_mni"]),
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

    ds_t1w_brain = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                        name="ds_t1w_brain")
    ds_t1w_brain.inputs.desc = "t1w_brain"
    wf.connect(inputnode, "t1w_brain", ds_t1w_brain, "in_file")
    wf.connect(inputnode, "generic_bids_file", ds_t1w_brain, "source_file")
    wf.connect(inputnode, "space", ds_t1w_brain, "space")

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


def prepare_bianca_data(bids_dir, out_dir, fs_dir, wd_dir, crash_dir, info_tpls, n_cpu=4):
    import subprocess
    version_label = subprocess.check_output(["git", "describe", "--tags"]).strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pipeline_version.txt").write_text(version_label.decode())

    wf = Workflow(name="meta_prepare")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    subjects, sessions, flair_acqs = list(zip(*info_tpls))
    infosource = Node(niu.IdentityInterface(fields=["subject", "session", "flair_acq"]), name="infosource")
    infosource.iterables = [("subject", subjects),
                            ("session", sessions),
                            ("flair_acq", flair_acqs)
                            ]
    infosource.synchronize = True

    grabber_wf = get_grabber_wf()
    grabber_wf.inputs.inputnode.bids_dir = bids_dir
    wf.connect(infosource, "subject", grabber_wf, "inputnode.subject")
    wf.connect(infosource, "session", grabber_wf, "inputnode.session")
    wf.connect(infosource, "flair_acq", grabber_wf, "inputnode.flair_acq")

    #
    prep_flair_wf = get_prep_flair_wf()
    prep_flair_wf.inputs.inputnode.fs_dir = fs_dir
    wf.connect([(grabber_wf, prep_flair_wf, [("outputnode.flair_file", "inputnode.flair_file"),
                                             ("outputnode.fs_sub", "inputnode.fs_sub"),
                                             ]
                 )
                ]
               )

    ds_wf = get_ds_wf(out_dir)
    wf.connect([(prep_flair_wf, ds_wf, [("outputnode.flair_biascorr", "inputnode.flair_biascorr"),
                                        ("outputnode.t1w_brain", "inputnode.t1w_brain"),
                                        ("outputnode.wm_mask", "inputnode.wm_mask"),
                                        ("outputnode.t1w_to_flair", "inputnode.t1w_to_flair"),
                                        ("outputnode.flair_mniSp", "inputnode.flair_mniSp"),
                                        ("outputnode.flair_to_mni", "inputnode.flair_to_mni"),
                                        ]
                 ),
                (grabber_wf, ds_wf, [("outputnode.flair_file", "inputnode.bids_flair_file"),
                                     ("outputnode.flair_space", "inputnode.space"),
                                     ("outputnode.generic_bids_file", "inputnode.generic_bids_file"),
                                     ]
                 )
                ]
               )

    wf.write_graph("workflow_graph.png", graph2use="exec")
    wf.write_graph("workflow_graph_c.png", graph2use="colored")
    wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})
