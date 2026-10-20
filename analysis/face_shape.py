"""Estimate face shape, selected landmarks, and a hairline category.

This module is intended as the member-2 component for the beard styling demo.
It does not expose an HTTP API. The backend can call ``analyze_face_shape`` and pass
its JSON-compatible result to the rest of the application.

Input
-----
``analyze_face_shape(image)`` accepts a file path, image bytes, a Base64 string,
an HTTP(S) image URL, a Pillow image, or a NumPy image array. NumPy arrays are
assumed to be RGB by default. If an array came from OpenCV (which normally uses
BGR), pass ``color_order="BGR"``.

Output
------
``{"landmarks": {"152": [x, y], ...}, "faceShape": "oval", "hairline": "normal"}``

Only the five agreed MediaPipe points (152, 172, 397, 234, 454) are returned.
Coordinates are normalized image x/y values. Keys are strings for JSON.

The face-shape and hairline labels are heuristic estimates for a prototype,
not a validated or definitive classification system. Hairline thresholds
should be checked against the team's own sample photos before presenting
accuracy claims.
"""

from __future__ import annotations

import math
import base64
import binascii
from io import BytesIO
import os
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any, Literal


def _ensure_dependencies() -> None:
    """Install the small set of runtime packages if they are missing."""
    required = {
        "mediapipe": "mediapipe>=0.10.14",
        "numpy": "numpy>=1.23",
        "PIL": "Pillow>=9.0",
        "onnxruntime": "onnxruntime>=1.17",
    }
    missing = [
        package_spec
        for import_name, package_spec in required.items()
        if importlib.util.find_spec(import_name) is None
    ]
    if not missing:
        return

    print("正在安装脸型和发际线分析所需依赖，请保持网络连接……")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *missing]
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "依赖自动安装失败。请检查网络和 Python 的 pip 是否可用，"
            "或在项目终端运行 python -m pip install -r requirements-face-shape.txt。"
        ) from exc


_ensure_dependencies()

import mediapipe as mp
import numpy as np
from PIL import Image


_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
_MODEL_PATH = Path(__file__).resolve().parent / "models" / "face_landmarker.task"
_HAIR_PARSING_MODEL_PATH = Path(__file__).resolve().parent / "models" / "resnet18.onnx"
_HAIR_PARSING_MODEL_URL = (
    "https://github.com/yakhyo/face-parsing/releases/download/"
    "v0.0.1/resnet18.onnx"
)
_OUTPUT_LANDMARK_INDICES = (152, 172, 397, 234, 454)
_LEFT_BROW_INDICES = (46, 53, 52, 65, 55, 70, 63, 105, 66, 107)
_RIGHT_BROW_INDICES = (276, 283, 282, 295, 285, 300, 293, 334, 296, 336)
_LANDMARKER: Any | None = None
_LANDMARKER_LOCK = threading.RLock()
_PARSING_SESSION: Any | None = None
_PARSING_SESSION_PATH: Path | None = None


def _ensure_model_file() -> Path:
    """Find the model file, downloading it once if necessary."""
    configured_path = os.environ.get("FACE_LANDMARKER_MODEL")
    model_path = Path(configured_path).expanduser() if configured_path else _MODEL_PATH

    if model_path.is_file():
        return _runtime_safe_model_path(model_path)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(model_path.suffix + ".download")
    try:
        urllib.request.urlretrieve(_MODEL_URL, temporary_path)
        temporary_path.replace(model_path)
    except Exception as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            "MediaPipe 的人脸模型尚未下载成功。请检查网络，或下载官方 "
            "face_landmarker.task 模型，并设置环境变量 "
            "FACE_LANDMARKER_MODEL 指向该文件。"
        ) from exc

    return _runtime_safe_model_path(model_path)


