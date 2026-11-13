#!/usr/bin/env python3
"""
Rebuilds the SPAM JAMS references from the original Sonic Visualiser (svl)
annotations and the metadata file, using only the Python 3 standard library.

This reproduces the original v1.1 pipeline:

1. ``parse_annotations.py`` / ``svl2jams.py``: convert every svl file into a
   ``segment_salami_upper`` or ``segment_salami_lower`` annotation and store the
   track metadata from ``metadata.tsv``.
2. ``SPAM annotation correction.ipynb`` (by Brian McFee): pad or trim every
   segmentation to the track duration, align the upper-level boundaries to the
   lower-level ones, and add a merged ``multi_segment`` annotation per
   annotator.

The original pipeline ran on Python 2 with jams 0.2.1 and pandas 0.18, which
stored times as ``Timedelta`` values rounded to the microsecond. That
arithmetic is emulated here (see ``to_ns``/``to_sec``), so the output matches
the original JAMS files exactly, except for the metadata fix below.

Running with ``--check`` compares the rebuilt annotations with the JAMS files
currently in ``references`` without writing anything. The only expected
differences are a few 1-microsecond ones in Epiphyte_0723_hotelroomservice:
pandas 0.18 parsed its duration (237.2963265) one ULP off, as
237.29632650000002, which shifts the rounding of its last segments.
"""
import argparse
import collections
import csv
import glob
import json
import logging
import os
import xml.etree.ElementTree as ET

__author__ = "Oriol Nieto"
__license__ = "MIT"

# Version of the SPAM annotations (1.1: original release, 1.2: fixed the
# shuffled SALAMI metadata)
VERSION = "1.2"

SPAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ANNOTATORS = {
    "Colin": {"name": "Colin Hua", "email": ""},
    "Eleni": {"name": "Eleni Vasilia Maltas", "email": ""},
    "Evan": {"name": "Evan S. Johnson", "email": ""},
    "John": {"name": "John Turner", "email": ""},
    "Shuli": {"name": "Shuli Tang", "email": ""},
}
NAMESPACES = {"s": "segment_salami_lower", "l": "segment_salami_upper"}
PAD_LABELS = {"segment_salami_upper": ("YYYYY", "ZZZZZ"),
              "segment_salami_lower": ("yyyyy", "zzzzz")}

# Tolerances from the correction notebook
TOLERANCE = 0.1         # padding tolerance (seconds)
ALIGN_TOLERANCE = 3.0   # upper/lower alignment tolerance (seconds)


def to_ns(seconds):
    """Seconds to nanoseconds, as pandas 0.18 did for unit='s' (6 decimals)."""
    base = int(seconds)
    frac = round(seconds - base, 6)
    return base * 10 ** 9 + int(frac * 10 ** 9)


def to_sec(ns):
    """Nanoseconds to seconds, as jams 0.2.1 serialized Timedelta columns."""
    return 1e-9 * ns


class AnnotationError(Exception):
    pass


