"""Merged lines split at their waist; a single line's hanging vowels do not."""

import cv2
import numpy as np

from BDRC.line_detection import split_tall_contours

WIDTH = 400


def _mask(*bands: tuple[int, int, float]) -> np.ndarray:
    """Line mask with (top, bottom, ink density) bands, joined by a 2px bridge."""
    mask = np.zeros((200, WIDTH), np.uint8)
    for top, bottom, density in bands:
        step = max(1, round(1 / density))
        mask[top:bottom, ::step] = 255
    mask[bands[0][0] : bands[-1][1], WIDTH // 2 : WIDTH // 2 + 2] = 255
    return mask


def _split(mask: np.ndarray) -> list[tuple[int, int]]:
    """Each resulting contour's (top, bottom) after splitting the masked region."""
    ys = np.nonzero(mask.any(axis=1))[0]
    contour = np.array(
        [[[0, ys[0]]], [[WIDTH - 1, ys[0]]], [[WIDTH - 1, ys[-1]]], [[0, ys[-1]]]], np.int32
    )
    parts = split_tall_contours(mask, [contour], 0.0)
    return sorted((y, y + h) for _, y, _, h in map(cv2.boundingRect, parts))


def test_two_merged_lines_split_in_two():
    """The live-capture case: the detector merges a pair of lines into one."""
    parts = _split(_mask((20, 60, 1.0), (66, 106, 1.0)))
    assert len(parts) == 2


def test_three_merged_lines_split_in_three():
    parts = _split(_mask((20, 60, 1.0), (66, 106, 1.0), (112, 152, 1.0)))
    assert len(parts) == 3


def test_hanging_vowels_under_one_line_stay_with_it():
    """Gyudsum Kongwa p1: a waist above sparse vowel tails stranded them as a sliver."""
    parts = _split(_mask((20, 68, 1.0), (73, 85, 0.03)))
    assert parts == [(20, 85)]


def test_a_sliver_below_merged_lines_joins_the_last_line():
    parts = _split(_mask((20, 60, 1.0), (66, 106, 1.0), (111, 121, 0.03)))
    assert len(parts) == 2
    assert parts[-1][1] == 121
