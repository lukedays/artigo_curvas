import time
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from io import StringIO
import os
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import curve_fit
import QuantLib as ql


# Simulated Brazilian yield curve data
# Columns represent different tenors, rows represent different time points
def generate_yield_curve_data():
    np.random.seed(42)
    tenors = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y", "20Y", "30Y"]
    time_points = 50

    # Generate synthetic yield curve data with realistic characteristics
    base_curve = np.linspace(8.5, 11.5, len(tenors))
    yield_data = np.zeros((time_points, len(tenors)))

    for t in range(time_points):
        # Add some randomness and trend
        noise = np.random.normal(0, 0.3, len(tenors))
        trend = np.sin(t / 5) * 0.5
        yield_data[t, :] = base_curve + noise + trend

    return pd.DataFrame(yield_data, columns=tenors)


# Create animated surface plot
def create_yield_curve_surface_plot(yield_data):
    # Prepare data for surface plot
    x = list(range(len(yield_data.columns)))  # Tenors
    y = list(range(len(yield_data)))  # Time points
    z = yield_data.values

    # Create figure
    fig = go.Figure(
        data=[
            go.Surface(
                z=z, x=x, y=y, colorscale="Viridis", colorbar=dict(title="Yield (%)")
            )
        ],
        layout=go.Layout(
            title="Brazilian Yield Curve Surface Chart",
            scene=dict(
                xaxis_title="Tenor",
                yaxis_title="Time Point",
                zaxis_title="Yield (%)",
                xaxis=dict(tickvals=x, ticktext=yield_data.columns),
            ),
            updatemenus=[
                {
                    "type": "buttons",
                    "showactive": False,
                    "buttons": [
                        {
                            "label": "Play",
                            "method": "animate",
                            "args": [
                                None,
                                {
                                    "frame": {"duration": 50, "redraw": True},
                                    "fromcurrent": True,
                                },
                            ],
                        },
                        {
                            "label": "Pause",
                            "method": "animate",
                            "args": [
                                [None],
                                {
                                    "frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0},
                                },
                            ],
                        },
                    ],
                }
            ],
        ),
    )

    # Add frames for animation
    frames = [
        go.Frame(
            data=[go.Surface(z=z[: i + 1], x=x, y=y[: i + 1], colorscale="Viridis")]
        )
        for i in range(len(y))
    ]

    fig.frames = frames

    return fig


# # Generate yield curve data
# yield_df = generate_yield_curve_data()

# # Generate and show the plot
# yield_curve_plot = create_yield_curve_surface_plot(yield_df)
# yield_curve_plot.show()


def get_b3_reference_rates():
    """
    Scrape reference rates from B3 website using Selenium and pandas.
    Since it's a dynamic JS page we can't use HTTP requests.
    """

    # Open Chrome
    driver = webdriver.Chrome()

    # Navigate to B3 reference rates page
    driver.get(
        "http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-taxas-referenciais-bmf-ptBR.asp"
    )

    start_date = ql.Date(10, 12, 2024)
    end_date = ql.Date(16, 12, 2024)
    schedule = create_brazilian_business_days_schedule(start_date, end_date)

    df_result = pd.DataFrame()

    for date in schedule:
        str_date = date.strftime("%d/%m/%Y")

        # Wait and input start date
        date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Data"))
        )
        date_field.clear()
        date_field.send_keys(str_date)

        # Submit form
        submit_button = driver.find_element(By.XPATH, './/button[text()="OK"]')
        submit_button.click()
        time.sleep(1)

        # Get page source
        page_source = StringIO(driver.page_source)

        # Use pandas to read HTML tables from source
        tables = pd.read_html(page_source, decimal=",", thousands=".")

        # Maturities and observed yields
        df = tables[0]
        t_new, y_new = svensson_model(df)

        # Plot the results
        # plt.plot(t, y, "o", label="Observed Yields")
        # plt.plot(t_new, y_new, "-", label="Svensson Fit")
        # plt.xlabel("Maturity")
        # plt.ylabel("Yield")
        # plt.legend()
        # plt.show()

        df_new = pd.DataFrame({date.strftime("%Y-%m-%d"): y_new}, index=t_new)

        df_result = pd.concat([df_result, df_new], join="outer", axis=1)

    # Close the browser
    driver.quit()

    return df_result


def svensson_model(df):
    t = df.iloc[:, 0].to_numpy()
    y = df.iloc[:, 1].to_numpy()

    # Initial guess for the parameters
    initial_guess = [0.1, 0.1, 0.1, 0.1, 1, 1]

    # Fit the model
    params, _ = curve_fit(svensson, t, y, p0=initial_guess)
    beta0, beta1, beta2, beta3, lambda1, lambda2 = params

    # Interpolate yields
    t_new = np.linspace(1, 14000, 14000)
    y_new = svensson(t_new, beta0, beta1, beta2, beta3, lambda1, lambda2)
    return t_new, y_new


def create_brazilian_business_days_schedule(start_date, end_date):
    # Create the schedule
    schedule = ql.MakeSchedule(
        effectiveDate=start_date,
        terminationDate=end_date,
        tenor=ql.Period(ql.Daily),
        calendar=ql.Brazil(),
        convention=ql.Following,
        rule=ql.DateGeneration.Forward,
    )

    # Return the schedule
    return [datetime(date.year(), date.month(), date.dayOfMonth()) for date in schedule]


# Define the Svensson model function
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


def main():
    # Get rates for last 30 days
    rates_df = get_b3_reference_rates()

    if rates_df is not None:
        print(rates_df.head())


if __name__ == "__main__":
    main()