def _runtime_safe_model_path(model_path: Path) -> Path:
    """Give native model runtimes an ASCII-only path on Windows if possible.

    The package may be extracted under a Chinese-named folder. Python can read
    that path, while some native runtime builds fail to open the same path.
    Keeping a cached copy under the system temporary directory avoids that
    mismatch without changing the package layout.
    """
    if os.name != "nt" or str(model_path).isascii():
        return model_path

    cache_dir = Path(tempfile.gettempdir()) / "face_shape_model_cache"
    cache_path = cache_dir / model_path.name
    cache_dir.mkdir(parents=True, exist_ok=True)
    if (
        not cache_path.is_file()
        or cache_path.stat().st_size != model_path.stat().st_size
        or cache_path.stat().st_mtime < model_path.stat().st_mtime
    ):
        shutil.copy2(model_path, cache_path)

    if str(cache_path).isascii():
        return cache_path

    # Resolve a Windows 8.3 alias for the temp path if the user folder itself
    # contains non-ASCII characters and short names are enabled on that drive.
    import ctypes

    short_path = ctypes.create_unicode_buffer(32768)
    get_short_path = ctypes.windll.kernel32.GetShortPathNameW
    get_short_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    get_short_path.restype = ctypes.c_uint
    length = get_short_path(str(cache_path), short_path, len(short_path))
    if length and short_path.value.isascii():
        return Path(short_path.value)
    return cache_path


def _get_landmarker() -> Any:
    """Create one reusable MediaPipe Face Landmarker."""
    global _LANDMARKER
    with _LANDMARKER_LOCK:
        if _LANDMARKER is None:
            model_path = _ensure_model_file()
            options = mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                # Detect more than one face so we can ask the user to crop a
                # group photo instead of silently analyzing an arbitrary face.
                num_faces=5,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
            )
            _LANDMARKER = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        return _LANDMARKER


def _to_rgb_array(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    color_order: Literal["RGB", "BGR"] = "RGB",
) -> np.ndarray:
    """Convert common image inputs into a contiguous uint8 RGB array."""
    if isinstance(image, str):
        parsed = urlsplit(image.strip())
        if parsed.scheme.lower() in ("http", "https"):
            if not parsed.netloc:
                raise ValueError("图片 URL 格式无效，请提供完整的 http:// 或 https:// 链接。")
            request = urllib.request.Request(
                image.strip(), headers={"User-Agent": "FaceShapeAnalyzer/1.0"}
            )
            max_download_bytes = 20 * 1024 * 1024
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    final_scheme = urlsplit(response.geturl()).scheme.lower()
                    if final_scheme not in ("http", "https"):
                        raise ValueError("图片 URL 跳转到了不支持的协议。")
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_download_bytes:
                        raise ValueError("图片 URL 文件超过 20 MB，请使用较小的图片。")
                    image_bytes = response.read(max_download_bytes + 1)
                    if len(image_bytes) > max_download_bytes:
                        raise ValueError("图片 URL 文件超过 20 MB，请使用较小的图片。")
            except ValueError:
                raise
            except Exception as exc:
                raise ValueError(f"无法从图片 URL 获取图片：{exc}") from exc
            with Image.open(BytesIO(image_bytes)) as opened:
                rgb = np.asarray(opened.convert("RGB"))
        else:
            image_path = Path(image).expanduser()
            try:
                is_image_path = image_path.is_file()
            except OSError:
                is_image_path = False
            if is_image_path:
                with Image.open(image_path) as opened:
                    rgb = np.asarray(opened.convert("RGB"))
            else:
                payload = image.strip()
                if payload.startswith("data:"):
                    header, separator, payload = payload.partition(",")
                    if not separator or ";base64" not in header.lower():
                        raise ValueError("Base64 图片需要使用 data:image/...;base64, 格式。")
                payload = "".join(payload.split())
                payload += "=" * (-len(payload) % 4)
                try:
                    image_bytes = base64.b64decode(payload, altchars=b"-_", validate=True)
                except (binascii.Error, ValueError) as exc:
                    raise ValueError(
                        "输入既不是可读取的图片路径、有效的 Base64 图片，也不是 http(s) 图片 URL。"
                    ) from exc
                with Image.open(BytesIO(image_bytes)) as opened:
                    rgb = np.asarray(opened.convert("RGB"))
    elif isinstance(image, os.PathLike):
        with Image.open(image) as opened:
            rgb = np.asarray(opened.convert("RGB"))
    elif isinstance(image, (bytes, bytearray)):
        with Image.open(BytesIO(image)) as opened:
            rgb = np.asarray(opened.convert("RGB"))
    elif isinstance(image, Image.Image):
        rgb = np.asarray(image.convert("RGB"))
    elif isinstance(image, np.ndarray):
        array = image
        if array.ndim == 2:
            array = np.repeat(array[:, :, None], 3, axis=2)
        if array.ndim != 3 or array.shape[2] not in (3, 4):
            raise ValueError("图片数组需要是 H×W×3、H×W×4，或灰度 H×W 格式。")

        array = array[:, :, :3]
        if np.issubdtype(array.dtype, np.floating):
            if not np.isfinite(array).all():
                raise ValueError("图片数组含有无效数值。")
            if array.size and float(array.max()) <= 1.0 and float(array.min()) >= 0.0:
                array = array * 255.0
        rgb = np.clip(array, 0, 255).astype(np.uint8)
        if color_order == "BGR":
            rgb = rgb[:, :, ::-1]
        elif color_order != "RGB":
            raise ValueError('color_order 只能是 "RGB" 或 "BGR"。')
    else:
        raise TypeError(
            "image 必须是图片路径、图片字节、Pillow 图片或 NumPy 图片数组。"
        )

    if rgb.size == 0 or rgb.shape[0] < 2 or rgb.shape[1] < 2:
        raise ValueError("图片为空或尺寸太小，请换一张清楚的正面照片。")

    return np.ascontiguousarray(rgb)


