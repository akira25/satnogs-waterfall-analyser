#!/usr/bin/python3

from os import walk, path
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import argparse

#
# This script implements a fairly easy, but quite robust proof-of-concept, to
# vet a waterfall for whether it likely has a satellite signal in it. Wile it
# detects very reliably the true-positives, we omit the other classes for simplicity.
#
# Rough idea:
#
# 1. Analyse the green values of the waterfall across the center line (where satellite
# signals should be).
# 2. Detect and "filter" broadband noise by comparing to parallel lines at 1/4 and 3/4
# of the waterfall
# 3. Avoid detecting the wrong signal of other satellites "sweeping" through the
# waterfall, by analysing only upper and lower thrid of waterfall (leaving out middle)
#
# -> If in the remaining fields there are green-spikes that are greater than a certain
# threshould, we very likely detected the satellite we are looking for.
#
# © by Martin Hübner, 2025
#


def has_satellite_signal(path: str, plot_signal_strength: bool = False) -> bool:
    img = Image.open(path).convert("RGB")
    width, height = img.size

    # Place three vertical lines in waterfall
    x_centre = width // 2
    x_left = width // 4
    x_right = (width // 4) * 3
    line_width = 10

    # red_values = []
    green_values = []
    # blue_values = []

    # skip white margin
    margin_top = 12  # px
    margin_bottom = 54  # px

    # Calculate mean green value over line width for every row in the image
    for y in range(margin_top, height - margin_bottom):
        center_pixel_block = []
        left_pixel_block = []
        right_pixel_block = []

        # Center line: gather pixel for calculating the green mean value
        for dx in range(-(line_width // 2), (line_width // 2) + 1):
            x = x_centre + dx
            if 0 <= x < width:
                center_pixel_block.append(img.getpixel((x, y)))

        # Left control line: gather pixel
        for dx in range(-(line_width // 2), (line_width // 2) + 1):
            x = x_left + dx
            if 0 <= x < width:
                left_pixel_block.append(img.getpixel((x, y)))

        # Right control line: gather pixel
        for dx in range(-(line_width // 2), (line_width // 2) + 1):
            x = x_right + dx
            if 0 <= x < width:
                right_pixel_block.append(img.getpixel((x, y)))

        # into numpy array for convenient
        center_pixel_block = np.array(center_pixel_block)
        left_pixel_block = np.array(left_pixel_block)
        right_pixel_block = np.array(right_pixel_block)

        center_green_mean = center_pixel_block[:, 1].mean()
        left_green_mean = left_pixel_block[:, 1].mean()
        right_green_mean = right_pixel_block[:, 1].mean()

        # "filter" broadband noise by substracting values of control lines
        substr = np.mean([left_green_mean, right_green_mean])
        center_green_mean -= substr

        green_values.append(center_green_mean)

    #
    # Decider: God/Bad
    # To be considered a good observation, there should be two values that
    # are 25 (unit: something) above the general "noise" level
    #

    # Optimization idea: cut values above 25 and take mean of rest
    # noisefloor = np.array([ x for x in green_values if x <= 25]).mean()
    arr = np.array([x for x in green_values])
    noisefloor = arr.mean()

    # First criterion: There is a signal in first and third third of waterfall.
    # This omits classifying a "sweeping" signal to be considered successful
    [first, second, third] = np.array_split(arr, 3)

    has_likely_sat_signal: list[bool] = []
    maxima = []
    for arr in first, third:
        max_val = arr.max()
        maxima.append(max_val)
        if (max_val - noisefloor) > 25:
            has_likely_sat_signal.append(True)
        else:
            has_likely_sat_signal.append(False)

    print(has_likely_sat_signal, end="\t")
    print(noisefloor, end="\t")
    # print(maxima)
    # print("")

    if plot_signal_strength:
        plt.figure(figsize=(8, 4))
        plt.plot(green_values, label="Grün")
        plt.title(f"Mean green value at center line (Width {line_width} px)")
        plt.xlabel("Pixel position (y)")
        plt.ylabel("Intensity (mean on n Pixel)")
        plt.ylim(bottom=(-20), top=100)
        plt.legend()
        plt.tight_layout()
        filename = path.split(".")[0] + "_out.png"
        # print(f"Storing {filename}")
        plt.savefig(filename, dpi=300)
        plt.close()
        # plt.show()

    # Decide: We consider a observation only good, when it is safe to say
    # so: when there is likely a signal in the upper third and in the
    # lower third. Other waterfalls very likely hold observations too! These
    # should be vetted by hand though, as our approach is not reliable
    # enough for them.
    match has_likely_sat_signal:
        case [True, True]:
            print(True)
            return True
        case _:
            print(False)
            return False

    return likely_signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="satnogs-waterfall-analyser",
        description="A simple approach to automatically classify/vet satnogs-observations based on their waterfall."
    )
    parser.add_argument(
        "path", help="Path to a directory with satnogs waterfalls")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Stores a plot of detected signal level values, which lead to decision")
    parser.add_argument("-r", "--recurse", action="store_true",
                        help="Recurse into sub directories")
    parser.add_argument(
        "--process-only", help="Only processes files, which name contains the given substring")
    parser.add_argument(
        "--process-not", help="Processes files, which name *does not* contains the given substring")
    args = parser.parse_args()


    total = 0
    signal = 0
    no_signal = 0

    for root, dirs, files in walk(args.path):
        for file in files:
            if "out" in file:  # skip output visualisations
                continue
            if ".png" not in file:  # skip non pictures
                continue
            if args.process_only:
                if args.process_only not in file:
                    continue
            if args.process_not:
                if args.process_not in file:
                    continue

            print(path.join(root, file), end="\t")
            ret = has_satellite_signal(
                path.join(root, file), plot_signal_strength=args.debug)

            # count for statistics
            total += 1
            if ret:
                signal += 1
            else:
                no_signal += 1

        if not args.recurse:
            dirs.clear()

        if '__pycache__' in dirs:
            dirs.remove('__pycache__')  # don't visit __pycache__ directories

    #
    # Print summary
    #
    signal_percent = signal / (total / 100)
    no_signal_percent = no_signal / (total / 100)

    print(f"\nTotal:\t{total}")
    print(f"With Signal:\t{signal}\t{signal_percent:.2f}%")
    print(f"W/o Signal:\t{no_signal}\t{no_signal_percent:.2f}%")
