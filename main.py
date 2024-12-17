import QuantLib as ql

from b3 import get_b3_reference_rates
from plot import create_yield_curve_surface_plot


def main():
    start_date = ql.Date(1, 1, 2024)
    end_date = ql.Date(16, 12, 2024)
    rates = get_b3_reference_rates(start_date, end_date)

    plot = create_yield_curve_surface_plot(rates)
    plot.show()


if __name__ == "__main__":
    main()