def _distance(points: list[list[float]], first: int, second: int) -> float:
    """Return normalized 2D distance between two MediaPipe point indices."""
    x1, y1 = points[first]
    x2, y2 = points[second]
    return math.hypot(x2 - x1, y2 - y1)


def _angle_at_point(
    points: list[list[float]], first: int, vertex: int, last: int
) -> float:
    """Return the angle at vertex formed by three landmark indices."""
    ax = points[first][0] - points[vertex][0]
    ay = points[first][1] - points[vertex][1]
    bx = points[last][0] - points[vertex][0]
    by = points[last][1] - points[vertex][1]
    magnitude_a = math.hypot(ax, ay)
    magnitude_b = math.hypot(bx, by)
    if magnitude_a <= 1e-9 or magnitude_b <= 1e-9:
        return 180.0
    cosine = (ax * bx + ay * by) / (magnitude_a * magnitude_b)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _jaw_corner_angles(
    points: list[list[float]], image_size: tuple[int, int]
) -> tuple[float, float]:
    """Measure both jaw-corner angles from the five agreed face landmarks."""
    width, height = image_size
    pixel_points = [[x * width, y * height] for x, y in points]
    return (
        _angle_at_point(pixel_points, 234, 172, 152),
        _angle_at_point(pixel_points, 454, 397, 152),
    )


