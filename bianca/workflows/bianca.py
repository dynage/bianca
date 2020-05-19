from nipype import Node, Workflow
from nipype.interfaces import utility as niu
from niworkflows.interfaces.bids import DerivativesDataSink
from .interfaces import BIANCA

import subprocess, bianca
import pandas as pd
import numpy as np
from copy import copy


def run_bianca_wf(masterfile, out_dir, wd_dir, crash_dir, df, training_subject_idx, query_subject_idx,
                  name="bianca", n_cpu=4, save_classifier=False, trained_classifier_file=None):
    """

    :param masterfile: str
    :param out_dir:
    :param wd_dir:
    :param crash_dir:
    :param df: df
    :param training_subject_idx: training_subject_idx: list of ints, python-style 0-based; training subjects in df
    :param query_subject_idx: list of ints, python-style 0-based; querysubjects in df
    :param name:
    :param n_cpu:
    :param save_classifier: bool
    :param trained_classifier_file: file previously saved with save_classifier; if given, training subjects
    are ignored and classifier file is used in prediction
    :return: None
    """

    if save_classifier and trained_classifier_file:
        raise RuntimeError("save_classifier and trained_classifier_file cannot be set at the same time")
    if trained_classifier_file:
        trained_classifier_file = str(trained_classifier_file)
    #####
    # masterfile information
    expected_header = ['flair', 't1w', 'manual_mask', 'mat', 'subject', 'session']
    assert df.columns.tolist() == expected_header, f"masterfile columns are off. columns should be \
    {expected_header} but are {df.columns}"

    featuresubset = "1,2"
    brainmaskfeaturenum = "2"
    labelfeaturenum = "3"
    matfeaturenum = "4"

    ######
    # workflow
    wf = Workflow(name=name)

    ######
    # subject info
    inputnode = Node(niu.IdentityInterface(fields=['query_subject_idx']), name='inputnode')
    inputnode.iterables = [("query_subject_idx", query_subject_idx)]
    inputnode.synchronize = True

    def get_query_info_fnc(df, query_subject_idx):
        def get_subjects_info(df, idx):
            return df.iloc[idx].subject.tolist()[0], df.iloc[idx].session.tolist()[0], df.iloc[idx].flair.tolist()[0]

        query_subject, query_session, query_flair = get_subjects_info(df, [query_subject_idx])
        query_subject_num = query_subject_idx + 1
        return query_subject, query_session, query_flair, query_subject_num

    query_info = Node(niu.Function(
        input_names=["df", "query_subject_idx"],
        output_names=['query_subject', 'query_session', 'query_flair', 'query_subject_num'],
        function=get_query_info_fnc), name="query_info")
    query_info.inputs.df = df
    wf.connect(inputnode, "query_subject_idx", query_info, "query_subject_idx")

    def get_training_info_fnc(df, query_subject_idx, training_subject_idx):
        import numpy as np
        training_subject_idx_clean = training_subject_idx.tolist()
        if query_subject_idx in training_subject_idx_clean:
            training_subject_idx_clean.remove(query_subject_idx)
        training_subjects = df.iloc[training_subject_idx_clean].subject.tolist()
        training_sessions = df.iloc[training_subject_idx_clean].session.tolist()
        training_subject_nums_str = ",".join((np.array(training_subject_idx_clean) + 1).astype(str).tolist())
        return training_subject_idx_clean, training_subject_nums_str, training_subjects, training_sessions

    training_info = Node(niu.Function(
        input_names=["df", "query_subject_idx", "training_subject_idx"],
        output_names=["training_subject_idx", "training_subject_nums_str", "training_subjects", "training_sessions"],
        function=get_training_info_fnc), name="training_info")
    training_info.inputs.df = df
    training_info.inputs.training_subject_idx = training_subject_idx
    wf.connect(inputnode, "query_subject_idx", training_info, "query_subject_idx")

    bianca = Node(BIANCA(), name="bianca")
    bianca.inputs.masterfile = str(masterfile)
    bianca.inputs.featuresubset = featuresubset
    bianca.inputs.brainmaskfeaturenum = brainmaskfeaturenum
    bianca.inputs.matfeaturenum = matfeaturenum
    bianca.inputs.save_classifier = save_classifier
    wf.connect(query_info, "query_subject_num", bianca, "querysubjectnum")

    if trained_classifier_file:
        bianca.inputs.trained_classifier_file = trained_classifier_file
    else:
        bianca.inputs.labelfeaturenum = labelfeaturenum
        wf.connect(training_info, "training_subject_nums_str", bianca, "trainingnums")

    def classifier_info_fct(masterfile, query_subject, query_session, query_flair, training_subjects=None,
                            training_sessions=None, classifier_file=None):
        d = {
            "masterfile": str(masterfile),
            "query_subject_session": [query_subject, query_session],
            "query_flair": query_flair,
        }
        if training_subjects:
            d["training_subjects_sessions"] = list(zip(training_subjects, training_sessions))
        else:
            d["classifier_file"] = classifier_file
        return d

    classifier_info = Node(niu.Function(
        input_names=["masterfile", "query_subject", "query_session", "query_flair", "training_subjects",
                     "training_sessions", "classifier_file"],
        output_names=["meta_dict"],
        function=classifier_info_fct), name="classifier_info")
    classifier_info.inputs.masterfile = masterfile
    wf.connect(query_info, "query_subject", classifier_info, "query_subject")
    wf.connect(query_info, "query_session", classifier_info, "query_session")
    wf.connect(query_info, "query_flair", classifier_info, "query_flair")
    if trained_classifier_file:
        classifier_info.inputs.classifier_file = trained_classifier_file
    else:
        wf.connect(training_info, "training_subjects", classifier_info, "training_subjects")
        wf.connect(training_info, "training_sessions", classifier_info, "training_sessions")

    ds = Node(DerivativesDataSink(base_directory=str(out_dir.parent), out_path_base=str(out_dir.name)), name="ds")
    ds.inputs.suffix = "LPM"
    wf.connect(bianca, "out_file", ds, "in_file")
    wf.connect(query_info, "query_flair", ds, "source_file")
    wf.connect(classifier_info, "meta_dict", ds, "meta_dict")

    if save_classifier:
        ds_clf = Node(DerivativesDataSink(base_directory=str(out_dir.parent), out_path_base=str(out_dir.name)),
                      name="ds_clf")
        ds_clf.inputs.suffix = "classifier"
        wf.connect(bianca, "classifier_file", ds_clf, "in_file")
        wf.connect(query_info, "query_flair", ds_clf, "source_file")

        ds_clf_labels = Node(DerivativesDataSink(base_directory=str(out_dir.parent), out_path_base=str(out_dir.name)),
                             name="ds_clf_labels")
        ds_clf_labels.inputs.suffix = "classifier_labels"
        wf.connect(bianca, "classifier_labels_file", ds_clf_labels, "in_file")
        wf.connect(query_info, "query_flair", ds_clf_labels, "source_file")

    wf.base_dir = wd_dir
    wf.config.remove_unnecessary_outputs = False
    wf.config["execution"]["crashdump_dir"] = crash_dir
    wf.config["monitoring"]["enabled"] = "true"
    # wf.write_graph("workflow_graph.png", graph2use="exec")
    # wf.write_graph("workflow_graph_c.png", graph2use="colored")
    wf.run(plugin='MultiProc', plugin_args={'n_procs': n_cpu})


def run_bianca(out_dir, wd_dir, crash_dir, n_cpu=4, save_classifier=False, trained_classifier_file=None,
               training_subject_idx=None, query_subject_idx=None):
    try:
        version_label = subprocess.check_output(["git", "describe", "--tags"]).strip()
        (out_dir / "pipeline_version.txt").write_text(f"git {version_label.decode()}")
    except:
        (out_dir / "pipeline_version.txt").write_text(bianca.__version__)

    masterfile = out_dir / "masterfile.txt"
    df = pd.read_csv(out_dir / "masterfile_wHeader.txt", sep=" ")

    ######
    # subject information
    if training_subject_idx is None:
        training_subject_idx = np.where(~df.manual_mask.isna())[0]
    if query_subject_idx is None:
        query_subject_idx = list(range(len(df)))

    run_bianca_wf(masterfile, out_dir, wd_dir, crash_dir, df, training_subject_idx, query_subject_idx,
                  n_cpu=n_cpu, save_classifier=save_classifier,
                  trained_classifier_file=trained_classifier_file)
