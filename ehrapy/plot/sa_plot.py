from __future__ import annotations
from xmlrpc.client import Boolean
from anndata import AnnData
from typing import Optional, Tuple, List, Union
from statsmodels.regression.linear_model import RegressionResults
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
import ehrapy as ep
from lifelines import KaplanMeierFitter

def ols_plot(
    adata: AnnData | None = None,
    x: str | None = None,
    y: str | None = None,
    scatter_plot: Optional[Boolean] = True,
    ols_results: List[RegressionResults] | None = None,
    ols_color: Optional[List[str]] | None = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = (6.4, 4.8),
    lines: Optional[list[Tuple[Union[ndarray, float], Union[ndarray, float]]]] = None,
    lines_color: Optional[List[str]] | None = None,
    lines_style: Optional[List[str]] | None = None,
    lines_label: Optional[List[str]] | None = None,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    **kwds,
):
    """Plots a Ordinary Least Squares (OLS) Model result, scatter plot, and line plot.
    
    Args:
        adata: :class:`~anndata.AnnData` object object containing all observations.
        x: x coordinate, for scatter plotting 
        y: y coordinate, for scatter plotting
        scatter_plot: If True, show scatter plot. Default is True
        ols_results: List of RegressionResults. From ehrapy.tl.ols. Example: [result_1, result_2]
        ols_color: List of colors for each ols_results. Example: ['red', 'blue']
        xlabel: The x-axis label text
        ylabel: The y-axis label text
        figsize: Width, height in inches. Default is: [6.4, 4.8]
        lines: List of Tuples of (slope, intercept) or (x, y). Plot lines by slope and intercept or data points. Example: plot two lines (y = x + 2 and y = 2*x + 1): [(1, 2), (2, 1)]
        lines_color: List of colors for each line. Example: ['red', 'blue']
        lines_style: List of line styles for each line. Example: ['-', '--']
        lines_label: List of line labels for each line. Example: ['Line1', 'Line2']
        xlim: Set the x-axis view limits. Required for only ploting lines using slope and intercept.
        ylim: Set the y-axis view limits. Required for only ploting lines using slope and intercept.

    Example:
        .. code-block:: python

            # Scatter plot and OLS regression plot
            import ehrapy as ep
            adata = ep.data.mimic_2(encoded=False)
            co2_lm_result = ep.tl.ols(adata, var_names=['pco2_first', 'tco2_first'], formula='tco2_first ~ pco2_first', missing="drop").fit()
            ep.pl.ols_plot(adata, x='pco2_first', y='tco2_first', ols_results=[co2_lm_result], ols_color=['red'], xlabel="PCO2", ylabel="TCO2")
        
        .. image:: /_static/docstring_previews/ols_plot_1.png

        .. code-block:: python

            # Scatter plot and line plot
            import ehrapy as ep
            adata = ep.data.mimic_2(encoded=False)
            ep.pl.ols_plot(adata, x='pco2_first', y='tco2_first', lines=[(0.25, 10), (0.3, 20)], lines_color=['red', 'blue'], lines_style=['-', ':'], lines_label=['Line1', 'Line2'])

        .. image:: /_static/docstring_previews/ols_plot_2.png

        .. code-block:: python

            # Line plot only
            import ehrapy as ep
            ep.pl.ols_plot(lines=[(0.25, 10), (0.3, 20)], lines_color=['red', 'blue'], lines_style=['-', ':'], lines_label=['Line1', 'Line2'], xlim=(0, 150), ylim=(0, 50))
        
        .. image:: /_static/docstring_previews/ols_plot_3.png
    """
    _, ax = plt.subplots(figsize=figsize)
    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)
    if ols_color is None and ols_results is not None:
        ols_color = [None]*len(ols_results)
    if lines_color is None and lines is not None:
        lines_color = [None]*len(lines)
    if lines_style is None and lines is not None:
        lines_style = [None]*len(lines)
    if lines_label is None and lines is not None:
        lines_label = [None]*len(lines)
    if adata is not None and x is not None and y is not None:
        x_processed = np.array(adata[:, x].X).astype(float)
        x_processed = x_processed[~np.isnan(x_processed)]
        if scatter_plot is True:
            ax = ep.pl.scatter(adata, x=x, y=y, show=False, ax=ax, **kwds)
        if ols_results is not None:
            for i, ols_result in enumerate(ols_results):
                ax.plot(x_processed, ols_result.predict(), color=ols_color[i])

    if lines is not None:
        for i, line in enumerate(lines):
            a, b = line
            if np.ndim(a) == 0 and np.ndim(b) == 0 :
                line_x = np.array(ax.get_xlim())
                line_y = a * line_x + b
                ax.plot(line_x, line_y, linestyle=lines_style[i], color=lines_color[i], label=lines_label[i])
            else:
                ax.plot(a, b, lines_style[i], color=lines_color[i], label=lines_label[i])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if lines_label is not None and lines_label[0] is not None:
        plt.legend()


