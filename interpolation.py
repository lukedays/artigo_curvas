import warnings

import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit


def linear_model(df):
    t = df.iloc[:, 0].to_numpy()
    y = df.iloc[:, 1].to_numpy()

    linear_interp = interp1d(t, y, kind="linear")

    t_new = np.linspace(5, 3000, 100)
    y_new = linear_interp(t_new)

    # Plot the results
    # plot_chart(t, y, t_new, y_new)

    return t_new, y_new


def svensson_model(df):
    t = df.iloc[:, 0].to_numpy()
    y = df.iloc[:, 1].to_numpy()

    # Initial guess for the parameters
    initial_guess = [0.1, 0.1, 0.1, 0.1, 1, 1]

    # Fit the model
    try:
        with warnings.catch_warnings(action="ignore"):
            params, _ = curve_fit(svensson, t, y, p0=initial_guess)
    except Exception as e:
        print("Error fitting curve", e)
        return np.array([]), np.array([])

    beta0, beta1, beta2, beta3, lambda1, lambda2 = params

    # Interpolate yields
    t_new = np.linspace(180, 3000, 100)
    y_new = svensson(t_new, beta0, beta1, beta2, beta3, lambda1, lambda2)

    # Plot the results
    # plot_chart(t, y, t_new, y_new)

    return t_new, y_new


def svensson(t, beta0, beta1, beta2, beta3, lambda1, lambda2):
    """
    Svensson model function
    https://www.anbima.com.br/data/files/18/42/65/50/4169E510222775E5A8A80AC2/est-termo_metodologia.pdf
    """
    return (
        beta0
        + beta1 * (1 - np.exp(-t * lambda1)) / (t * lambda1)
        + beta2 * ((1 - np.exp(-t * lambda1)) / (t * lambda1) - np.exp(-t * lambda1))
        + beta3 * ((1 - np.exp(-t * lambda2)) / (t * lambda2) - np.exp(-t * lambda2))
    )


def objective(params, t, y):
    """
    Define the objective function to minimize
    """
    beta0, beta1, beta2, beta3, lambda1, lambda2 = params
    return np.sum((y - svensson(t, beta0, beta1, beta2, beta3, lambda1, lambda2)) ** 2)


def plot_chart(t, y, t_new, y_new):
    plt.plot(t, y, "o", label="Observed Data")
    plt.plot(t_new, y_new, "-", label="Model Data")
    plt.xlabel("Maturity")
    plt.ylabel("Yield")
    plt.legend()
    plt.show()
