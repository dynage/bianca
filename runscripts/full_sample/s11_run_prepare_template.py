from pathlib import Path
from bianca.workflows.prepare_template import prepare_template
from bianca.utils import get_subject_sessions

bids_dir = "/home/fliem/lhab_data/LHAB/LHAB_v2.0.0/sourcedata"
smriprep_dir = "/home/fliem/lhab_data/LHAB/LHAB_v1.1.1/derivates/fmriprep_1.0.5_wSTC/fmriprep"
name = "prepare_template"

base_dir = Path("/home/fliem/lhab_collaboration/WMH/BIANCA/full_sample/")

out_dir = base_dir / name
# wd_dir = base_dir / "_wd" / name
wd_dir = Path("/tmp/fl/full_sample/") / "_wd" / name
crash_dir = base_dir / "_crash" / name

####
# collect flair subjects
# subjects_sessions = get_subject_sessions(bids_dir, "*")
# subjects, _ = list(zip(*subjects_sessions))
# subjects = list(set(subjects))

#
# b1 = ['lhabX0104', 'lhabX0105', 'lhabX0106', 'lhabX0107', 'lhabX0108', 'lhabX0109', 'lhabX0111', 'lhabX0112',
#       'lhabX0113', 'lhabX0114', 'lhabX0115', 'lhabX0116', 'lhabX0117', 'lhabX0118', 'lhabX0119', 'lhabX0120',
#       'lhabX0121', 'lhabX0122', 'lhabX0123', 'lhabX0124', 'lhabX0126', 'lhabX0127', 'lhabX0128', 'lhabX0129',
#       'lhabX0130', 'lhabX0131', 'lhabX0132', 'lhabX0133', 'lhabX0134', 'lhabX0135', 'lhabX0136', 'lhabX0137',
#       'lhabX0138', 'lhabX0139', 'lhabX0140', 'lhabX0141', 'lhabX0142', 'lhabX0143', 'lhabX0144', 'lhabX0145',
#       'lhabX0146', 'lhabX0147', 'lhabX0148', 'lhabX0149', 'lhabX0150', 'lhabX0151', 'lhabX0153',
#       'lhabX0154', 'lhabX0155', 'lhabX0156', 'lhabX0157', 'lhabX0158', 'lhabX0159', 'lhabX0160', 'lhabX0161',
#       'lhabX0162', 'lhabX0163', 'lhabX0164', 'lhabX0165', 'lhabX0166', 'lhabX0167', 'lhabX0168', 'lhabX0169',
#       'lhabX0170', 'lhabX0171', 'lhabX0172', 'lhabX0173', 'lhabX0174', 'lhabX0175', 'lhabX0176', 'lhabX0177',
#       'lhabX0178', 'lhabX0179', 'lhabX0180', 'lhabX0181', 'lhabX0182', 'lhabX0183', 'lhabX0184', 'lhabX0185',
#       'lhabX0186', 'lhabX0187', 'lhabX0188', 'lhabX0189', 'lhabX0190', 'lhabX0191', 'lhabX0192', 'lhabX0193',
#       'lhabX0194', 'lhabX0195', 'lhabX0197', 'lhabX0198', 'lhabX0199', 'lhabX0200', 'lhabX0201', 'lhabX0202',
#       'lhabX0203', 'lhabX0204', 'lhabX0205', 'lhabX0206', 'lhabX0207', 'lhabX0208', 'lhabX0209', 'lhabX0210',
#       'lhabX0211', 'lhabX0212', 'lhabX0213', 'lhabX0214', 'lhabX0215', 'lhabX0216', 'lhabX0217', 'lhabX0218',
#       'lhabX0219', 'lhabX0220', 'lhabX0221', 'lhabX0222', 'lhabX0223', 'lhabX0224', 'lhabX0225', 'lhabX0226',
#       'lhabX0227', 'lhabX0228', 'lhabX0229', 'lhabX0230', 'lhabX0231', 'lhabX0232']
# subjects = b1

b2 = ['lhabX0001', 'lhabX0002', 'lhabX0003', 'lhabX0004', 'lhabX0005', 'lhabX0006', 'lhabX0007', 'lhabX0008',
      'lhabX0009', 'lhabX0010', 'lhabX0011', 'lhabX0012', 'lhabX0013', 'lhabX0014', 'lhabX0015', 'lhabX0016',
      'lhabX0017', 'lhabX0018', 'lhabX0019', 'lhabX0020', 'lhabX0021', 'lhabX0022', 'lhabX0023', 'lhabX0024',
      'lhabX0025', 'lhabX0026', 'lhabX0027', 'lhabX0028', 'lhabX0029', 'lhabX0030', 'lhabX0031', 'lhabX0032',
      'lhabX0033', 'lhabX0034', 'lhabX0035', 'lhabX0036', 'lhabX0037', 'lhabX0038', 'lhabX0039', 'lhabX0040',
      'lhabX0041', 'lhabX0042', 'lhabX0043', 'lhabX0044', 'lhabX0045', 'lhabX0046', 'lhabX0047', 'lhabX0048',
      'lhabX0049', 'lhabX0050', 'lhabX0051', 'lhabX0052', 'lhabX0053', 'lhabX0054', 'lhabX0055', 'lhabX0056',
      'lhabX0057', 'lhabX0058', 'lhabX0059', 'lhabX0060', 'lhabX0061', 'lhabX0062', 'lhabX0063',
      'lhabX0065', 'lhabX0066', 'lhabX0068', 'lhabX0069', 'lhabX0070', 'lhabX0071', 'lhabX0072',
      'lhabX0073', 'lhabX0074', 'lhabX0075', 'lhabX0076', 'lhabX0077', 'lhabX0078', 'lhabX0079', 'lhabX0080',
      'lhabX0081', 'lhabX0082', 'lhabX0083', 'lhabX0084', 'lhabX0085', 'lhabX0086', 'lhabX0087', 'lhabX0088',
      'lhabX0089', 'lhabX0090', 'lhabX0091', 'lhabX0093', 'lhabX0094', 'lhabX0095', 'lhabX0096',
      'lhabX0097', 'lhabX0098', 'lhabX0099', 'lhabX0100', 'lhabX0101', 'lhabX0102', 'lhabX0103', 'lhabX0152']
subjects = b2

# missing=["lhabX0196","lhabX0125"]
#missing=["lhabX0092","lhabX0064","lhabX0067"]

subjects.sort()
print(subjects)
print(f"\n{len(subjects)} subjects\n")
prepare_template(bids_dir, smriprep_dir, out_dir, wd_dir, crash_dir, subjects, n_cpu=25, omp_nthreads=1)
