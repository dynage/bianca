from pathlib import Path

from nipype.pipeline import engine as pe
from nipype import Workflow
from nipype.interfaces import utility as niu, fsl, io, ants

import smriprep
import niworkflows
from niworkflows.interfaces.bids import DerivativesDataSink

from ..utils import export_version
from warnings import warn


def _check_versions():
    if smriprep.__version__ != '0.5.2':
        warn(f"tested with smriprep version 0.5.2. but {smriprep.__version__} is installed")

    if niworkflows.__version__ != '1.1.12':
        warn(f"tested with niworkflows version 0.5.2. but {niworkflows.__version__} is installed")


def prepare_t1w(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, info_tpls, n_cpu=1, omp_nthreads=1, run_wf=True,
                graph=False):
    _check_versions()
    export_version(out_dir)

    out_dir.mkdir(exist_ok=True, parents=True)

    wf = Workflow(name="meta_prepare_t1")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    for subject, sessions in info_tpls:
        for session in sessions:
            name = f"anat_preproc_{subject}_{session}"
            single_ses_wf = init_single_ses_anat_preproc_wf(subject=subject,
                                                            session=session,
                                                            bids_dir=bids_dir,
                                                            smriprep_dir=smriprep_dir,
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
                                    bids_dir,
                                    smriprep_dir,
                                    out_dir,
                                    omp_nthreads=1,
                                    name='anat_preproc_wf'):
    """
    """
    wf = Workflow(name=name)

    def subject_info_fnc(bids_dir, smriprep_dir, subject, session):
        from pathlib import Path
        tpl_t1w = str(Path(smriprep_dir, f"sub-{subject}/anat/sub-{subject}_T1w_preproc.nii.gz"))
        tpl_brainmask = str(Path(smriprep_dir, f"sub-{subject}/anat/sub-{subject}_T1w_brainmask.nii.gz"))

        t1ws = list(Path(bids_dir).glob(f"sub-{subject}/ses-{session}/anat/*_T1w.nii.gz"))
        assert len(t1ws) > 0, f"Expected at least one file, but found {t1ws}"
        t1ws.sort()

        xfms = list(Path(smriprep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/*_run-*_T1w_space-orig_target-T1w_affine.txt"))
        xfms.sort()

        for f in t1ws + xfms:
            if not f.is_file():
                raise FileNotFoundError(f)
        t1ws = [str(o) for o in t1ws]  # as Path is not taken everywhere
        xfms = [str(o) for o in xfms]
        return tpl_t1w, tpl_brainmask, t1ws, xfms

    grabber = pe.Node(niu.Function(input_names=["bids_dir", "smriprep_dir", "subject", "session"],
                                   output_names=["tpl_t1w", "tpl_brainmask", "t1ws", "xfms"],
                                   function=subject_info_fnc),
                      name="grabber"
                      )
    grabber.inputs.bids_dir = bids_dir
    grabber.inputs.smriprep_dir = smriprep_dir
    grabber.inputs.subject = subject
    grabber.inputs.session = session

    t1w_biascorr = pe.MapNode(ants.N4BiasFieldCorrection(save_bias=False, num_threads=omp_nthreads),
                              iterfield=["input_image"],
                              name="t1w_biascorr")
    wf.connect(grabber, "t1ws", t1w_biascorr, "input_image")

    t1w_tpl_space = pe.MapNode(fsl.FLIRT(dof=6), iterfield=["in_file"], name="t1w_tpl_space")
    wf.connect(grabber, "tpl_t1w", t1w_tpl_space, "reference")
    wf.connect(t1w_biascorr, "output_image", t1w_tpl_space, "in_file")

    merge_t1w = pe.Node(fsl.Merge(dimension="t"), name='merge_t1w')
    wf.connect(t1w_tpl_space, "out_file", merge_t1w, "in_files")

    mean_t1w = pe.Node(fsl.MeanImage(), name='mean_t1w')
    wf.connect(merge_t1w, "merged_file", mean_t1w, "in_file")

    t1w_brain_tpl_space = pe.Node(fsl.ApplyMask(), name="t1w_brain_tpl_space")
    wf.connect(mean_t1w, "out_file", t1w_brain_tpl_space, "in_file")
    wf.connect(grabber, "tpl_brainmask", t1w_brain_tpl_space, "mask_file")

    ds = init_t1w_derivatives_wf(bids_dir, out_dir)
    ds.inputs.inputnode.subject = subject
    ds.inputs.inputnode.session = session
    wf.connect(mean_t1w, "out_file", ds, "inputnode.t1w_template_space")
    wf.connect(t1w_brain_tpl_space, "out_file", ds, "inputnode.t1w_brain_template_space")

    return wf


def init_t1w_derivatives_wf(bids_root, output_dir, name='t1w_derivatives_wf'):
    """Set up a battery of datasinks to store derivatives in the right location."""
    base_directory = str(output_dir.parent)
    out_path_base = str(output_dir.name)

    wf = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['subject', 'session', 't1w_template_space', 't1w_brain_template_space']),
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
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, keep_dtype=True, compress=True,
                            space="tpl"),
        name='ds_t1w_preproc', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_preproc, "source_file")
    wf.connect(inputnode, "t1w_template_space", ds_t1w_preproc, "in_file")

    ds_t1w_brain = pe.Node(
        DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base, keep_dtype=True, compress=True,
                            space="tpl", desc="brain"),
        name='ds_t1w_brain', run_without_submitting=True)
    wf.connect(generic_bids_file, "out_file", ds_t1w_brain, "source_file")
    wf.connect(inputnode, "t1w_brain_template_space", ds_t1w_brain, "in_file")

    return wf