def kmf_plot(
    kmfs: List[KaplanMeierFitter] = None,
    ci_alpha: Optional[List[float]] = None,
    ci_force_lines: Optional[List[Boolean]] = None,
    ci_show: Optional[List[Boolean]] = None,
    ci_legend: Optional[List[Boolean]] = None,
    at_risk_counts: Optional[List[Boolean]] = None,
    color: Optional[List[str]] | None = None,
    grid: Optional[Boolean] = False,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = (6.4, 4.8),
):
    """Plots a pretty figure of the Fitted KaplanMeierFitter model

    See https://lifelines.readthedocs.io/en/latest/fitters/univariate/KaplanMeierFitter.html
    
    Args:
        kmfs: Lists of fitted KaplanMeierFitter object
        ci_alpha: The transparency level of the confidence interval. Default: 0.3. If more than one kmfs, this should be a list
        ci_force_lines: Force the confidence intervals to be line plots (versus default shaded areas). Default: False. If more than one kmfs, this should be a list
        ci_show: Show confidence intervals. Default: True. If more than one kmfs, this should be a list
        ci_legend: If ci_force_lines is True, this is a boolean flag to add the lines' labels to the legend. Default: False. If more than one kmfs, this should be a list
        at_risk_counts: Show group sizes at time points. Default: False. If more than one kmfs, this should be a list
        color: List of colors for each kmf. If more than one kmfs, this should be a list
        grid: If True, plot grid lines
        xlim: Set the x-axis view limits
        ylim: Set the y-axis view limits
        xlabel: The x-axis label text
        ylabel: The y-axis label text
        figsize: Width, height in inches. Default is: [6.4, 4.8]
        
    Example:
        .. code-block:: python

            import ehrapy as ep
            import numpy as np
            from lifelines import KaplanMeierFitter
            adata = ep.data.mimic_2(encoded=False)
            adata[:, ['censor_flg']].X = np.where(adata[:, ['censor_flg']].X == 0, 1, 0)
            kmf = KaplanMeierFitter().fit(adata[:, ['mort_day_censored']].X, adata[:, ['censor_flg']].X)
            ep.pl.kmf_plot([kmf], color=['r'], xlim=[0, 700], ylim=[0, 1], xlabel="Days", ylabel="Proportion Survived")

        .. image:: /_static/docstring_previews/kmf_plot_1.png

        .. code-block:: python
            
            import ehrapy as ep
            import numpy as np
            from lifelines import KaplanMeierFitter
            adata = ep.data.mimic_2(encoded=False)
            adata[:, ['censor_flg']].X = np.where(adata[:, ['censor_flg']].X == 0, 1, 0)
            T = adata_subset[:, ['mort_day_censored']].X
            E = adata_subset[:, ['censor_flg']].X
            kmf_1 = KaplanMeierFitter().fit(T[ix1], E[ix1], label='FICU')
            kmf_2 = KaplanMeierFitter().fit(T[ix2], E[ix2], label='MICU')
            kmf_3 = KaplanMeierFitter().fit(T[ix3], E[ix3], label='SICU')

            ep.pl.kmf_plot([kmf_1, kmf_2, kmf_3], ci_show=[False,False,False], color=['k','r', 'g'], xlim=[0, 750], ylim=[0, 1], xlabel="Days", ylabel="Proportion Survived")    
    
        .. image:: /_static/docstring_previews/kmf_plot_2.png
    """
    if ci_alpha is None:
        ci_alpha = [0.3]*len(kmfs)
    if ci_force_lines is None:
        ci_force_lines = [False]*len(kmfs)
    if ci_show is None:
        ci_show = [True]*len(kmfs)
    if ci_legend is None:
        ci_legend = [False]*len(kmfs)
    if at_risk_counts is None:
        at_risk_counts = [False]*len(kmfs)
    if color is None:
        color = [None]*len(kmfs)
    plt.figure(figsize=figsize)
    for i, kmf in enumerate(kmfs):
        if i == 0:
            ax = kmf.plot(ci_alpha=ci_alpha[i], ci_force_lines=ci_force_lines[i], ci_show=ci_show[i], ci_legend=ci_legend[i], at_risk_counts=at_risk_counts[i], color=color[i])
        else:
            ax = kmf.plot(ax=ax, ci_alpha=ci_alpha[i], ci_force_lines=ci_force_lines[i], ci_show=ci_show[i], ci_legend=ci_legend[i], at_risk_counts=at_risk_counts[i], color=color[i])
    ax.grid(grid)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)