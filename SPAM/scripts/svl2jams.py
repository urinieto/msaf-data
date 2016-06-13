#!/usr/bin/env python
"""
Converts an svl file into a JAMS annotation
"""
from __future__ import print_function
import argparse
import librosa
import logging
import os
import time
import json
import xml.etree.ElementTree as ET

import jams

__author__ = "Oriol Nieto"
__copyright__ = "Copyright 2016, Music and Audio Research Lab (MARL)"
__license__ = "MIT"
__version__ = "1.1"
__email__ = "oriol@nyu.edu"

ANNOTATORS = {
    "Colin": {
        "name": "Colin Hua",
        "email": "colin.z.hua@gmail.com"
    },
    "Eleni": {
        "name": "Eleni Vasilia Maltas",
        "email": "evm241@nyu.edu"
    },
    "Evan": {
        "name": "Evan S. Johnson",
        "email": "esj254@nyu.edu"
    },
    "John": {
        "name": "John Turner",
        "email": "johnturner@me.com"
    },
    "Shuli": {
        "name": "Shuli Tang",
        "email": "luiseslt@gmail.com"
    }
}


def create_annotation(root, annotator_id, jam_file, namespace):
    """Creates an annotation from the given root of an XML svl file."""
    # Load jam file
    jam = jams.load(jam_file)

    # Get the annotation parameters from the SV model
    model = root.iter('model').next()

    sr = float(model.attrib['sampleRate'])
    ann_time = float(model.attrib['start']) / sr
    ann_duration = float(model.attrib['end']) / sr - ann_time

    # Create Annotation
    ann = jams.Annotation(namespace=namespace,
                          time=ann_time,
                          duration=ann_duration)

    # Create Annotation Metadata
    ann.annotation_metadata = jams.AnnotationMetadata(
        corpus="SPAM dataset", data_source="Human Expert", version="1.0",
        annotation_rules="SALAMI")
    ann.annotation_metadata.annotation_tools = "Sonic Visualiser"
    ann.annotation_metadata.curator = jams.Curator(
        name="Oriol Nieto", email="oriol@nyu.edu")
    ann.annotation_metadata.annotator = {
        "name": ANNOTATORS[annotator_id]["name"],
        "email": ANNOTATORS[annotator_id]["email"]
    }


    # Create datapoints from the XML root
    boundaries = []
    labels = []

    for boundary in root.iter('point'):
        # Convert from frames to time
        boundaries.append(float(boundary.attrib['frame']) / sr)

        # strip out spaces
        labels.append(boundary.attrib['label'].replace(' ', ''))

    # Pad to the full range [ann_time, ann_time + ann_duration]
    if min(boundaries) > ann_time:
        boundaries.insert(0, ann_time)
        labels.insert(0, 'Silence')

    if max(boundaries) < ann_time + ann_duration:
        boundaries.append(ann_time + ann_duration)
        labels.append('Silence')

    # Adjust the capitalization
    if namespace == 'segment_salami_lower':
        labels = [_.lower() for _ in labels]
    elif namespace == 'segment_salami_upper':
        labels = [_.upper() for _ in labels]

    for start, end, label in zip(boundaries[:-1], boundaries[1:], labels):
        # Only include intervals with positive duration
        dur = end - start
        if dur > 0:
            ann.append(time=start, duration=dur,
                       value=label, confidence=1)

    # Add annotation to JAMS
    jam.annotations.append(ann)

    # Save file
    jam.save(jam_file)


def sv_to_audio_path(sv_file, audio_folder):
    """Converts a sonic visualiser name file to an audio for the SPAM
    dataset."""
    return os.path.join(audio_folder,
                        "SPAM_" + os.path.basename(sv_file)[:-6] + ".mp3")


def create_jams(out_file, audio_file):
    """Creates a new JAMS file in out_file for the SPAM dataset."""
    # Get duration
    y, fs = librosa.load(audio_file)
    dur = len(y) / float(fs)

    # Create the actual jams object and add some metadata
    jam = jams.JAMS()
    jam.file_metadata.duration = dur

    # Save to disk
    jam.save(out_file)


def process(in_file, out_file="output.jams", audio_folder="audio"):
    """Main process to convert an svl file to JAMS."""
    # If the output jams doesn't exist, create it:
    audio_file = sv_to_audio_path(in_file, audio_folder)
    if not os.path.isfile(out_file):
        create_jams(out_file, audio_file)

    # Parse svl file (XML)
    tree = ET.parse(in_file)
    root = tree.getroot()

    # Retrieve context from in_file name
    namespaces = {
        "s": "segment_salami_lower",
        "l": "segment_salami_upper"
    }
    namespace_id = in_file[:-4].split("_")[-1].lower()

    # Retrieve annotator id from in_file name
    annotator_id = os.path.basename(os.path.dirname(in_file))

    # Create Annotation
    create_annotation(root, annotator_id, out_file, namespaces[namespace_id])


def main():
    """Main function to convert the annotation."""
    parser = argparse.ArgumentParser(
        description="Converts a Sonic Visualizer segment annotation into a "
        "JAMS file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_path",
                        action="store",
                        help="Input svl file.")
    parser.add_argument("-o",
                        action="store",
                        dest="out_file",
                        help="Output file",
                        default="output.jams")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                        level=logging.INFO)

    # Run the algorithm
    process(args.in_path, out_file=args.out_file)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))

if __name__ == '__main__':
    main()
