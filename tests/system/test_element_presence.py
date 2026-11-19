import json

import numpy as np
import pytest
import torch

from EVA.core.ml_identification import element_presence as ep

ELEMENTS = ["Al", "B", "Bi", "C", "Co", "Fe", "Pb", "Si", "W"]


def make_model(models_dir, name, L=ep.DEFAULT_L, settings=None):
    """Creates a model folder containing a tiny random-weight checkpoint trained-shape for L points."""
    folder = models_dir / name
    folder.mkdir()
    model = ep.CNNPresenceTiny(n_out=len(ELEMENTS))
    with torch.no_grad():
        model(
            torch.zeros(1, 1, L)
        )  # LazyLinear needs one forward pass to get its shape
    torch.save(model.state_dict(), folder / ep.CHECKPOINT_FILENAME)
    if settings is not None:
        (folder / ep.SETTINGS_FILENAME).write_text(json.dumps(settings))
    return folder


@pytest.fixture
def models_dir(tmp_path, monkeypatch):
    """Points the module at an empty temporary models folder with a shared elements library."""
    d = tmp_path / "models"
    d.mkdir()
    np.savez(d / ep.ELEMENTS_LIBRARY_FILENAME, element_order=np.array(ELEMENTS))
    monkeypatch.setattr(ep, "MODEL_DIR", d)
    monkeypatch.setattr(
        ep, "SHARED_ELEMENTS_LIBRARY_PATH", d / ep.ELEMENTS_LIBRARY_FILENAME
    )
    return d


def spectrum(n=5000, x_max=8000.0):
    rng = np.random.default_rng(0)
    x = np.linspace(0, x_max, n)
    return x, rng.poisson(20, n).astype(float)


def test_discover_models_finds_only_folders_with_a_checkpoint(models_dir):
    folder = make_model(models_dir, "biryani_3099")
    (models_dir / "not_a_model").mkdir()

    assert ep.discover_models() == {"Biryani 3099": folder}


def test_discover_models_empty_when_no_models_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(ep, "MODEL_DIR", tmp_path / "does_not_exist")
    assert ep.discover_models() == {}


def test_settings_default_and_override(models_dir):
    default = make_model(models_dir, "default_model")
    custom = make_model(
        models_dir, "custom_model", L=1000, settings={"L": 1000, "x_max": 999.99}
    )

    assert ep._load_settings(default) == ep.ModelSettings()
    assert ep._load_settings(custom) == ep.ModelSettings(L=1000, x_max=999.99)


def test_settings_unknown_key_is_rejected(models_dir):
    folder = make_model(models_dir, "typo_model", settings={"Lx": 5})
    with pytest.raises(KeyError):
        ep._load_settings(folder)


@pytest.mark.parametrize(
    "settings", [ep.ModelSettings(), ep.ModelSettings(L=1000, x_max=999.99)]
)
def test_preprocess_gives_fixed_length_normalised_spectrum(settings):
    x, y = spectrum()
    out = ep.preprocess_spectrum(x, y, settings)

    assert out.shape == (settings.L,)
    assert out.dtype == np.float32
    assert out.sum() == pytest.approx(1.0, rel=1e-5)
    assert (out >= 0).all()


def test_preprocess_rejects_spectrum_without_counts():
    x, _ = spectrum()
    with pytest.raises(ValueError):
        ep.preprocess_spectrum(x, np.zeros_like(x))


def test_identify_elements_output_structure(models_dir):
    folder = make_model(models_dir, "m")
    x, y = spectrum()
    res = ep.identify_elements(x, y, folder)

    assert set(res["probs"]) == set(ELEMENTS)
    assert all(0.0 <= p <= 1.0 for p in res["probs"].values())
    probs_topk = [p for _, p in res["topk"]]
    assert probs_topk == sorted(probs_topk, reverse=True)
    assert set(res["present"]) <= set(ELEMENTS)


def test_identify_elements_threshold(models_dir):
    folder = make_model(models_dir, "m")
    x, y = spectrum()

    assert set(ep.identify_elements(x, y, folder, threshold=0.0)["present"]) == set(
        ELEMENTS
    )
    assert ep.identify_elements(x, y, folder, threshold=1.1)["present"] == []


def test_model_trained_on_another_grid_works_with_its_settings(models_dir):
    folder = make_model(
        models_dir, "short", L=1000, settings={"L": 1000, "x_max": 999.99}
    )
    x, y = spectrum(n=2000, x_max=1000.0)

    assert set(ep.identify_elements(x, y, folder)["probs"]) == set(ELEMENTS)


def test_wrong_grid_settings_fail_loudly_instead_of_giving_wrong_answers(models_dir):
    # checkpoint built for 1000 points but no settings.json -> default 8000-point grid
    folder = make_model(models_dir, "short_without_settings", L=1000)
    x, y = spectrum()

    with pytest.raises(RuntimeError):
        ep.identify_elements(x, y, folder)


def test_missing_checkpoint_raises(models_dir):
    folder = models_dir / "empty"
    folder.mkdir()
    with pytest.raises(FileNotFoundError):
        ep._load_model(folder)


def test_missing_elements_library_raises(models_dir):
    folder = make_model(models_dir, "m")
    (models_dir / ep.ELEMENTS_LIBRARY_FILENAME).unlink()
    with pytest.raises(FileNotFoundError):
        ep._load_model(folder)
