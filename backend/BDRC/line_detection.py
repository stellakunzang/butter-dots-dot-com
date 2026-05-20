"""
Line detection and sorting utilities for OCR processing.

This module contains functions for:
- Line detection and contour analysis
- Line sorting and grouping algorithms
- Line image extraction and processing
- Rotation angle calculation from line orientations
"""

import cv2
import numpy as np
import numpy.typing as npt
from typing import List, Optional, Tuple, Sequence

from BDRC.Data import BBox, Line
from uuid import uuid1


def generate_guid(clock_seq: int):
    """
    Generate a UUID with a specific clock sequence.
    
    Args:
        clock_seq: Clock sequence value for UUID generation
        
    Returns:
        Generated UUID
    """
    return uuid1(clock_seq=clock_seq)


def get_contours(image: npt.NDArray) -> Sequence:
    """
    Find contours in a binary image.
    
    Args:
        image: Binary image array
        
    Returns:
        Sequence of detected contours
    """
    contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def optimize_countour(cnt, e=0.001):
    """
    Optimize contour by approximating with fewer points.
    
    Args:
        cnt: Input contour
        e: Epsilon factor for approximation
        
    Returns:
        Optimized contour
    """
    epsilon = e * cv2.arcLength(cnt, True)
    return cv2.approxPolyDP(cnt, epsilon, True)


def rotate_from_angle(image: np.array, angle: float) -> np.array:
    """
    Rotate image by a specified angle.
    
    Args:
        image: Input image array
        angle: Rotation angle in degrees
        
    Returns:
        Rotated image array
    """
    rows, cols = image.shape[:2]
    rot_matrix = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    rotated_img = cv2.warpAffine(image, rot_matrix, (cols, rows), borderValue=(0, 0, 0))
    return rotated_img


def mask_n_crop(image: np.array, mask: np.array) -> np.array:
    """
    Apply mask to image and crop to non-zero regions.
    
    Args:
        image: Input image array
        mask: Binary mask array
        
    Returns:
        Masked and cropped image
    """
    image = image.astype(np.uint8)
    mask = mask.astype(np.uint8)

    if len(image.shape) == 2:
        image = np.expand_dims(image, axis=-1)

    image_masked = cv2.bitwise_and(image, image, mask, mask)
    image_masked = np.delete(
        image_masked, np.where(~image_masked.any(axis=1))[0], axis=0
    )
    image_masked = np.delete(
        image_masked, np.where(~image_masked.any(axis=0))[0], axis=1
    )

    return image_masked


