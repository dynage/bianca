from nipype import Node, Workflow
from nipype.interfaces import utility as niu, fsl, ants
from niworkflows.interfaces.bids import DerivativesDataSink
from pathlib import Path
from warnings import warn
from ..utils import export_version


def prepare_flair_intNorm(flair_prep_dir, out_dir, wd_dir, crash_dir, subjects_sessions, flair_acq, n_cpu=-1):
    out_dir.mkdir(exist_ok=True, parents=True)
    export_version(out_dir)

    wf = Workflow(name="prepare_flair_intNorm")
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

    def subject_info_fnc(flair_prep_dir, subject, session, flair_acq):
        from pathlib import Path

        sub_ses = f"sub-{subject}_ses-{session}"
        flair_files = list(Path(flair_prep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_acq-{flair_acq}_*_FLAIR_biascorr.nii.gz"))
        assert len(flair_files) == 1, f"Expected one file, but found {flair_files}"
        flair_file = flair_files[0]

        brain_masks = list(Path(flair_prep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_space-flair{flair_acq}_desc-brainmask.nii.gz"))
        assert len(brain_masks) > 0, f"Expected one file, but found {brain_masks}"
        brain_mask = brain_masks[0]

        out_list = [flair_file, brain_mask]
        return [str(o) for o in out_list]  # as Path is not taken everywhere

    grabber = Node(niu.Function(input_names=["flair_prep_dir", "subject", "session", "flair_acq"],
                                output_names=["flair_file", "brain_mask"],
                                function=subject_info_fnc),
                   name="grabber"
                   )
    grabber.inputs.flair_prep_dir = flair_prep_dir
    grabber.inputs.flair_acq = flair_acq

    wf.connect([(infosource, grabber, [("subject", "subject"),
                                       ("session", "session"),
                                       ]
                 )
                ]
               )

    # adapted from https://gist.github.com/lebedov/94f1caf8a792d80cd91e7b99c1a0c1d7
    # Intensity normalization - subtract minimum, then divide by difference of maximum and minimum:
    img_range = Node(interface=fsl.ImageStats(op_string='-k %s -R'), name='img_range')
    wf.connect(grabber, "flair_file", img_range, "in_file")
    wf.connect(grabber, "brain_mask", img_range, "mask_file")

    def func(in_stat):
        min_val, max_val = in_stat
        return '-sub %s -div %s' % (min_val, (max_val - min_val))

    stat_to_op_string = Node(interface=niu.Function(input_names=['in_stat'],
                                                    output_names=['op_string'],
                                                    function=func),
                             name='stat_to_op_string', iterfield=['in_stat'])
    wf.connect(img_range, "out_stat", stat_to_op_string, "in_stat")

    flair_normalized = Node(interface=fsl.ImageMaths(), name='flair_normalized')
    wf.connect(stat_to_op_string, "op_string", flair_normalized, "op_string")
    wf.connect(grabber, "flair_file", flair_normalized, "in_file")

    base_directory = str(out_dir.parent)
    out_path_base = str(out_dir.name)
    ds_flair_biascorr_intNorm = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                                     name="ds_flair_biascorr_intNorm")
    ds_flair_biascorr_intNorm.inputs.suffix = "FLAIR_biascorrIntNorm"
    wf.connect(flair_normalized, "out_file", ds_flair_biascorr_intNorm, "in_file")
    wf.connect(grabber, "flair_file", ds_flair_biascorr_intNorm, "source_file")

    wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})