def _estimate_face_shape(
    points: list[list[float]], image_size: tuple[int, int]
) -> str:
    """Apply the agreed starter ratio heuristic using face-oval landmarks."""
    # Approximate forehead/temple width, cheek width, jaw width, and vertical
    # face length from MediaPipe's normalized x/y landmarks.
    face_length = _distance(points, 10, 152)
    cheek_width = _distance(points, 234, 454)
    jaw_width = _distance(points, 172, 397)
    forehead_width = _distance(points, 103, 332)

    if cheek_width <= 1e-6 or face_length <= 1e-6:
        raise ValueError("无法可靠估算脸部比例，请上传正面、完整、清楚的照片。")

    length_to_width = face_length / cheek_width
    jaw_to_cheek = jaw_width / cheek_width
    forehead_to_cheek = forehead_width / cheek_width
    left_jaw_angle, right_jaw_angle = _jaw_corner_angles(points, image_size)
    smaller_jaw_angle = min(
        round(left_jaw_angle, 1), round(right_jaw_angle, 1)
    )

    # Starter thresholds for a hackathon prototype, not population-validated
    # boundaries. Either a broad jaw or a clear turn on either side can qualify
    # as square; oval is the longer-face branch of the round family.
    if jaw_to_cheek >= 0.85 or (
        smaller_jaw_angle <= 134.0
    ):
        return "square"
    if jaw_to_cheek < 0.85 and (
        smaller_jaw_angle > 140.0
        or forehead_to_cheek - jaw_to_cheek >= 0.12
    ):
        return "heart"
    if length_to_width <= 1.22 and jaw_to_cheek < 0.85:
        return "round"
    return "oval"


def _detect_all_landmarks(rgb: np.ndarray) -> list[list[float]]:
    """Run MediaPipe once and return all normalized face landmarks."""
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    with _LANDMARKER_LOCK:
        result = _get_landmarker().detect(mp_image)
    if not result.face_landmarks:
        raise ValueError("没有检测到人脸，请上传一张正面、光线充足的照片。")
    if len(result.face_landmarks) > 1:
        raise ValueError("检测到多张人脸，请先裁剪成只包含一位用户的单人照片，再重新上传。")
    points = [[float(point.x), float(point.y)] for point in result.face_landmarks[0]]
    if len(points) <= 454:
        raise RuntimeError(
            f"MediaPipe 返回了 {len(points)} 个点，少于当前规则需要的 455 个点。"
        )
    return points


def _landmark_result(
    points: list[list[float]], image_size: tuple[int, int]
) -> dict[str, Any]:
    return {
        "faceShape": _estimate_face_shape(points, image_size),
        "landmarks": {
            str(index): points[index] for index in _OUTPUT_LANDMARK_INDICES
        },
    }


def analyze_face_shape_only(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    *,
    color_order: Literal["RGB", "BGR"] = "RGB",
) -> dict[str, Any]:
    """Analyze one face and return faceShape plus the five selected points.

    Args:
        image: Image path, encoded image bytes, Pillow image, or NumPy array.
        color_order: Applies to NumPy arrays only. Use ``"BGR"`` for an array
            decoded by OpenCV; otherwise leave the default ``"RGB"``.

    Returns:
        A dictionary with ``faceShape`` (oval/round/square/heart) and
        ``landmarks`` (five normalized ``[x, y]`` pairs keyed by point index).

    Raises:
        ValueError: The image is invalid or no face was detected.
        RuntimeError: The MediaPipe model could not be loaded or run.
    """
    rgb = _to_rgb_array(image, color_order=color_order)
    return _landmark_result(
        _detect_all_landmarks(rgb), (rgb.shape[1], rgb.shape[0])
    )


def _get_parsing_session(model_path: str | os.PathLike[str] | None = None) -> Any:
    """Load the optional BiSeNet ONNX face-parsing model, downloading it once."""
    global _PARSING_SESSION, _PARSING_SESSION_PATH
    configured_path = model_path or os.environ.get("FACE_PARSING_MODEL")
    path = (
        Path(configured_path).expanduser()
        if configured_path
        else _HAIR_PARSING_MODEL_PATH
    )

    try:
        import onnxruntime as ort
    except ImportError:
        _ensure_dependencies()
        import onnxruntime as ort

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".download")
        try:
            print("首次使用发际线功能，正在下载分割模型，请保持网络连接……")
            urllib.request.urlretrieve(_HAIR_PARSING_MODEL_URL, temporary_path)
            temporary_path.replace(path)
        except Exception as exc:
            temporary_path.unlink(missing_ok=True)
            raise RuntimeError(
                "发际线模型自动下载失败。请检查网络，或手动下载 resnet18.onnx "
                "并放到 models 文件夹；也可以设置 FACE_PARSING_MODEL。"
            ) from exc

    runtime_path = _runtime_safe_model_path(path)
    resolved_path = runtime_path.resolve()
    if _PARSING_SESSION is None or _PARSING_SESSION_PATH != resolved_path:
        _PARSING_SESSION = ort.InferenceSession(
            str(runtime_path), providers=["CPUExecutionProvider"]
        )
        _PARSING_SESSION_PATH = resolved_path
    return _PARSING_SESSION


