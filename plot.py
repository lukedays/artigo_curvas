import plotly.graph_objs as go


def create_yield_curve_surface_plot(data):
    """
    Create animated surface plot
    """

    # Prepare data for surface plot
    x = data.columns.values  # Maturity
    y = data.index.values  # Time points
    z = data.values

    # Create figure
    buttons = {
        "type": "buttons",
        "showactive": False,
        "buttons": [
            {
                "label": "Play",
                "method": "animate",
                "args": [
                    None,
                    {
                        "frame": {"duration": 100, "redraw": True},
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

    fig = go.Figure(
        data=[
            go.Surface(
                z=z, x=x, y=y, colorscale="Viridis", colorbar=dict(title="Taxa (%)")
            )
        ],
        layout=go.Layout(
            title="Curva de Juros Brasileira",
            scene=dict(
                xaxis_title="Prazo (anos)",
                yaxis_title="Data",
                zaxis_title="Taxa (%)",
                xaxis=dict(
                    range=[x[-1], x[0]],
                    tickformat=".2f",
                ),
            ),
            updatemenus=[buttons],
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