def read_metadata(metadata_file):
    """Reads the metadata file, keyed by the track name (no extension)."""
    with open(metadata_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return collections.OrderedDict(
        (r["File Name"].replace("/", ":")[:-4], r) for r in rows)


def parse_svl(svl_file, namespace):
    """Parses an svl file into a segmentation (svl2jams.create_annotation).

    Returns the annotation time and duration (in seconds) and a list of
    observations [time_ns, duration_ns, label, confidence].
    """
    root = ET.parse(svl_file).getroot()
    model = next(root.iter("model"))
    sr = float(model.attrib["sampleRate"])
    ann_time = float(model.attrib["start"]) / sr
    ann_duration = float(model.attrib["end"]) / sr - ann_time

    boundaries, labels = [], []
    for point in root.iter("point"):
        boundaries.append(float(point.attrib["frame"]) / sr)
        labels.append(point.attrib["label"].replace(" ", ""))

    # Pad to the full range [ann_time, ann_time + ann_duration]
    if min(boundaries) > ann_time:
        boundaries.insert(0, ann_time)
        labels.insert(0, "Silence")
    if max(boundaries) < ann_time + ann_duration:
        boundaries.append(ann_time + ann_duration)
        labels.append("Silence")

    if namespace == "segment_salami_lower":
        labels = [_.lower() for _ in labels]
    else:
        labels = [_.upper() for _ in labels]

    data = []
    for start, end, label in zip(boundaries[:-1], boundaries[1:], labels):
        dur = end - start
        if dur > 0:
            data.append([to_ns(start), to_ns(dur), label, 1.0])
    return ann_time, ann_duration, data


def span_segment(data, namespace, duration):
    """Pads or trims a segmentation to span [0, duration] (notebook)."""
    pre, post = PAD_LABELS[namespace]
    if any(t > to_ns(duration + 1.0) for t, _, _, _ in data):
        raise AnnotationError(
            "track length exceeded in observation: {:g}/{:g}".format(
                to_sec(max(t for t, _, _, _ in data)), duration))

    dur_ns = to_ns(duration)
    frame = [list(obs) for obs in data if obs[0] <= dur_ns]

    idx = min(range(len(frame)), key=lambda i: frame[i][0])
    min_time = frame[idx][0]
    if min_time > 0:
        if min_time <= to_ns(TOLERANCE) or frame[idx][2].lower() == "silence":
            frame[idx][0] = 0
        else:
            frame.append([0, to_ns(to_sec(min_time)), pre, 0.0])

    idx = max(range(len(frame)), key=lambda i: frame[i][0] + frame[i][1])
    max_time = frame[idx][0] + frame[idx][1]
    if max_time != dur_ns:
        if to_ns(duration - TOLERANCE) <= max_time or \
                frame[idx][2].lower() == "silence":
            frame[idx][1] = to_ns(duration - to_sec(frame[idx][0]))
        else:
            frame.append([to_ns(to_sec(max_time)),
                          to_ns(duration - to_sec(max_time)), post, 0.0])

    return sorted(frame, key=lambda obs: obs[0])


def match_events(events_from, events_to):
    """Index of the closest event in events_to (librosa.util.match_events)."""
    return [min(range(len(events_to)), key=lambda j: abs(e - events_to[j]))
            for e in events_from]


def align_annotations(upper, lower):
    """Snaps the upper boundaries to the lower ones (notebook)."""
    starts = [to_sec(t) for t, _, _, _ in upper]
    ends = [to_sec(t + d) for t, d, _, _ in upper]
    t_times = sorted({to_sec(x) for t, d, _, _ in lower for x in (t, t + d)})
    starts_adj = [t_times[i] for i in match_events(starts, t_times)]
    ends_adj = [t_times[i] for i in match_events(ends, t_times)]

    err = max(abs(a - s) for a, s in zip(starts_adj, starts))
    if err > ALIGN_TOLERANCE:
        raise AnnotationError("alignment error of {}s".format(err))

    return [[to_ns(s), to_ns(t - s), obs[2], obs[3]]
            for s, t, obs in zip(starts_adj, ends_adj, upper) if t > s]


def obs_to_json(obs, level=None):
    value = obs[2] if level is None else collections.OrderedDict(
        [("label", obs[2]), ("level", level)])
    return collections.OrderedDict([("duration", to_sec(obs[1])),
                                    ("confidence", obs[3]),
                                    ("value", value),
                                    ("time", to_sec(obs[0]))])


def annotation_metadata(annotator):
    return collections.OrderedDict([
        ("annotation_tools", "Sonic Visualiser"),
        ("curator", collections.OrderedDict([("name", "Oriol Nieto"),
                                             ("email", "oriol@nyu.edu")])),
        ("annotator", collections.OrderedDict([
            ("name", ANNOTATORS[annotator]["name"]),
            ("email", ANNOTATORS[annotator]["email"])])),
        ("version", VERSION),
        ("corpus", "SPAM dataset"),
        ("annotation_rules", "SALAMI"),
        ("validation", ""),
        ("data_source", "Human Expert")])


def make_annotation(namespace, annotator, time, duration, data):
    return collections.OrderedDict([
        ("namespace", namespace),
        ("sandbox", {}),
        ("time", time),
        ("duration", duration),
        ("annotation_metadata", annotation_metadata(annotator)),
        ("data", data)])


def file_metadata(meta):
    identifiers = collections.OrderedDict()
    for key in ("internet_archive_url", "musicbrainzid", "youtube_url"):
        if meta.get(key):
            identifiers[key] = meta[key]
    return collections.OrderedDict([
        ("jams_version", "0.2.1"),
        ("title", meta["title"]),
        ("identifiers", identifiers),
        ("release", meta["release"]),
        ("duration", float(meta["duration"])),
        ("artist", meta["artist"])])


def build_jams(track, meta, original_dir):
    """Builds the JAMS dictionary of a single track."""
    duration = float(meta["duration"])
    segments = []   # (namespace, annotator, annotation)
    corrected = collections.defaultdict(dict)
    for annotator in sorted(os.listdir(original_dir)):
        for suffix, namespace in sorted(NAMESPACES.items()):
            svl_file = os.path.join(original_dir, annotator,
                                    "{}_{}.svl".format(track, suffix))
            if not os.path.isfile(svl_file):
                continue
            ann_time, ann_dur, data = parse_svl(svl_file, namespace)
            try:
                data = span_segment(data, namespace, duration)
                corrected[annotator][namespace] = data
            except AnnotationError as exc:
                logging.warning("%s %s %s: %s", track, annotator, namespace,
                                exc)
            segments.append([namespace, annotator, ann_time, ann_dur, data])

    multi = []
    for annotator, anns in corrected.items():
        if len(anns) != 2:
            logging.warning("%s %s: align and merge failed", track, annotator)
            continue
        upper = anns["segment_salami_upper"]
        lower = anns["segment_salami_lower"]
        try:
            upper = align_annotations(upper, lower)
        except AnnotationError as exc:
            logging.warning("%s %s: %s", track, annotator, exc)
            continue
        for seg in segments:
            if seg[:2] == ["segment_salami_upper", annotator]:
                seg[4] = upper
        data = [obs_to_json(o, 0) for o in upper] + \
            [obs_to_json(o, 1) for o in lower]
        multi.append(("multi_segment", annotator,
                      make_annotation("multi_segment", annotator, 0, None,
                                      data)))

    annotations = [(ns, ann, make_annotation(ns, ann, t, d,
                                             [obs_to_json(o) for o in data]))
                   for ns, ann, t, d, data in segments] + multi
    return annotations, collections.OrderedDict([
        ("sandbox", collections.OrderedDict([("genre", meta["Genre"]),
                                             ("subcorpus", meta["subcorpus"])])),
        ("annotations", None),
        ("file_metadata", file_metadata(meta))])


def order_like(annotations, jams_file):
    """Keeps the annotation order of the existing JAMS file, if any."""
    if not os.path.isfile(jams_file):
        return [a for _, _, a in annotations]
    with open(jams_file) as f:
        old = json.load(f)
    names = {v["name"]: k for k, v in ANNOTATORS.items()}
    old_order = [(a["namespace"], names[a["annotation_metadata"]["annotator"]
                                        ["name"]]) for a in old["annotations"]]
    rank = {key: i for i, key in enumerate(old_order)}
    annotations = sorted(annotations,
                         key=lambda a: rank.get(a[:2], len(rank)))
    return [a for _, _, a in annotations]


def dumps(jam):
    """Serializes like Python 2's json.dump(indent=2)."""
    return json.dumps(jam, indent=2, separators=(", ", ": "))


def compare(new, old, path="", tol=1e-9):
    """Returns a list of differences between two JSON-like objects."""
    if isinstance(new, dict) and isinstance(old, dict):
        if set(new) != set(old):
            return ["{}: keys {} != {}".format(path, sorted(new), sorted(old))]
        return [d for k in new for d in compare(new[k], old[k],
                                                "{}/{}".format(path, k), tol)]
    if isinstance(new, list) and isinstance(old, list):
        if len(new) != len(old):
            return ["{}: length {} != {}".format(path, len(new), len(old))]
        return [d for i, (a, b) in enumerate(zip(new, old))
                for d in compare(a, b, "{}[{}]".format(path, i), tol)]
    if isinstance(new, float) or isinstance(old, float):
        if new is None or old is None or abs(new - old) > tol:
            return ["{}: {} != {}".format(path, new, old)]
        return []
    return [] if new == old else ["{}: {!r} != {!r}".format(path, new, old)]


def process(original_dir, out_dir, metadata_file, check=False, tracks=None):
    metadata = read_metadata(metadata_file)
    n_diff = 0
    for track, meta in metadata.items():
        if tracks and track not in tracks:
            continue
        out_file = os.path.join(out_dir, track + ".jams")
        annotations, jam = build_jams(track, meta, original_dir)
        jam["annotations"] = order_like(annotations, out_file)
        if check:
            with open(out_file) as f:
                old = json.load(f)
            diffs = compare(json.loads(dumps(jam)), old)
            if diffs:
                n_diff += 1
                logging.info("%s: %d differences, e.g. %s", track,
                             len(diffs), diffs[:3])
        else:
            with open(out_file, "w") as f:
                f.write(dumps(jam))
            logging.info("Wrote %s", out_file)
    if check:
        logging.info("%d/%d tracks differ from %s", n_diff,
                     len(tracks or metadata), out_dir)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original_dir",
                        default=os.path.join(SPAM_DIR, "original_references"))
    parser.add_argument("--out_dir",
                        default=os.path.join(SPAM_DIR, "references"))
    parser.add_argument("--metadata_file",
                        default=os.path.join(SPAM_DIR, "metadata.tsv"))
    parser.add_argument("--check", action="store_true",
                        help="Compare with the existing JAMS, do not write.")
    parser.add_argument("tracks", nargs="*",
                        help="Only process these tracks (default: all).")
    args = parser.parse_args()
    logging.basicConfig(format="%(levelname)s: %(message)s",
                        level=logging.INFO)
    process(args.original_dir, args.out_dir, args.metadata_file, args.check,
            args.tracks)


if __name__ == "__main__":
    main()
