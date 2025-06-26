import lmfit.model
import numpy as np
from functools import partial

from lmfit import Model, Parameter
from lmfit.models import GaussianModel, QuadraticModel, ConstantModel

from EVA.core.physics.functions import gaussian


def fit_gaussian_lmfit(x_data: np.ndarray, y_data: np.ndarray, peak_params: dict,
                       bg_params: dict) -> lmfit.model.ModelResult:
    """
    Fit a model containing N Gaussians using the least-squared method.

    Args:
        x_data: x-values to fit for
        y_data: y-values to fit for
        peak_params: dictionary containing each peak to fit for and fit settings for each peak
        bg_params: dictionary containing the background parameters and settings.

    Returns:
        lmfit model result object.
    """
    model = QuadraticModel(prefix="background_", nan_policy="omit")
    model.set_param_hint("a", **bg_params["background"]["a"])
    model.set_param_hint("b", **bg_params["background"]["b"])
    model.set_param_hint("c", **bg_params["background"]["c"])

    for name, params in peak_params.items():
        peak_model = GaussianModel(prefix=f"{name}_", nan_policy="omit")
        peak_model.set_param_hint("center", **params["center"])
        peak_model.set_param_hint("sigma", **params["sigma"])
        peak_model.set_param_hint("amplitude", **params["amplitude"])

        model += peak_model

    if len(model.param_names) > len(x_data):
        raise TypeError("Not enough points")

    fit_res = model.fit(y_data, x=x_data, weights=1/np.sqrt(y_data))
    return fit_res


def scaled_shifted_gaussians(x: np.ndarray, scale: float, x0: float, params: dict) -> np.ndarray:
    """
    Spectrum of multiple Gaussians, one for each set of peak parameters in 'params', with a vertical shift
    parameter x0 and an overall scale factor 'scale'

    Args:
        x: input array to calculate for
        scale: intensity scale factor
        x0: vertical offset parameter
        params: Gaussian peak parameter dict

    Returns:
        Array containing total spectrum from sum of all Gaussians.
    """
    return scale * np.sum([gaussian(x-x0, param["center"]["value"], param["sigma"]["value"],
                     param["amplitude"]["value"], offset=0) for param in params.values()], axis=0)


def fit_model_lmfit(x_data: np.ndarray, y_data:np.ndarray, peak_params: dict, bg_params: dict, model_params: dict,
                    constrain_scale: float | None = None) -> lmfit.model.ModelResult:
    """
    Fit a sum of previously defined fixed-shape N-Gaussian spectra with scale factors and shift parameters
    for each spectrum using the least-squares method.

    For example, if a spectrum containing multiple Gaussians has previously been fitted, this
    function can be used to fit the shape of that spectrum to another dataset, holding the mean and standard deviations
    of the previously fitted model fixed, only varying the scale factor and offset of the model.

    Args:
        x_data: x-values to fit for
        y_data: y-values to fit for
        peak_params: parameter dictionary for the gaussian peaks within each model
        bg_params: background parameters
        model_params: parameter dictionary for each model containing scale and offset parameters
        constrain_scale: if not None, all scale parameters will obey the constraint A + B ... + Z = constrain_scale

    Returns:
        lmfit model result object.
    """
    gaussian_sum_model = None

    # Check how many models will be fitted
    n_models = len(model_params)

    scale_param_names = [] # to store the names of the scale parameters
    for i, (model_id, params) in enumerate(model_params.items()):
        """
        'partial' creates a new fitting function for each model by feeding peak parameters into scaled_shifted_gaussian()
        This way, the fitting function can be generated automatically for each model.

        It's essentially like using a lambda, except the functions will still exist outside this scope. When using a
        lambda expression for this, I found that when plotting result.best_fit, lmfit only plotted the last model,
        instead of all..
        """
        func = partial(scaled_shifted_gaussians, params=peak_params[model_id])

        # partial functions do not have a __name__ attribute, but in order for lmfit to work it needs to have a name
        func.__name__ = f"scaled_shifted_gaussians{i}"

        spectrum_model = Model(func, prefix=f"{model_id}_")
        spectrum_model.set_param_hint("x0", **params["x0"], vary=True)

        # if user wants scale parameters to be constrained as scale1 + scale2 + scale3 = value
        if constrain_scale is not None:
            if n_models == 1: # if there is only one model, force scale=constrain_scale
                spectrum_model.set_param_hint("scale", value=constrain_scale, vary=False, min=0, max=constrain_scale)

            elif i < n_models - 1: # set all but the last scale parameters to be between 0 and scale constraint
                spectrum_model.set_param_hint("scale", **params["scale"], min=0, max=constrain_scale)
                scale_param_names.append(f"{model_id}_scale")
            else:
                # Constrain the last scale parameter to be equal to constraint - A - B... etc. to satisfy A + B + C = constraint
                # Only one of the scale parameters should have this constraint, otherwise we get recursion errors
                constraint = f"{constrain_scale} - " + " - ".join(scale_param_names)
                spectrum_model.set_param_hint("scale", **params["scale"], min=0, max=constrain_scale, expr=constraint)

        # if no scale constraints are wanted
        else:
            spectrum_model.set_param_hint("scale", **params["scale"])

        # finally, add this model to the total model
        if gaussian_sum_model is None:
            gaussian_sum_model = spectrum_model
        else:
            gaussian_sum_model += spectrum_model


    # First set up the background model
    bg_model = QuadraticModel(prefix="background_", nan_policy="omit")
    bg_model.set_param_hint("a", **bg_params["background"]["a"])
    bg_model.set_param_hint("b", **bg_params["background"]["b"])
    bg_model.set_param_hint("c", **bg_params["background"]["c"])

    # Add everything together
    model = gaussian_sum_model + bg_model

    return model.fit(y_data, x=x_data, weights=1/np.sqrt(y_data))

