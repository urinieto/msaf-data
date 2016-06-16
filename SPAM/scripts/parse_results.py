#!/usr/bin/env python
"""
Converts svl files into JAMS annotations.
"""
import argparse
import glob
import logging
import os
import time

import svl2jams

__author__ = "Oriol Nieto"
__copyright__ = "Copyright 2016, Music and Audio Research Lab (MARL)"
__license__ = "MIT"
__version__ = "1.1"
__email__ = "oriol@nyu.edu"


def ensure_dir(directory):
    """Makes sure that the given directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def process(original_dir, out_dir):
    """Main process to parse all the results from the results_dir
        to out_dir."""
    ensure_dir(out_dir)
    annotators = glob.glob(os.path.join(original_dir, "*"))
    for annotator in annotators:
        svl_files = glob.glob(os.path.join(annotator, "*.svl"))
        for svl_file in svl_files:
            out_file = os.path.join(out_dir, os.path.basename(svl_file)[:-6] +
                                    ".jams")
            logging.info("Parsing %s into %s" % (svl_file, out_file))
            svl2jams.process(svl_file, out_file)


def main():
    """Main function to parse the original annotations."""
    parser = argparse.ArgumentParser(
        description="Parse all the original annotations.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("original_dir",
                        action="store",
                        help="Original annotations directory")
    parser.add_argument("out_dir",
                        action="store",
                        help="Output annotation folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                        level=logging.INFO)

    # Run the algorithm
    process(args.original_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))

if __name__ == '__main__':
    main()
