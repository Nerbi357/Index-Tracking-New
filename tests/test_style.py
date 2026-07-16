import matplotlib

matplotlib.use("Agg")

from index_tracking.viz.style import custom_set_style


def test_set_style_runs():
    custom_set_style()
    import matplotlib.pyplot as plt

    assert plt.rcParams["axes.grid"] is True
    assert plt.rcParams["axes.spines.top"] is False