def _predict_face_parts(image: Image.Image, session: Any) -> np.ndarray:
    """Return a per-pixel face-parsing class mask in the original image size."""
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    resampling = getattr(Image, "Resampling", Image)
    resized = image.resize((512, 512), resampling.BILINEAR)
    tensor = np.asarray(resized, dtype=np.float32) / 255.0
    tensor = (tensor - mean) / std
    tensor = np.transpose(tensor, (2, 0, 1))[None, ...].astype(np.float32)

    input_name = session.get_inputs()[0].name
    output_names = [output.name for output in session.get_outputs()]
    outputs = session.run(output_names, {input_name: tensor})
    logits = np.asarray(outputs[0])
    # CelebAMask-HQ label IDs: skin=1, eyebrows=2/3, hair=17.
    if logits.ndim != 4 or logits.shape[0] != 1 or logits.shape[1] <= 17:
        raise RuntimeError(
            "ONNX 模型输出格式与预期不符；请确认使用的是 19 类 BiSeNet ResNet18 模型。"
        )
    small_mask = logits[0].argmax(axis=0).astype(np.uint8)
    mask_image = Image.fromarray(small_mask, mode="L")
    restored = mask_image.resize(image.size, resampling.NEAREST)
    return np.asarray(restored, dtype=np.uint8)


def _smooth_line(values: list[int], radius: int = 2) -> list[int]:
    """Reduce small pixel-level jumps along the estimated hairline."""
    smoothed: list[int] = []
    for position in range(len(values)):
        window = values[max(0, position - radius) : position + radius + 1]
        smoothed.append(int(np.median(window)))
    return smoothed


