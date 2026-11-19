"""
ML-based element-presence identification.

Wraps a small 1D-CNN (``CNNPresenceTiny``) that looks at an *entire* muon
X-ray spectrum and predicts which elements from a fixed, trained-on set are
present in it. This is deliberately separate from ``EVA.core.peak_finding``:
that package answers "where are the peaks", this one answers "which elements
are probably here" - the two return different kinds of result and are not
interchangeable.

Multiple trained models can be installed side by side (e.g. one per data
category/detector range) as subfolders of ``models/``. Each subfolder needs
at least a ``model.pt`` checkpoint; if it doesn't have its own
``elements_library.npz``, the shared one directly in ``models/`` is used
instead. Models are discovered automatically - see discover_models().
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

try:
    from scipy.interpolate import interp1d

    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"
CHECKPOINT_FILENAME = "model.pt"
ELEMENTS_LIBRARY_FILENAME = "elements_library.npz"
SHARED_ELEMENTS_LIBRARY_PATH = MODEL_DIR / ELEMENTS_LIBRARY_FILENAME

# Defaults, used when a model folder has no settings.json. A model trained on a different
# spectrum grid (e.g. 1000 points over 0-1000 keV) overrides these with its own settings.json.
DEFAULT_L = 8000
DEFAULT_X_MAX = 7900.0
DEFAULT_BASE = 4
DEFAULT_DROP = 0.10
SETTINGS_FILENAME = "settings.json"
DEFAULT_THRESHOLD = 0.5


@dataclass(frozen=True)
class ModelSettings:
    """Training-time settings a model needs at inference time - must match how it was trained."""

    L: int = DEFAULT_L  # number of points in the input spectrum grid
    x_max: float = DEFAULT_X_MAX  # grid spans [0, x_max) with L evenly spaced points
    base: int = DEFAULT_BASE  # CNN width
    drop: float = DEFAULT_DROP


# -------------------------
# Model definition - must match training exactly (copied from the training/
# inference script; do not change without retraining).
# -------------------------
class ConvBlock(nn.Module):
    def __init__(self, cin, cout, k=9, stride=2, p_drop=0.0):
        super().__init__()
        pad = k // 2
        self.net = nn.Sequential(
            nn.Conv1d(cin, cout, kernel_size=k, stride=stride, padding=pad, bias=False),
            nn.BatchNorm1d(cout),
            nn.GELU(),
            nn.Dropout(p_drop),
        )

    def forward(self, x):
        return self.net(x)


class CNNPresenceTiny(nn.Module):
    def __init__(self, n_out=18, base=4, drop=0.10):
        super().__init__()
        self.feat = nn.Sequential(
            ConvBlock(1, base, k=5, stride=2, p_drop=drop),  # 8000 -> 4000
            ConvBlock(base, base * 2, k=5, stride=2, p_drop=drop),  # 4000 -> 2000
            ConvBlock(base * 2, base * 4, k=3, stride=2, p_drop=drop),  # 2000 -> 1000
            ConvBlock(base * 4, base * 4, k=3, stride=2, p_drop=drop),  # 1000 -> 500
            ConvBlock(base * 4, base * 4, k=3, stride=2, p_drop=drop),  # 500  -> 250
            ConvBlock(base * 4, base * 4, k=3, stride=2, p_drop=drop),  # 250  -> 125
        )
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.LazyLinear(128),
            nn.GELU(),
            nn.Dropout(drop),
            nn.Linear(128, n_out),
        )

    def forward(self, x):
        return self.head(self.feat(x))


# -------------------------
# Model discovery
# -------------------------
def discover_models() -> dict[str, Path]:
    """
    Scans the models/ directory for subfolders containing a trained checkpoint.

    A subfolder is recognised as a model if it contains a file named
    CHECKPOINT_FILENAME ("model.pt"). The subfolder name is turned into a
    human-readable display name for the GUI (underscores -> spaces, title case).

    Returns:
        dict mapping display name -> that subfolder's Path. Empty if models/
        doesn't exist or contains no recognised model subfolders.
    """
    discovered: dict[str, Path] = {}
    if not MODEL_DIR.exists():
        return discovered

    for sub in sorted(MODEL_DIR.iterdir()):
        if sub.is_dir() and (sub / CHECKPOINT_FILENAME).exists():
            display_name = sub.name.replace("_", " ").strip().title()
            discovered[display_name] = sub

    return discovered


# -------------------------
# Lazy-loaded singletons, keyed by model subfolder - each model's checkpoint
# and element list are only read from disk once per app session, not on
# every button click, and loading one model doesn't evict another.
# -------------------------
_model_cache: dict[str, nn.Module] = {}
_element_order_cache: dict[str, list[str]] = {}
_settings_cache: dict[str, ModelSettings] = {}


def _load_settings(model_dir: Path) -> ModelSettings:
    """
    Reads the optional settings.json in a model's folder, e.g.
        {"L": 1000, "x_max": 999.99}
    Any key left out falls back to the default. No file means all defaults.
    """
    key = str(model_dir)
    if key not in _settings_cache:
        path = model_dir / SETTINGS_FILENAME
        values = {}
        if path.exists():
            with open(path) as f:
                values = json.load(f)
            unknown = set(values) - set(ModelSettings.__dataclass_fields__)
            if unknown:
                raise KeyError(
                    f"{path} has unknown setting(s) {sorted(unknown)}; "
                    f"allowed: {sorted(ModelSettings.__dataclass_fields__)}"
                )
        _settings_cache[key] = ModelSettings(**values)
    return _settings_cache[key]


def _resolve_elements_library_path(model_dir: Path) -> Path:
    own_path = model_dir / ELEMENTS_LIBRARY_FILENAME
    if own_path.exists():
        return own_path
    return SHARED_ELEMENTS_LIBRARY_PATH


def _load_element_order(model_dir: Path) -> list[str]:
    key = str(model_dir)
    if key not in _element_order_cache:
        lib_path = _resolve_elements_library_path(model_dir)
        if not lib_path.exists():
            raise FileNotFoundError(
                f"No elements_library.npz found for model '{model_dir.name}' "
                f"(checked {model_dir / ELEMENTS_LIBRARY_FILENAME} and {SHARED_ELEMENTS_LIBRARY_PATH})"
            )
        lib = np.load(lib_path, allow_pickle=True)
        if "element_order" not in lib.files:
            raise KeyError(
                f"{lib_path} does not contain 'element_order'. Keys: {lib.files}"
            )
        _element_order_cache[key] = [str(el) for el in lib["element_order"]]
    return _element_order_cache[key]


def _load_model(model_dir: Path) -> nn.Module:
    key = str(model_dir)
    if key not in _model_cache:
        ckpt_path = model_dir / CHECKPOINT_FILENAME
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Missing model checkpoint at: {ckpt_path}")

        element_order = _load_element_order(model_dir)
        settings = _load_settings(model_dir)
        device = torch.device("cpu")  # desktop app - don't require CUDA
        model = CNNPresenceTiny(
            n_out=len(element_order), base=settings.base, drop=settings.drop
        ).to(device)

        # LazyLinear needs one dummy forward pass before weights can be loaded
        with torch.no_grad():
            dummy = torch.zeros((1, 1, settings.L), dtype=torch.float32, device=device)
            _ = model(dummy)

        ckpt = torch.load(ckpt_path, map_location=device)
        state = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
        model.load_state_dict(state, strict=True)
        model.eval()

        logger.info(
            "Loaded ML element-presence model '%s' from %s (settings: %s)",
            model_dir.name,
            ckpt_path,
            settings,
        )
        _model_cache[key] = model
    return _model_cache[key]


# -------------------------
# Preprocessing - must match the training pipeline exactly.
# -------------------------
def _make_xnew(L: int, x_max: float) -> np.ndarray:
    # identical values to np.arange(0, x_max, x_max / L), but guaranteed to have exactly L points
    return np.linspace(0.0, x_max, L, endpoint=False, dtype=np.float64)


def _interp_to_xnew(x: np.ndarray, y: np.ndarray, xnew: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if not np.all(np.diff(x) > 0):
        order = np.argsort(x)
        x, y = x[order], y[order]

    if _HAS_SCIPY:
        f = interp1d(
            x,
            y,
            kind="linear",
            bounds_error=False,
            fill_value=(y[0], y[-1]),
            assume_sorted=True,
        )
        ynew = f(xnew)
    else:
        ynew = np.interp(xnew, x, y, left=y[0], right=y[-1])
    return ynew.astype(np.float64)


def preprocess_spectrum(
    x: np.ndarray,
    y: np.ndarray,
    settings: ModelSettings = ModelSettings(),
    eps: float = 1e-12,
) -> np.ndarray:
    """
    Reproduces the exact preprocessing used at training time: interpolate onto
    the model's fixed grid (settings.L points spanning 0 to settings.x_max),
    clip negatives, then normalise so that sum(y) == 1.
    """
    xnew = _make_xnew(settings.L, settings.x_max)
    y_interp = _interp_to_xnew(x, y, xnew)
    y_interp = np.clip(y_interp, 0.0, None)

    total = float(y_interp.sum())
    if total <= eps:
        raise ValueError("sum(y) is ~0 after preprocessing; cannot normalize spectrum.")

    return (y_interp / total).astype(np.float32)


def identify_elements(
    x: np.ndarray, y: np.ndarray, model_dir: Path, threshold: float = DEFAULT_THRESHOLD
) -> dict:
    """
    Runs a single ML element-presence model on a single spectrum.

    Args:
        x: input x-data (histogram bins)
        y: input y-data (counts per bin)
        model_dir: path to the model's subfolder under models/ (one of the
            values returned by discover_models())
        threshold: probability threshold above which an element is reported as "present"

    Returns:
        dict with keys:
            "present": list of element symbols with probability >= threshold
            "probs": dict mapping every element symbol to its predicted probability
            "topk": list of (element, probability) tuples, sorted descending, top 8
    """
    model = _load_model(model_dir)
    element_order = _load_element_order(model_dir)

    y_proc = preprocess_spectrum(x, y, _load_settings(model_dir))
    x_t = torch.from_numpy(y_proc).unsqueeze(0).unsqueeze(0)  # (1, 1, L)

    with torch.no_grad():
        logits = model(x_t)
        probs = torch.sigmoid(logits)[0].detach().cpu().numpy()

    present = [
        element_order[i] for i in range(len(element_order)) if probs[i] >= threshold
    ]
    topk_idx = np.argsort(-probs)[:8]
    topk = [(element_order[i], float(probs[i])) for i in topk_idx]

    return {
        "present": present,
        "probs": {element_order[i]: float(probs[i]) for i in range(len(element_order))},
        "topk": topk,
    }
