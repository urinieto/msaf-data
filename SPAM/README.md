Structural Poly Annotations of Music
====================================

The SPAM dataset contains 5 human annotations of music structural segmentation for each of its 50 tracks.
The tracks are divided into two subcorpuses: _challenging_ (45) and _simple_ (5).
Please, refer to the original publication for more information (see "Publications" below).

Annotations
-----------

The annotations are found in the `references` folder, and are stored using the JAMS format.
Each JAMS file contains the 5 different human annotations and a `sandbox` key where the `genre` and the `subcorpus` (_challenging_ or _simple_) can be found.
Moreover, a `metadata.tsv` file is also available containing all the metadata on the JAMS for quick access.

The JAMS files are generated from the original Sonic Visualiser annotations in `original_references`
by running `python3 scripts/rebuild_references.py` (use `--check` to compare against the existing files).

Features
--------

In order to not depend on the actual (copyrighted) audio, a set of features have been computed using
[MSAF](https://github.com/urinieto/msaf).
Due to their size, they are hosted externally: see [`features/README.md`](features/README.md) for the download link,
checksums, and provenance details.
These are stored in a JSON file using the MSAF format, one per track.

The available features are the following:

* Constant-Q Transform (`cqt`)
* Mel Frequency Cepstral Coefficients (`mfcc`)
* Pitch Class Profiles (`pcp`)
* Tempograms (`tempogram`)
* Tonal Centroids (`tonnetz`)

Additionally, beat-synchronous features are also included for each one of these features, using estimated beat times using [librosa](https://github.com/librosa/librosa).

**The features are provided for non-commercial research purposes only.**
They may not be used for commercial applications, including training models for commercial use.
The MIT license of this repository applies to its code, not to the features or to the copyrighted recordings they were computed from.
See [`features/README.md`](features/README.md) for the full terms.

Changelog
---------

* **v1.2 (2026-11):** Fixed the metadata of the 32 SALAMI tracks, which had been shuffled since June 2016 (the
  numerically sorted rows of `metadata.tsv` had received the metadata of the alphabetically sorted tracks).
  This affected the `artist`, `title`, `release`, `duration`, `musicbrainzid`, and URL fields of
  `metadata.tsv` and of the JAMS `file_metadata`. Because the annotations are padded or trimmed to the track
  duration, the wrong durations had also stretched or cut the end of most SALAMI annotations and
  prevented many `multi_segment` annotations from being created. The SALAMI JAMS files have been rebuilt
  from the original annotations with the corrected metadata. The other 18 tracks and the features
  were not affected.
  The `version` in the `annotation_metadata` of all JAMS files is now `1.2`.
* **v1.1 (2016-06):** Added the metadata, the upper/lower alignment, and the `multi_segment` annotations.

Publications
------------

Nieto, O., Bello, J. P., Systematic Exploration Of Computational Music Structure Research. Proc. of the 17th International Society for Music Information Retrieval Conference (ISMIR). New York City, NY, USA, 2016 ([PDF](http://marl.smusic.nyu.edu/nieto/publications/ISMIR2016-NietoBello.pdf)).