def _trace_visible_hairline(
    mask: np.ndarray, landmarks: list[list[float]]
) -> dict[str, Any]:
    """Trace hairline along a face-aligned axis and measure by projections."""
    height, width = mask.shape

    def px(index: int) -> np.ndarray:
        x, y = landmarks[index]
        return np.asarray([x * (width - 1), y * (height - 1)], dtype=np.float64)

    # Pick each eyebrow's highest MediaPipe brow point separately, then use
    # their connecting line as L1. This follows a slightly tilted face.
    brow_left = min(_LEFT_BROW_INDICES, key=lambda i: landmarks[i][1])
    brow_right = min(_RIGHT_BROW_INDICES, key=lambda i: landmarks[i][1])
    b1, b2 = px(brow_left), px(brow_right)
    line_vector = b2 - b1
    line_length = float(np.linalg.norm(line_vector))
    if line_length < 5:
        raise ValueError("无法分别定位两侧眉毛最高点，请换一张正面清晰照片。")
    along = line_vector / line_length
    toward_chin = np.asarray([-along[1], along[0]], dtype=np.float64)
    d1 = px(152)
    if float(np.dot(d1 - b1, toward_chin)) < 0:
        toward_chin = -toward_chin

    # L2 is perpendicular to L1 through D1. D2 is the foot from D1 to L1.
    d2 = b1 + float(np.dot(d1 - b1, along)) * along
    brow_to_chin = float(np.dot(d1 - d2, toward_chin))
    if brow_to_chin <= 5:
        raise ValueError("眉线与下巴位置关系异常，请换一张正对镜头的照片。")

    # Trace the parser mask in face coordinates: across the forehead parallel
    # to L1 and from forehead toward brow along the perpendicular direction.
    side_projections = [float(np.dot(px(i) - b1, along)) for i in (234, 454)]
    t_start, t_end = min(side_projections), max(side_projections)
    if t_end - t_start < 20:
        raise ValueError("人脸宽度不足，无法稳定定位额头和两侧额角。")
    t_samples = np.linspace(t_start, t_end, num=81)
    normal_step = 1.0
    s_start = -brow_to_chin * 0.82
    s_end = -brow_to_chin * 0.035
    s_samples = np.arange(s_start, s_end, normal_step)
    hair_nearby = max(3.0, brow_to_chin * 0.045)
    valid: list[tuple[float, float]] = []
    for t in t_samples:
        found_s: float | None = None
        last_hair_s: float | None = None
        for s in s_samples:
            point = b1 + t * along + s * toward_chin
            x, y = int(round(point[0])), int(round(point[1]))
            if x < 0 or x >= width or y < 0 or y >= height:
                continue
            label = int(mask[y, x])
            if label == 17:
                last_hair_s = float(s)
            elif label == 1 and last_hair_s is not None and s - last_hair_s <= hair_nearby:
                found_s = float(s)
                break
        if found_s is not None:
            valid.append((float(t), found_s))

    if len(valid) < 12 or len(valid) / len(t_samples) < 0.14:
        raise ValueError(
            "没有找到足够的额头/额角发际线点（至少需要约12个）。"
            "请上传单人正面照片，并尽可能露出额头和两侧额角，保证光线充足。"
        )

    smoothed_s = _smooth_line([round(s) for _t, s in valid], radius=2)
    line_pixels = [
        (b1 + t * along + s * toward_chin).tolist()
        for (t, _raw_s), s in zip(valid, smoothed_s)
    ]
    # The most forehead-ward point along L2's direction is the hairline peak.
    peak_index = min(range(len(smoothed_s)), key=lambda i: smoothed_s[i])
    peak = np.asarray(line_pixels[peak_index], dtype=np.float64)

    # L3 is parallel to L1 through the hairline peak; D3 is its foot on L2.
    d3 = d1 + float(np.dot(peak - d1, toward_chin)) * toward_chin
    numerator = abs(float(np.dot(d3 - d2, toward_chin)))
    denominator = abs(float(np.dot(d3 - d1, toward_chin)))
    if numerator <= 0 or denominator <= 0:
        raise ValueError("检测到的发际线与眉毛/下巴位置关系异常，请换一张正面照片。")

    ratio = numerator / denominator
    if ratio < 0.27:
        label = "receding"
    elif ratio <= 0.34:
        label = "normal"
    else:
        label = "high"

    return {
        "label": label,
        "line_pixels": [[round(x, 1), round(y, 1)] for x, y in line_pixels],
        "L1": [[round(x, 1), round(y, 1)] for x, y in (b1, b2)],
        "D1": [round(float(d1[0]), 1), round(float(d1[1]), 1)],
        "D2": [round(float(d2[0]), 1), round(float(d2[1]), 1)],
        "D3": [round(float(d3[0]), 1), round(float(d3[1]), 1)],
        "peak": [round(float(peak[0]), 1), round(float(peak[1]), 1)],
        "distance_D2D3_px": round(numerator, 1),
        "distance_D1D3_px": round(denominator, 1),
        "ratio": round(ratio, 4),
    }


def _hairline_details_from_rgb(
    rgb: np.ndarray,
    landmarks: list[list[float]],
    model_path: str | os.PathLike[str] | None,
) -> dict[str, Any]:
    source = Image.fromarray(rgb, mode="RGB")
    mask = _predict_face_parts(source, _get_parsing_session(model_path))
    return _trace_visible_hairline(mask, landmarks)


