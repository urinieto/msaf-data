SPAM Features
=============

Due to github's file size limit, the features can be found in the following URL:
https://ccrma.stanford.edu/~urinieto/SPAM/SPAM-features.tgz

Terms of use
------------

**The SPAM features are provided for non-commercial research purposes only.**
They may not be used to build, train, or improve commercial products or services,
and models trained on them (including their weights) may not be used or distributed
for commercial purposes.

The features are computed from copyrighted commercial recordings that are owned by
third parties and are not distributed here. The MIT license of this repository
covers its code only; it does not apply to the features, and it does not grant
any rights to the underlying recordings. Some of the source recordings carry their
own terms (e.g., the RWC Music Database, used by `SALAMI_1562`). The features are
provided "as is", without warranty of any kind.

If you use them, please cite the publication listed in the [SPAM README](../README.md).

Provenance
----------

| | |
|---|---|
| File | `SPAM-features.tgz` |
| Size | 1,143,032,803 bytes |
| SHA-256 | `f3caa007c67f93b3ee2cab28632f88b431feb70f2b36e3b188f8293ec800652d` |
| MD5 | `e7bc1872cdba31c58f12a7b6a57b851f` |
| Computed | 2016-06-30, with MSAF 0.1.0, librosa 0.4.3, numpy 1.11.0 |
| Audio analysis | 22050 Hz, hop length of 1024 samples |

The archive contains 50 JSON files in the MSAF features format, one per track. Each
file is named like its JAMS file in `../references` (e.g., `SALAMI_12.json` and
`SALAMI_12.jams`). Each one includes:

* `globals`: the duration (`dur`) of the analyzed audio, its sample rate and hop length.
* `metadata`: the computation timestamp and library versions.
* `est_beats`: the beat times estimated with librosa.
* `cqt` (84 bins), `mfcc` (14 coefficients), `pcp` (12 bins), `tonnetz` (6 dimensions),
  and `tempogram` (192 lags), each with its `params` and with `framesync` and
  `est_beatsync` versions.

The feature durations match the `duration` column in `../metadata.tsv` and the
`file_metadata.duration` of the JAMS files: to within 1e-7 seconds for the SALAMI
and Cerulean tracks, and within 0.2 seconds for the Isophonics and Epiphyte tracks because of
differences in MP3 decoding.
