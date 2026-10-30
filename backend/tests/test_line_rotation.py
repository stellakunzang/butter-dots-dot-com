"""Rotation estimated from the line mask stays inside the deskew limit.

OpenCV 4.9 reports a clockwise text line as an angle just under 90°. The
previous formula added 90 and turned that into a ~180° page flip. These masks
are the two shapes that showed up on the Padmasambhava and all-Tibetan photos.
"""

import cv2
import numpy as np

from BDRC.line_detection import (
    calculate_rotation_angle_from_lines,
    get_rotation_angle_from_lines,
)


def _line_mask(tilt_deg: float) -> np.ndarray:
    size = 800
    mask = np.zeros((size, size), np.uint8)
    for dy in (-80, -40, 0, 40, 80):
        rect = ((size / 2, size / 2 + dy), (500, 16), tilt_deg)
        box = cv2.boxPoints(rect).astype(np.int32)
        cv2.fillPoly(mask, [box], 255)
    return mask


def test_clockwise_line_is_a_small_negative_tilt():
    angle = get_rotation_angle_from_lines(_line_mask(-0.7))
    assert -2.0 < angle < 0.0


def test_counterclockwise_line_is_a_small_positive_tilt():
    angle = get_rotation_angle_from_lines(_line_mask(0.7))
    assert 0.0 < angle < 2.0


def test_correction_never_exceeds_the_deskew_limit():
    for tilt in (-3.0, -1.5, -0.7, 0.0, 0.7, 1.5, 3.0):
        angle = get_rotation_angle_from_lines(_line_mask(tilt))
        assert abs(angle) < 2.0, f"tilt {tilt} produced {angle}"


def test_horizontal_and_empty_masks_do_not_rotate():
    assert get_rotation_angle_from_lines(_line_mask(0.0)) == 0.0
    assert get_rotation_angle_from_lines(np.zeros((200, 200), np.uint8)) == 0.0


def test_both_entry_points_agree():
    mask = _line_mask(-1.5)
    assert get_rotation_angle_from_lines(mask) == calculate_rotation_angle_from_lines(
        mask
    )