def analyze_hairline(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    *,
    model_path: str | os.PathLike[str] | None = None,
    color_order: Literal["RGB", "BGR"] = "RGB",
) -> str:
    """Return ``high``, ``normal`` or ``receding`` for hairline height.

    This optional feature uses the BiSeNet face-parsing ONNX model. On first
    use it installs the shared dependencies (if needed) and downloads its model
    into ``models/``. Hair covering the forehead, hats, and poor lighting can
    prevent a reliable classification.
    """
    rgb = _to_rgb_array(image, color_order=color_order)
    landmarks = _detect_all_landmarks(rgb)
    return _hairline_details_from_rgb(rgb, landmarks, model_path)["label"]


def analyze_face_shape(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    *,
    color_order: Literal["RGB", "BGR"] = "RGB",
    hairline_model_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Return the complete API-contract result for one face photo.

    The result contains only ``landmarks``, ``faceShape`` and ``hairline``.
    If either model cannot make its estimate, this function raises an error
    instead of returning a fabricated label or an incomplete result.
    """
    rgb = _to_rgb_array(image, color_order=color_order)
    landmarks = _detect_all_landmarks(rgb)
    result = _landmark_result(landmarks, (rgb.shape[1], rgb.shape[0]))
    details = _hairline_details_from_rgb(rgb, landmarks, hairline_model_path)
    result["hairline"] = details["label"]
    return result


def analyze_face(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    *,
    color_order: Literal["RGB", "BGR"] = "RGB",
    hairline_model_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Compatibility alias returning the complete agreed analysis.

    This legacy name returns the same three fields as
    :func:`analyze_face_shape`, including ``hairline``.
    """
    return analyze_face_shape(
        image,
        color_order=color_order,
        hairline_model_path=hairline_model_path,
    )


def analyze_face_with_debug(
    image: str | os.PathLike[str] | bytes | bytearray | Image.Image | np.ndarray,
    *,
    color_order: Literal["RGB", "BGR"] = "RGB",
    hairline_model_path: str | os.PathLike[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the agreed result and pixel measurements for the local preview."""
    rgb = _to_rgb_array(image, color_order=color_order)
    landmarks = _detect_all_landmarks(rgb)
    result = _landmark_result(landmarks, (rgb.shape[1], rgb.shape[0]))
    details = _hairline_details_from_rgb(rgb, landmarks, hairline_model_path)
    left_angle, right_angle = _jaw_corner_angles(
        landmarks, (rgb.shape[1], rgb.shape[0])
    )
    details["jaw_angles_deg"] = [round(left_angle, 1), round(right_angle, 1)]
    details["jaw_angle_landmarks"] = {
        str(index): [
            round(landmarks[index][0] * rgb.shape[1], 1),
            round(landmarks[index][1] * rgb.shape[0], 1),
        ]
        for index in (234, 172, 152, 454, 397)
    }
    result["hairline"] = details["label"]
    return result, details


def close_face_landmarker() -> None:
    """Release the reusable MediaPipe detector, useful when shutting down."""
    global _LANDMARKER
    with _LANDMARKER_LOCK:
        if _LANDMARKER is not None:
            _LANDMARKER.close()
            _LANDMARKER = None


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="分析一张照片并输出脸型、发际线和 5 个约定关键点。"
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="可选：照片文件路径，例如 sample.jpg；不填时仅显示使用提示",
    )
    parser.add_argument(
        "--output",
        help="可选：把结果保存为 JSON 文件，例如 face_shape.json",
    )
    args = parser.parse_args()

    if args.image:
        output = analyze_face_shape(args.image)
        rendered = json.dumps(output, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
            print(
                f"脸型：{output['faceShape']}；发际线：{output['hairline']}；"
                f"结果已保存到：{args.output}"
            )
        else:
            print(rendered)
    else:
        print(
            "face_shape.py 是供后端调用的分析模块。\n"
            "要选择照片并查看分析结果，请运行同文件夹里的 face_shape_测试版.py。\n"
            "命令行分析示例：python face_shape.py sample.jpg --output result.json"
        )
