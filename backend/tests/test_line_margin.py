"""Line crops whose ink would touch the model window's edges get a white band."""

import numpy as np

from BDRC.Inference import TARGET_FILL, add_vertical_margin

WINDOW = (3200, 100)


def _line(height: int, width: int, ink_rows: slice) -> np.ndarray:
    image = np.full((height, width, 3), 255, np.uint8)
    image[ink_rows, 10:-10] = 30
    return image


def test_ink_touching_both_edges_is_padded_back_to_target_fill():
    image = _line(40, 1100, slice(0, 40))
    padded = add_vertical_margin(image, *WINDOW)
    pad = (padded.shape[0] - 40) // 2
    assert 40 / padded.shape[0] <= TARGET_FILL
    assert padded[:pad].min() == 255
    assert padded[-pad:].min() == 255


def test_crop_with_room_above_and_below_is_unchanged():
    image = _line(100, 3300, slice(15, 85))
    assert add_vertical_margin(image, *WINDOW) is image


def test_stray_mark_narrower_than_a_line_is_unchanged():
    image = _line(31, 113, slice(0, 31))
    assert add_vertical_margin(image, *WINDOW) is image


def test_masked_out_black_is_not_counted_as_ink():
    image = _line(40, 1100, slice(10, 30))
    image[:4] = 0
    image[-4:] = 0
    assert add_vertical_margin(image, *WINDOW) is image


def test_single_channel_image_stays_single_channel():
    image = np.full((40, 1100), 255, np.uint8)
    image[:, 10:-10] = 30
    padded = add_vertical_margin(image, *WINDOW)
    assert padded.ndim == 2
    assert padded.shape[0] > 40