def get_rotation_angle_from_lines(
    line_mask: npt.NDArray,
    max_angle: float = 2.0,
    debug_angles: bool = False,
) -> float:
    """
    Calculate rotation angle from detected lines in a mask.
    
    Args:
        line_mask: Binary mask containing line detections
        max_angle: Maximum angle threshold for filtering
        debug_angles: Whether to print angle information
        
    Returns:
        Mean rotation angle in degrees
    """
    contours, _ = cv2.findContours(line_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    mask_threshold = (line_mask.shape[0] * line_mask.shape[1]) * 0.001
    contours = [x for x in contours if cv2.contourArea(x) > mask_threshold]
    angles = [cv2.minAreaRect(x)[2] for x in contours]

    low_angles = [x for x in angles if abs(x) != 0.0 and abs(x) < max_angle]
    # Modern OpenCV returns angles in [-90°, 0°), so near-90° tilts come back as
    # e.g. -88.6° rather than +88.6°.  Use abs() so both signs are caught.
    high_angles = [x for x in angles if abs(x) != 90.0 and abs(x) > (90 - max_angle)]

    if debug_angles:
        print(f"All Angles: {angles}")

    if len(low_angles) > len(high_angles) and len(low_angles) > 0:
        mean_angle = np.mean(low_angles)
    # check for clockwise rotation (near-90° angles encode small tilt as 90+angle)
    elif len(high_angles) > 0:
        mean_angle = 90 + np.mean(high_angles)
    else:
        mean_angle = 0

    return mean_angle


def calculate_rotation_angle_from_lines(
    line_mask: npt.NDArray,
    max_angle: float = 2.0,
    debug_angles: bool = False,
) -> float:
    """
    Calculate rotation angle from detected lines with improved handling.
    
    Args:
        line_mask: Binary mask containing line detections
        max_angle: Maximum angle threshold for filtering
        debug_angles: Whether to print angle information
        
    Returns:
        Mean rotation angle in degrees
    """
    contours, _ = cv2.findContours(line_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    mask_threshold = (line_mask.shape[0] * line_mask.shape[1]) * 0.001
    contours = [x for x in contours if cv2.contourArea(x) > mask_threshold]
    
    # Check if contours is empty before proceeding
    if not contours:
        return 0.0
        
    angles = [cv2.minAreaRect(x)[2] for x in contours]

    low_angles = [x for x in angles if abs(x) != 0.0 and abs(x) < max_angle]
    # Modern OpenCV returns angles in [-90°, 0°), so near-90° tilts come back as
    # e.g. -88.6° rather than +88.6°.  Use abs() so both signs are caught.
    high_angles = [x for x in angles if abs(x) != 90.0 and abs(x) > (90 - max_angle)]

    if debug_angles:
        print(f"All Angles: {angles}")

    if len(low_angles) > len(high_angles) and len(low_angles) > 0:
        mean_angle = np.mean(low_angles)
    # check for clockwise rotation (near-90° angles encode small tilt as 90+angle)
    elif len(high_angles) > 0:
        mean_angle = 90 + np.mean(high_angles)
    else:
        mean_angle = 0.0

    return mean_angle


def build_line_data(contour: np.array, optimize: bool = True) -> Line:
    """
    Create a Line object from a contour with bounding box and center information.
    
    Args:
        contour: Contour points array
        optimize: Whether to optimize the contour shape
        
    Returns:
        Line object with GUID, contour, bounding box, and center point
    """
    if optimize:
        contour = optimize_countour(contour)

    x, y, w, h = cv2.boundingRect(contour)

    x_center = x + (w // 2)
    y_center = y + (h // 2)

    bbox = BBox(x, y, w, h)
    guid = generate_guid(clock_seq=23)
    return Line(guid, contour, bbox, (x_center, y_center))


def build_raw_line_data(image: npt.NDArray, line_mask: npt.NDArray):
    """
    Process raw line detection data by rotating and extracting contours.
    
    Args:
        image: Input image array
        line_mask: Binary mask of detected lines
        
    Returns:
        Tuple of (rotated_image, rotated_mask, line_contours, rotation_angle)
    """
    if len(line_mask.shape) == 3:
        line_mask = cv2.cvtColor(line_mask, cv2.COLOR_BGR2GRAY)

    angle = get_rotation_angle_from_lines(line_mask)
    rot_mask = rotate_from_angle(line_mask, angle)
    rot_img = rotate_from_angle(image, angle)

    line_contours = get_contours(rot_mask)
    line_contours = [x for x in line_contours if cv2.contourArea(x) > 10]

    rot_mask = cv2.cvtColor(rot_mask, cv2.COLOR_GRAY2RGB)

    return rot_img, rot_mask, line_contours, angle


def _find_valley_rows(smoothed: np.ndarray, h: int) -> List[int]:
    """
    Find row indices where a vertical projection has significant valleys.

    A valley qualifies as a split point if its prominence (depth below the
    minimum of the left and right surrounding peaks within ±30 rows) is at
    least 25% of the global peak value.  Nearby valleys are deduplicated by
    keeping only the deepest one in each 15-row neighbourhood.
    """
    n = len(smoothed)
    if n < 20:
        return []

    peak_val = float(np.max(smoothed))
    if peak_val == 0:
        return []

    # Search only in the middle 80% of the contour to avoid edge artefacts
    search_start = max(1, n // 10)
    search_end   = min(n - 2, 9 * n // 10)

    valleys = []
    for i in range(search_start, search_end):
        if smoothed[i] > smoothed[i - 1] or smoothed[i] > smoothed[i + 1]:
            continue  # not a local minimum

        left_arr  = smoothed[max(0, i - 30):i]
        right_arr = smoothed[i + 1:min(n, i + 30)]
        if left_arr.size == 0 or right_arr.size == 0:
            continue

        local_peak = min(float(np.max(left_arr)), float(np.max(right_arr)))
        prominence = local_peak - float(smoothed[i])
        if local_peak > 0 and prominence >= 0.25 * local_peak:
            valleys.append((i, float(smoothed[i])))

    if not valleys:
        return []

    # Merge valleys within 15 rows of each other — keep the deepest in each group
    merged: List[Tuple[int, float]] = []
    group = [valleys[0]]
    for v in valleys[1:]:
        if v[0] - group[-1][0] <= 15:
            group.append(v)
        else:
            merged.append(min(group, key=lambda x: x[1]))
            group = [v]
    merged.append(min(group, key=lambda x: x[1]))

    return [v[0] for v in merged]


def split_tall_contours(
    line_mask: npt.NDArray,
    contours: List,
    max_line_height_ratio: float = 0.08,
) -> List:
    """
    Split contours that are taller than a single text line.

    When the line-detection model produces masks with thin pixel bridges
    between adjacent lines, cv2.findContours merges them into a single tall
    contour.  This function detects such contours (height > image_height *
    max_line_height_ratio) and splits them at the deepest valley in their
    vertical projection, returning separate contours for each sub-line.

    Args:
        line_mask:              Binary (or 3-channel) line-detection mask,
                                in the same coordinate space as *contours*.
        contours:               Contour list from filter_line_contours.
        max_line_height_ratio:  Contours with h > image_height * this value
                                are candidates for splitting (default 0.08 ≈ 8%).

    Returns:
        New contour list with tall merged contours replaced by their parts.
    """
    if not contours:
        return contours

    # Work with a 2-D binary mask
    if len(line_mask.shape) == 3:
        gray_mask = cv2.cvtColor(line_mask, cv2.COLOR_RGB2GRAY)
    else:
        gray_mask = line_mask.copy()

    img_height  = gray_mask.shape[0]
    max_line_h  = img_height * max_line_height_ratio

    result: List = []
    split_count = 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if h <= max_line_h:
            result.append(cnt)
            continue

        # ── Build projection of the original mask pixels under this contour ──
        tmp_mask = np.zeros(gray_mask.shape[:2], dtype=np.uint8)
        cv2.drawContours(tmp_mask, [cnt], -1, 255, -1)
        combined = cv2.bitwise_and(tmp_mask, gray_mask)
        region   = combined[y:y + h, x:x + w]

        proj = np.sum(region > 0, axis=1).astype(float)

        # Smooth with a 7-row moving average
        kernel   = np.ones(7) / 7
        padded   = np.pad(proj, 3, mode="edge")
        smoothed = np.convolve(padded, kernel, mode="valid")[:len(proj)]

        split_rows = _find_valley_rows(smoothed, h)

        if not split_rows:
            result.append(cnt)
            continue

        # ── Build sub-contours for each stripe ──────────────────────────────
        boundaries  = [0] + split_rows + [h]
        sub_contours: List = []

        for i in range(len(boundaries) - 1):
            y_start = boundaries[i]
            y_end   = boundaries[i + 1]

            if y_end - y_start < 10:
                continue

            sub_mask = np.zeros(gray_mask.shape[:2], dtype=np.uint8)
            sub_mask[y + y_start:y + y_end, x:x + w] = \
                gray_mask[y + y_start:y + y_end, x:x + w]

            sub_cnts, _ = cv2.findContours(
                sub_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            sub_cnts = [c for c in sub_cnts if cv2.contourArea(c) > 5]

            if sub_cnts:
                merged_cnt = np.vstack(sub_cnts) if len(sub_cnts) > 1 else sub_cnts[0]
                sub_contours.append(merged_cnt)
            else:
                # Fallback: rectangular contour spanning the stripe
                rect_cnt = np.array([
                    [[x,         y + y_start]],
                    [[x + w - 1, y + y_start]],
                    [[x + w - 1, y + y_end - 1]],
                    [[x,         y + y_end - 1]],
                ], dtype=np.int32)
                sub_contours.append(rect_cnt)

        if len(sub_contours) > 1:
            result.extend(sub_contours)
            split_count += 1
            print(f"[split_tall_contours] h={h}px → split into {len(sub_contours)} parts at rows {split_rows}")
        else:
            result.append(cnt)  # valley found but couldn't produce 2+ clean sub-regions

    if split_count > 0:
        print(
            f"[split_tall_contours] {split_count} contours split "
            f"→ {len(result)} total (was {len(contours)})"
        )

    return result


def split_tall_lines(
    line_mask: npt.NDArray,
    lines: List["Line"],
    max_line_height_ratio: float = 0.08,
) -> List["Line"]:
    """
    Split Line objects whose bounding-box height exceeds a single text line.

    This is the post-grouping companion to split_tall_contours.  After
    group_line_chunks merges contour fragments, the resulting Line object
    may still span two text rows (convex-hull artefact or pixel bridge).
    Running split_tall_contours on each Line's contour individually avoids
    the re-merging problem that occurs when splitting happens before grouping.

    Args:
        line_mask:              Binary (or 3-channel) line-detection mask.
        lines:                  Sorted list of Line objects.
        max_line_height_ratio:  Lines taller than image_height * this are
                                candidates for splitting (default 0.08).

    Returns:
        New list of Line objects with tall lines replaced by their parts,
        still in top-to-bottom order.
    """
    if not lines:
        return lines

    if len(line_mask.shape) == 3:
        gray_mask = cv2.cvtColor(line_mask, cv2.COLOR_RGB2GRAY)
    else:
        gray_mask = line_mask.copy()

    # Use median line height × 1.5 as the split threshold so it adapts to the
    # actual text size on the page rather than a fixed % of image height.
    heights = [ln.bbox.h for ln in lines]
    median_h = float(np.median(heights))
    img_height = gray_mask.shape[0]
    adaptive_ratio = (median_h * 1.5) / img_height if img_height > 0 else max_line_height_ratio

    result: List = []
    for line in lines:
        split = split_tall_contours(gray_mask, [line.contour], adaptive_ratio)
        if len(split) > 1:
            for cnt in split:
                result.append(build_line_data(cnt))
        else:
            result.append(line)

    # Re-sort by y-center so order stays top-to-bottom after any splits
    result.sort(key=lambda ln: ln.bbox.y + ln.bbox.h // 2)

    return result


def filter_line_contours(image: npt.NDArray, line_contours, threshold: float = 0.005) -> List:
    """
    Filter line contours based on size criteria.

    Args:
        image: Reference image for size calculations
        line_contours: List of detected contours
        threshold: Minimum width threshold as fraction of image width

    Returns:
        Filtered list of contours
    """
    filtered_contours = []
    rejected = []
    img_width = image.shape[1]
    min_w = img_width * threshold

    for _, line_cnt in enumerate(line_contours):
        _, _, w, h = cv2.boundingRect(line_cnt)
        if w > min_w and h > 3:
            filtered_contours.append(line_cnt)
        else:
            rejected.append((w, h))

    if len(filtered_contours) == 0 and rejected:
        widths  = [r[0] for r in rejected]
        heights = [r[1] for r in rejected]
        print(f"[filter_line_contours] All {len(rejected)} contours rejected. "
              f"image_width={img_width}, min_w={min_w:.1f}, "
              f"w range={min(widths)}-{max(widths)}, h range={min(heights)}-{max(heights)}")

    return filtered_contours


def extract_line(
    image: npt.NDArray,
    mask: npt.NDArray,
    bbox_h: int,
    k_factor: float = 1.2,
    y_bounds: Tuple[int, int] = None,
):
    """
    Extract line region using morphological operations.

    Args:
        image:    Input image array
        mask:     Binary mask of line region
        bbox_h:   Height of bounding box
        k_factor: Scaling factor for morphological kernel
        y_bounds: Optional (top, bottom) pixel rows to clip the dilated mask,
                  preventing bleed into adjacent lines.

    Returns:
        Extracted line image
    """
    k_size = int(bbox_h * k_factor)
    morph_multiplier = k_factor

    morph_rect = cv2.getStructuringElement(
        shape=cv2.MORPH_RECT, ksize=(k_size, int(k_size * morph_multiplier))
    )
    dilated_mask = cv2.dilate(mask, kernel=morph_rect, iterations=1)

    if y_bounds is not None:
        top, bottom = y_bounds
        if top > 0:
            dilated_mask[:top, :] = 0
        if bottom < dilated_mask.shape[0]:
            dilated_mask[bottom:, :] = 0

    masked_line = mask_n_crop(image, dilated_mask)

    return masked_line


def get_line_image(
    image: npt.NDArray,
    mask: npt.NDArray,
    bbox_h: int,
    bbox_tolerance: float = 2.5,
    k_factor: float = 1.2,
    y_bounds: Tuple[int, int] = None,
):
    """
    Extract line image with adaptive height tolerance.

    Args:
        image:          Input image array
        mask:           Binary mask of line region
        bbox_h:         Height of bounding box
        bbox_tolerance: Height tolerance multiplier
        k_factor:       Initial scaling factor for morphological kernel
        y_bounds:       Optional (top, bottom) clip rows passed to extract_line.

    Returns:
        Tuple of (line_image, adapted_k_factor)
    """
    try:
        tmp_k = k_factor
        line_img = extract_line(image, mask, bbox_h, k_factor=tmp_k, y_bounds=y_bounds)

        max_attempts = 10
        attempts = 0

        while line_img.shape[0] > bbox_h * bbox_tolerance and attempts < max_attempts:
            tmp_k = tmp_k - 0.1
            if tmp_k <= 0.1:
                break
            line_img = extract_line(image, mask, bbox_h, k_factor=tmp_k, y_bounds=y_bounds)
            attempts += 1

        return line_img, tmp_k
    except Exception as e:
        print(f"Error in get_line_image: {e}")
        fallback_img = np.zeros((bbox_h, bbox_h * 2, 3), dtype=np.uint8)
        return fallback_img, k_factor


def find_folio_marker_end(line_mask: npt.NDArray, line: "Line",
                          search_fraction: float = 0.20,
                          gap_threshold: float = 0.02,
                          min_gap_width: int = 10) -> Optional[int]:
    """
    Look for the gap between the folio marker and the main text body in the
    line detection mask.  Tibetan folios often have a brief folio-number
    annotation (e.g. གོ།) at the left edge of the first text line, separated
    from the body text by a clear blank stretch in the mask.

    Args:
        line_mask:       Grayscale (or 3-channel) line detection mask.
        line:            The Line object for the line to inspect.
        search_fraction: Only search the left this fraction of the line width.
        gap_threshold:   Column is considered empty if its mask-pixel fraction
                         is below this value.
        min_gap_width:   Minimum number of consecutive empty columns to count
                         as a gap.

    Returns:
        The absolute x-coordinate (in the full image) where the gap ends
        (i.e. where the main text starts), or None if no gap found.
    """
    if len(line_mask.shape) == 3:
        gray = cv2.cvtColor(line_mask, cv2.COLOR_RGB2GRAY)
    else:
        gray = line_mask

    x, y, w, h = line.bbox.x, line.bbox.y, line.bbox.w, line.bbox.h
    crop = gray[y:y + h, x:x + w]
    col_density = (crop > 0).astype(np.float32).mean(axis=0)

    search_end = int(w * search_fraction)
    in_gap, gap_start = False, 0
    gaps = []

    for col in range(search_end):
        if col_density[col] < gap_threshold:
            if not in_gap:
                in_gap, gap_start = True, col
        else:
            if in_gap:
                in_gap = False
                if col - gap_start >= min_gap_width:
                    gaps.append((gap_start, col))

    if not gaps:
        return None

    _, gap_end_relative = gaps[-1]
    return x + gap_end_relative  # absolute x in the full image


def extract_line_images(image: npt.NDArray, line_data: List[Line], default_k: float = 1.7, bbox_tolerance: float = 3, line_mask: npt.NDArray = None):
    """
    Extract individual line images from detected line data.

    Args:
        image:          Input image array
        line_data:      List of Line objects (top-to-bottom order)
        default_k:      Default scaling factor
        bbox_tolerance: Height tolerance for line extraction

    Returns:
        List of extracted line images
    """
    current_k = default_k
    img_h = image.shape[0]
    line_images = []

    for i, line in enumerate(line_data):
        x, y, w, h = cv2.boundingRect(line.contour)

        # Clip dilation to the midpoint between this line and its neighbours so
        # that the expanded mask never bleeds into adjacent line text.
        if i == 0:
            top_bound = 0
        else:
            prev_bottom = line_data[i - 1].bbox.y + line_data[i - 1].bbox.h
            top_bound = (prev_bottom + y) // 2

        if i == len(line_data) - 1:
            bottom_bound = img_h
        else:
            next_top = line_data[i + 1].bbox.y
            bottom_bound = (y + h + next_top) // 2

        tmp_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
        cv2.drawContours(tmp_mask, [line.contour], -1, (255, 255, 255), -1)

        line_img, adapted_k = get_line_image(
            image, tmp_mask, h,
            bbox_tolerance=bbox_tolerance,
            k_factor=current_k,
            y_bounds=(top_bound, bottom_bound),
        )
        line_images.append(line_img)

        if current_k != adapted_k:
            current_k = adapted_k

    return line_images


def get_line_threshold(line_prediction: npt.NDArray, slice_width: int = 20):
    """
    Calculate threshold for line sorting based on detected lines.
    
    This function generates n slices (of n = steps) width the width of slice_width across the bbox of the detected lines.
    The slice with the max. number of contained contours is taken to be the canditate to calculate the bbox center of each contour and
    take the median distance between each bbox center as estimated line cut-off threshold to sort each line segment across the horizontal

    Note: This approach might turn out to be problematic in case of sparsely spread line segments across a page
    
    Args:
        line_prediction: Binary prediction mask containing lines
        slice_width: Width of analysis slices
        
    Returns:
        Calculated line threshold value
    """
    if len(line_prediction.shape) == 3:
        line_prediction = cv2.cvtColor(line_prediction, cv2.COLOR_BGR2GRAY)

    x, y, w, h = cv2.boundingRect(line_prediction)
    x_steps = (w // slice_width) // 2

    bbox_numbers = []

    for step in range(1, x_steps + 1):
        x_offset = x_steps * step
        x_start = x + x_offset
        x_end = x_start + slice_width

        _slice = line_prediction[y : y + h, x_start:x_end]
        contours, _ = cv2.findContours(_slice, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        bbox_numbers.append((len(contours), contours))

    sorted_list = sorted(bbox_numbers, key=lambda x: x[0], reverse=True)

    if len(sorted_list) > 0:
        reference_slice = sorted_list[0]

        y_points = []
        n_contours, contours = reference_slice

        if n_contours == 0:
            print("number of contours is 0")
            line_threshold = 0.0
        else:
            for _, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                y_center = y + (h // 2)
                y_points.append(y_center)

            # Check if y_points is empty before calculating median
            if len(y_points) > 0:
                line_threshold = float(np.median(y_points) // n_contours)
            else:
                line_threshold = 0.0
    else:
        line_threshold = 0.0

    return line_threshold


def sort_bbox_centers(bbox_centers: List[Tuple[int, int]], line_threshold: int = 20) -> List:
    """
    Sort bounding box centers into horizontal lines.
    
    Args:
        bbox_centers: List of (x, y) center coordinates
        line_threshold: Vertical distance threshold for grouping
        
    Returns:
        List of lists, each containing centers on the same line
    """
    # Handle empty bbox_centers
    if not bbox_centers:
        return []
        
    sorted_bbox_centers = []
    tmp_line = []

    for i in range(0, len(bbox_centers)):
        if len(tmp_line) > 0:
            for s in range(0, len(tmp_line)):
                # TODO: refactor this to make this calculation an enum to choose between both methods
                # y_diff = abs(tmp_line[s][1] - bbox_centers[i][1])
                """
                I use the mean of the hitherto present line chunks in tmp_line since
                the precalculated fixed threshold can break the sorting if
                there is some slight bending in the line. This part may need some tweaking after
                some further practical review
                """
                ys = [y[1] for y in tmp_line]
                
                # Check if ys is not empty before calculating mean
                if ys:
                    mean_y = np.mean(ys)
                    y_diff = abs(mean_y - bbox_centers[i][1])

                    if y_diff > line_threshold:
                        tmp_line.sort(key=lambda x: x[0])
                        sorted_bbox_centers.append(tmp_line.copy())
                        tmp_line.clear()

                        tmp_line.append(bbox_centers[i])
                        break
                    else:
                        tmp_line.append(bbox_centers[i])
                        break
                else:
                    tmp_line.append(bbox_centers[i])
                    break
        else:
            tmp_line.append(bbox_centers[i])

    # Add the last tmp_line if it's not empty
    if tmp_line:
        sorted_bbox_centers.append(tmp_line)

    # Sort each line by x-coordinate
    for y in sorted_bbox_centers:
        y.sort(key=lambda x: x[0])

    sorted_bbox_centers = list(reversed(sorted_bbox_centers))

    return sorted_bbox_centers


def group_line_chunks(sorted_bbox_centers, lines: List[Line], adaptive_grouping: bool = True):
    """
    Group line chunks into unified line objects.
    
    Args:
        sorted_bbox_centers: Sorted bounding box centers by lines
        lines: Original Line objects
        adaptive_grouping: Whether to apply adaptive sizing adjustments
        
    Returns:
        List of grouped Line objects
    """
    new_line_data = []
    for bbox_centers in sorted_bbox_centers:

        if len(bbox_centers) > 1:  # i.e. more than 1 bbox center in a group
            contour_stack = []

            for box_center in bbox_centers:
                for line_data in lines:
                    if box_center == line_data.center:
                        contour_stack.append(line_data.contour)
                        break

            if adaptive_grouping:
                for contour in contour_stack:
                    x, y, w, h = cv2.boundingRect(contour)
                    width_offset = int(w * 0.05)
                    height_offset = int(h * 0.05)
                    w += width_offset
                    h += height_offset

            stacked_contour = np.vstack(contour_stack)
            stacked_contour = cv2.convexHull(stacked_contour)

            # TODO: both calls necessary?
            x, y, w, h = cv2.boundingRect(stacked_contour)
            _, _, angle = cv2.minAreaRect(stacked_contour)

            _bbox = BBox(x, y, w, h)
            x_center = _bbox.x + (_bbox.w // 2)
            y_center = _bbox.y + (_bbox.h // 2)

            new_line = Line(
                guid=generate_guid(clock_seq=23),
                contour=stacked_contour,
                bbox=_bbox,
                center=(x_center, y_center)
            )

            new_line_data.append(new_line)

        else:
            for _bcenter in bbox_centers:
                for line_data in lines:
                    if _bcenter == line_data.center:
                        new_line_data.append(line_data)
                        break

    return new_line_data


def filter_outlier_lines(lines: List[Line], gap_ratio: float = 2.5) -> List[Line]:
    """
    Remove lines that are isolated far from the main text block.

    After sorting, the first or last line is sometimes a page-border or
    frame detection rather than real text.  We detect these by comparing
    each line's gap to its nearest neighbour against the median inter-line
    gap: any line whose nearest-neighbour gap exceeds gap_ratio × median is
    considered an outlier and dropped.

    Args:
        lines:      Sorted list of Line objects (top-to-bottom).
        gap_ratio:  A line is an outlier if its nearest-gap > this × median.

    Returns:
        Filtered list with outlier lines removed.
    """
    if len(lines) < 3:
        return lines

    y_centers = [ln.bbox.y + ln.bbox.h // 2 for ln in lines]
    gaps = [abs(y_centers[i + 1] - y_centers[i]) for i in range(len(y_centers) - 1)]
    median_gap = float(np.median(gaps))

    if median_gap == 0:
        return lines

    keep = []
    for i, ln in enumerate(lines):
        # Nearest-neighbour gap for this line
        neighbour_gaps = []
        if i > 0:
            neighbour_gaps.append(gaps[i - 1])
        if i < len(lines) - 1:
            neighbour_gaps.append(gaps[i])
        min_gap = min(neighbour_gaps)

        if min_gap > gap_ratio * median_gap:
            print(f"[filter_outlier_lines] Dropping isolated line at y={ln.bbox.y} "
                  f"(gap={min_gap:.0f}px, median={median_gap:.0f}px, ratio={min_gap/median_gap:.2f})")
        else:
            keep.append(ln)

    return keep


def sort_lines_by_threshold(
    line_mask: np.array,
    lines: list[Line],
    threshold: int = 20,
    calculate_threshold: bool = True,
    group_lines: bool = True
):
    """
    Sort detected lines by vertical position using threshold-based grouping.
    
    Args:
        line_mask: Binary mask of detected lines
        lines: List of Line objects to sort
        threshold: Vertical distance threshold for grouping
        calculate_threshold: Whether to auto-calculate threshold
        group_lines: Whether to merge nearby lines
        
    Returns:
        Tuple of (sorted_lines, calculated_threshold)
    """
    bbox_centers = [x.center for x in lines]

    if calculate_threshold:
        line_treshold = get_line_threshold(line_mask)
    else:
        line_treshold = threshold

    sorted_bbox_centers = sort_bbox_centers(bbox_centers, line_threshold=line_treshold)

    if group_lines:
        new_lines = group_line_chunks(sorted_bbox_centers, lines)
    else:
        _bboxes = [x for xs in sorted_bbox_centers for x in xs]

        new_lines = []
        for _bbox in _bboxes:
            for _line in lines:
                if _bbox == _line.center:
                    new_lines.append(_line)

    return new_lines, line_treshold


def sort_lines_by_threshold2(
    line_mask: npt.NDArray,
    lines: List[Line],
    threshold: int = 20,
    calculate_threshold: bool = True,
    group_lines: bool = True
):
    """
    Alternative implementation for sorting lines by threshold.

    Args:
        line_mask: Binary mask of detected lines
        lines: List of Line objects to sort
        threshold: Vertical distance threshold for grouping
        calculate_threshold: Whether to auto-calculate threshold
        group_lines: Whether to merge nearby lines

    Returns:
        Tuple of (sorted_lines, calculated_threshold)
    """
    bbox_centers = [x.center for x in lines]

    if calculate_threshold:
        line_treshold = get_line_threshold(line_mask)
    else:
        line_treshold = threshold

    sorted_bbox_centers = sort_bbox_centers(bbox_centers, line_threshold=line_treshold)

    if group_lines:
        new_lines = group_line_chunks(sorted_bbox_centers, lines)
    else:
        _bboxes = [x for xs in sorted_bbox_centers for x in xs]

        new_lines = []
        for _bbox in _bboxes:
            for _line in lines:
                if _bbox == _line.center:
                    new_lines.append(_line)

    new_lines = split_tall_lines(line_mask, new_lines)
    new_lines = filter_outlier_lines(new_lines)

    return new_lines, line_treshold