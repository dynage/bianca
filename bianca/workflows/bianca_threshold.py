from nipype import Node, Workflow
from nipype.interfaces import utility as niu, fsl, ants
from niworkflows.interfaces.bids import DerivativesDataSink
from bianca.workflows.interfaces import BiancaOverlapMeasures, BiancaClusterStats


def bianca_threshold(bianca_dir, mask_dir, flair_prep_dir, wd_dir, crash_dir, out_dir, subjects_sessions, flair_acq,
                     thresholds, n_cpu=1, run_BiancaOverlapMeasures=True):
    out_dir.mkdir(exist_ok=True, parents=True)

    wf = Workflow(name="bianca_threshold")
    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"

    def format_t(s):
        return f"thresh{s}"

    base_directory = str(out_dir.parent)
    out_path_base = str(out_dir.name)

    subjects, sessions = list(zip(*subjects_sessions))
    infosource = Node(niu.IdentityInterface(fields=["subject", "session"]), name="infosource")
    infosource.iterables = [("subject", subjects),
                            ("session", sessions),
                            ]
    infosource.synchronize = True

    threshsource = Node(niu.IdentityInterface(fields=["threshold"]), name="threshsource")
    threshsource.iterables = [("threshold", thresholds)]

    def subject_info_fnc(bianca_dir, mask_dir, flair_prep_dir, subject, session, flair_acq, run_BiancaOverlapMeasures):
        from pathlib import Path
        sub_ses = f"sub-{subject}_ses-{session}"
        bianca_lpm = list(Path(bianca_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_acq-{flair_acq}_*_FLAIR_LPM.nii.gz"))[0]

        if run_BiancaOverlapMeasures:
            manual_mask = list(Path(mask_dir).glob(
                f"sub-{subject}/ses-{session}/{sub_ses}_acq-{flair_acq}_*_FLAIR_mask_goldstandard_new.nii.gz"))[0]
        else:
            manual_mask = None

        wm_mask = list(Path(flair_prep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_space-flair{flair_acq}_desc-wmmask.nii.gz"))[0]
        deepwm_mask = list(Path(flair_prep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_space-flair{flair_acq}_desc-deepWMmask.nii.gz"))[0]
        pervent_mask = list(Path(flair_prep_dir).glob(
            f"sub-{subject}/ses-{session}/anat/{sub_ses}_space-flair{flair_acq}_desc-periventmask.nii.gz"))[0]
        out_list = [bianca_lpm, manual_mask, wm_mask, deepwm_mask, pervent_mask]
        return [str(o) for o in out_list]  # as Path is not taken everywhere

    grabber = Node(niu.Function(input_names=["bianca_dir", "mask_dir", "flair_prep_dir", "subject", "session",
                                             "flair_acq", "run_BiancaOverlapMeasures"],
                                output_names=["bianca_lpm", "manual_mask", "wm_mask", "deepwm_mask", "pervent_mask"],
                                function=subject_info_fnc),
                   name="grabber"
                   )
    grabber.inputs.bianca_dir = bianca_dir
    grabber.inputs.mask_dir = mask_dir
    grabber.inputs.flair_prep_dir = flair_prep_dir
    grabber.inputs.flair_acq = flair_acq
    grabber.inputs.run_BiancaOverlapMeasures = run_BiancaOverlapMeasures

    wf.connect([(infosource, grabber, [("subject", "subject"),
                                       ("session", "session"),
                                       ]
                 )
                ]
               )
    # threshold lpm
    bianca_lpm_masked = Node(fsl.ApplyMask(), name="bianca_lpm_masked")
    wf.connect(grabber, "bianca_lpm", bianca_lpm_masked, "in_file")
    wf.connect(grabber, "wm_mask", bianca_lpm_masked, "mask_file")

    thresholded_bianca_lpm_mask = Node(fsl.Threshold(), name="thresholded_bianca_lpm_mask")
    wf.connect(bianca_lpm_masked, "out_file", thresholded_bianca_lpm_mask, "in_file")
    wf.connect(threshsource, "threshold", thresholded_bianca_lpm_mask, "thresh")
    thresholded_bianca_lpm_mask.inputs.args = "-bin"

    ds_masked = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base), name="ds_masked")
    ds_masked.inputs.desc = "biancamasked"
    wf.connect(bianca_lpm_masked, "out_file", ds_masked, "in_file")
    wf.connect(grabber, "bianca_lpm", ds_masked, "source_file")

    ds_masked_thr_bin = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                             name="ds_masked_thr_bin")
    ds_masked_thr_bin.inputs.suffix = "biancaLPMmaskedThrBin"
    wf.connect(threshsource, ("threshold", format_t), ds_masked_thr_bin, "desc")
    wf.connect(thresholded_bianca_lpm_mask, "out_file", ds_masked_thr_bin, "in_file")
    wf.connect(grabber, "bianca_lpm", ds_masked_thr_bin, "source_file")

    def str_to_file_fct(s):
        from pathlib import Path
        out_file = Path.cwd() / "out.txt"
        out_file.write_text(s)
        return str(out_file)

    # volume extraction
    ## total
    cluster_stats_total = Node(BiancaClusterStats(), name="cluster_stats_total")
    cluster_stats_total.inputs.min_cluster_size = 0
    wf.connect(bianca_lpm_masked, "out_file", cluster_stats_total, "bianca_output_map")
    wf.connect(threshsource, "threshold", cluster_stats_total, "threshold")
    wf.connect(grabber, "wm_mask", cluster_stats_total, "mask_file")

    str_to_file_total = Node(niu.Function(input_names=["s"], output_names=["out_file"], function=str_to_file_fct),
                             name="str_to_file_total")
    wf.connect(cluster_stats_total, "out_stat", str_to_file_total, "s")

    ds_cluster_stats_total = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                                  name="ds_cluster_stats_total")
    ds_cluster_stats_total.inputs.suffix = "ClusterStatsTotal"
    wf.connect(threshsource, ("threshold", format_t), ds_cluster_stats_total, "desc")
    wf.connect(str_to_file_total, "out_file", ds_cluster_stats_total, "in_file")
    wf.connect(grabber, "bianca_lpm", ds_cluster_stats_total, "source_file")

    ## deep wm
    cluster_stats_deepwm = Node(BiancaClusterStats(), name="cluster_stats_deepwm")
    cluster_stats_deepwm.inputs.min_cluster_size = 0
    wf.connect(bianca_lpm_masked, "out_file", cluster_stats_deepwm, "bianca_output_map")
    wf.connect(threshsource, "threshold", cluster_stats_deepwm, "threshold")
    wf.connect(grabber, "deepwm_mask", cluster_stats_deepwm, "mask_file")

    str_to_file_deepwm = Node(niu.Function(input_names=["s"], output_names=["out_file"], function=str_to_file_fct),
                              name="str_to_file_deepwm")
    wf.connect(cluster_stats_deepwm, "out_stat", str_to_file_deepwm, "s")

    ds_cluster_stats_deepwm = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                                   name="ds_cluster_stats_deepwm")
    ds_cluster_stats_deepwm.inputs.suffix = "ClusterStatsdeepwm"
    wf.connect(threshsource, ("threshold", format_t), ds_cluster_stats_deepwm, "desc")
    wf.connect(str_to_file_deepwm, "out_file", ds_cluster_stats_deepwm, "in_file")
    wf.connect(grabber, "bianca_lpm", ds_cluster_stats_deepwm, "source_file")

    ## perivent wm
    cluster_stats_perventwm = Node(BiancaClusterStats(), name="cluster_stats_perventwm")
    cluster_stats_perventwm.inputs.min_cluster_size = 0
    wf.connect(bianca_lpm_masked, "out_file", cluster_stats_perventwm, "bianca_output_map")
    wf.connect(threshsource, "threshold", cluster_stats_perventwm, "threshold")
    wf.connect(grabber, "pervent_mask", cluster_stats_perventwm, "mask_file")

    str_to_file_perventwm = Node(niu.Function(input_names=["s"], output_names=["out_file"], function=str_to_file_fct),
                                 name="str_to_file_perventwm")
    wf.connect(cluster_stats_perventwm, "out_stat", str_to_file_perventwm, "s")

    ds_cluster_stats_perventwm = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                                      name="ds_cluster_stats_perventwm")
    ds_cluster_stats_perventwm.inputs.suffix = "ClusterStatsperventwm"
    wf.connect(threshsource, ("threshold", format_t), ds_cluster_stats_perventwm, "desc")
    wf.connect(str_to_file_perventwm, "out_file", ds_cluster_stats_perventwm, "in_file")
    wf.connect(grabber, "bianca_lpm", ds_cluster_stats_perventwm, "source_file")

    if run_BiancaOverlapMeasures:
        overlap = Node(BiancaOverlapMeasures(), name="overlap")
        wf.connect(bianca_lpm_masked, "out_file", overlap, "lesionmask")
        wf.connect(grabber, "manual_mask", overlap, "manualmask")
        wf.connect(threshsource, "threshold", overlap, "threshold")
        overlap.inputs.saveoutput = 1

        ds_overlap = Node(DerivativesDataSink(base_directory=base_directory, out_path_base=out_path_base),
                          name="ds_overlap")
        ds_overlap.inputs.suffix = "overlap"
        wf.connect(threshsource, ("threshold", format_t), ds_overlap, "desc")
        wf.connect(overlap, "out_file", ds_overlap, "in_file")
        wf.connect(grabber, "bianca_lpm", ds_overlap, "source_file")

    wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})
