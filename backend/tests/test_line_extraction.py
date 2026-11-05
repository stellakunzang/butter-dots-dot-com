"""First-line extraction must not swallow a pecha frame above the text."""

import numpy as np

from BDRC.line_detection import (
    build_line_data,
    extract_line_images,
    first_line_top_bound,
    rule_bottom_above,
    whiten_rule_above,
)


def _rect_line(x: int, y: int, w: int, h: int):
    contour = np.array(
        [[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]],
        dtype=np.int32,
    )
    return build_line_data(contour, optimize=False)


def _page(rule_rows: slice = None, rule_value: int = 0) -> np.ndarray:
    image = np.full((160, 400, 3), 255, np.uint8)
    if rule_rows is not None:
        image[rule_rows, :] = rule_value
    image[40:60, 20:380] = (40, 40, 40)
    image[90:110, 20:380] = (40, 40, 40)
    return image


def test_rule_bottom_is_the_row_below_the_lowest_rule():
    image = _page()
    image[8:10, :] = 0
    image[20:22, :] = 0
    assert rule_bottom_above(image, 20, 40, 360) == 22


def test_a_thin_gray_photo_rule_counts():
    assert rule_bottom_above(_page(slice(30, 32), 150), 20, 40, 360) == 32


def test_marks_above_the_line_are_not_a_rule():
    image = _page()
    for x in range(30, 370, 40):  # gi-gu sized marks, ~20px above the box
        image[22:28, x : x + 12] = 0
    assert rule_bottom_above(image, 20, 40, 360) == 0
    assert whiten_rule_above(image, 20, 40, 360) is image


def test_whitening_keeps_marks_below_the_rule():
    image = _page(slice(8, 16))
    image[30:36, 50:60] = 0
    painted = whiten_rule_above(image, 20, 40, 360)
    assert painted[8:16].min() == 255
    assert painted[30:36, 50:60].max() == 0
    assert image[8:16].max() == 0, "source image must not be modified"


def test_first_line_crop_paints_out_a_top_rule_without_changing_its_shape():
    lines = [_rect_line(20, 40, 360, 20), _rect_line(20, 90, 360, 20)]
    with_rule = extract_line_images(_page(slice(8, 16)), lines, default_k=2.5, bbox_tolerance=3.0)
    without = extract_line_images(_page(), lines, default_k=2.5, bbox_tolerance=3.0)

    assert [c.shape for c in with_rule] == [c.shape for c in without]
    black_rows = np.all(with_rule[0] == 0, axis=(1, 2))
    assert not np.any(black_rows), "top rule leaked into the first-line crop"


def test_first_line_reaches_one_median_gap_above_its_box():
    lines = [
        _rect_line(20, 60, 360, 20),
        _rect_line(20, 100, 360, 20),
        _rect_line(20, 144, 360, 20),
    ]
    # boxes are 21px tall (boundingRect is inclusive), so gaps are 19 and 23 → median 21
    assert first_line_top_bound(lines, 60) == 39


def test_single_line_page_keeps_the_upstream_unbounded_top():
    assert first_line_top_bound([_rect_line(20, 60, 360, 20)], 60) == 0


def test_blank_margin_above_the_first_line_is_cut_like_any_other_line():
    image = np.full((200, 400, 3), 255, np.uint8)
    image[100:120, 20:380] = (40, 40, 40)
    image[150:170, 20:380] = (40, 40, 40)
    image[10:12, 20:380] = (200, 200, 200)  # faint mark far above, outside the reach
    lines = [_rect_line(20, 100, 360, 20), _rect_line(20, 150, 360, 20)]
    crops = extract_line_images(image, lines, default_k=2.5, bbox_tolerance=3.0)
    assert crops[0].shape[0] < crops[1].shape[0] + 30
    assert not np.any(np.all(crops[0] == 200, axis=(1, 2)))
