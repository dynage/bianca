from nipype import Node, Workflow
from nipype.interfaces import utility as niu, fsl
from niworkflows.interfaces.bids import DerivativesDataSink


def post_locate_masking(locate_dir, wd_dir, crash_dir, out_dir, subjects_sessions, n_cpu=1):
    out_dir.mkdir(exist_ok=True, parents=True)

    wf = Workflow(name="post_locate_masking")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    base_directory = str(out_dir.parent)
    out_path_base = str(out_dir.name)

    subjects, sessions = list(zip(*subjects_sessions))
    infosource = Node(niu.IdentityInterface(fields=["subject", "session"]), name="infosource")
    infosource.iterables = [("subject", subjects),
                            ("session", sessions),
                            ]
    infosource.synchronize = True

    def subject_info_fnc(locate_dir, subject, session):
        from pathlib import Path
        subses = f"sub-{subject}ses-{session}"

        # bianca mask
        search_pattern = f"*/{subses}_biancamask.nii.gz"
        bianca_mask = list(Path(locate_dir).glob(search_pattern))
        if len(bianca_mask) != 1:
            raise Exception(f"Expected one file, but {len(bianca_mask)} found. {search_pattern}")
        bianca_mask = bianca_mask[0]

        # locate output
        search_pattern = f"*/*_results_directory/{subses}_BIANCA_LOCATE_binarylesionmap.nii.gz"
        locate_mask = list(Path(locate_dir).glob(search_pattern))
        if len(locate_mask) != 1:
            raise Exception(f"Expected one file, but {len(locate_mask)} found. {search_pattern}")
        locate_mask = locate_mask[0]

        generic_bids_file = f"sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_FLAIR.nii.gz"
        out_list = [bianca_mask, locate_mask, generic_bids_file]
        return [str(o) for o in out_list]  # as Path is not taken everywhere

    grabber = Node(niu.Function(input_names=["locate_dir", "subject", "session"],
                                output_names=["bianca_mask", "locate_mask", "generic_bids_file"],
                                function=subject_info_fnc),
                   name="grabber"
                   )
    grabber.inputs.locate_dir = locate_dir

    wf.connect([(infosource, grabber, [("subject", "subject"),
                                       ("session", "session"),
                                       ]
                 )
                ]
               )

    locate_output_masked = Node(fsl.ApplyMask(), name="locate_output_masked")
    wf.connect(grabber, "locate_mask", locate_output_masked, "in_file")
    wf.connect(grabber, "bianca_mask", locate_output_masked, "mask_file")

    ds = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base), name="ds")
    ds.inputs.suffix = "locateBinaryLesionMap"
    ds.inputs.desc = "biancaMasked"
    wf.connect(locate_output_masked, "out_file", ds, "in_file")
    wf.connect(grabber, "generic_bids_file", ds, "source_file")

    wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})
