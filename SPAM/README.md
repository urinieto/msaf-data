Structural Poly Annotations of Music
====================================

The SPAM dataset contains 5 human annotations of music structural segmentation for each of its 50 tracks.
The tracks are divided into two subcorpuses: _challenging_ (45) and _simple_ (5).
Please, refer to the original publication for more information (see "Publications" below).

Annotations
-----------

The annotations are found in the `references` folder, and are stored using the JAMS format.
Each JAMS file contains the 5 different human annotations and a `sandbox` key where the `genre` and the `subcorpus` (_challenging_ or _simple_) can be found.
Moreover, a `metadata.csv` file is also available containing all the metadata on the JAMS for quick access.

Features
--------

In order to not depend on the actual (copyrighted) audio, a set of features have been computed using
[MSAF](https://github.com/urinieto/msaf), and are found inside the `features` directory.
These are stored in a JSON file using the MSAF format, one per track.

The available features are the following:

* Constant-Q Transform (`cqt)
* Mel Frequency Cepstral Coefficients (`mfcc`)
* Pitch Class Profiles (`pcp`)
* Tempograms (`tempograms`)
* Tonal Centroids (`tonnetz`)

Additionally, beat-synchronous feautures are also included for each one of these features, using estimated beat times using [librosa](https://github.com/librosa/librosa).

Publications
------------

Nieto, O., Bello, J. P., Systematic Exploration Of Computational Music Structure Research. Proc. of the 17th International Society for Music Information Retrieval Conference (ISMIR). New York City, NY, USA, 2016 ([PDF](http://marl.smusic.nyu.edu/nieto/publications/ISMIR2016-NietoBello.pdf)).
