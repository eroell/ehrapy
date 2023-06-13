from typing import Union, Iterable, Literal

import numpy as np
import pandas as pd

from ehrapy.tools import _datatypes


def _merge_arrays(recarray, array, groups_order):
    """Merge `recarray` obtained from scanpy with manually created numpy `array`"""

    # The easiest way to convert recarray to a normal array is through pandas
    df = pd.DataFrame(recarray)

    # In case groups have different order. List conversion helps to prevent error, when `groups_order` is hashable (e.g. tuple)
    converted_recarray = df[list(groups_order)]
    concatenated_arrays = pd.concat([converted_recarray, pd.DataFrame(array, columns=groups_order)],
                                    ignore_index=True, axis=0)
    
    return concatenated_arrays.to_records(index=False)


def _adjust_pvalues(pvals: np.recarray, corr_method: _datatypes._corr_method):
    """Perform per group p-values correction with a given `corr_method`
    
    Args:
        pvals: numpy records array with p-values. The resulting p-values are corrected per group (i.e. column)
        corr_method: p-value correction method

    Returns:
        Records array of the same format as an input but with corrected p-values
    """
    from statsmodels.stats.multitest import multipletests

    method_map = {
        "benjamini-hochberg": "fdr_bh",
        "bonferroni": "bonferroni"
    }

    pvals_adj = np.ones_like(pvals)

    for group in pvals.dtype.names:
        group_pvals = pvals[group]
        
        _, group_pvals_adj, _, _ = multipletests(
            group_pvals, alpha=0.05, method=method_map[corr_method]
        )
        pvals_adj[group] = group_pvals_adj

    return pvals_adj


def _sort_features(adata, key_added="rank_features_groups") -> None:
    """Sort results of :func:`~ehrapy.tl.rank_features_groups` by adjusted p-value
    
    Args:
        adata: Annotated data matrix after running :func:`~ehrapy.tl.rank_features_groups`
        key_added: The key in `adata.uns` information is saved to.

    Returns:
        Nothing. The operation is performed in place
    """
    if key_added not in adata.uns:
        return

    pvals_adj = adata.uns[key_added]["pvals_adj"]

    for group in pvals_adj.dtype.names:
        group_pvals = pvals_adj[group]
        sorted_indexes = np.argsort(group_pvals)
        
        for key in adata.uns[key_added].keys():
            if key == "params":
                # This key only stores technical information, nothing to sort here
                continue
            
            # Sort every key (e.g. pvals, names) by adjusted p-value in an increasing order
            adata.uns[key_added][key][group] = adata.uns[key_added][key][group][sorted_indexes]


def _save_rank_features_result(adata, key_added, names, scores, pvals, pvals_adj=None, logfoldchanges=None, pts=None, groups_order=None) -> None:
    """Write keys with statistical test results to adata.uns
    
    Args:
        adata: Annotated data matrix after running :func:`~ehrapy.tl.rank_features_groups`
        key_added: The key in `adata.uns` information is saved to.
        names: Structured array storing the feature names
        scores: Array with the statistics
        logfoldchanges: logarithm of fold changes or other info to store under logfoldchanges key
        pvals: p-values of a statistical test 
        pts: Percentages of cells containing features
        groups_order: order of groups in structured arrays

    Returns:
        Nothing. The operation is performed in place
    """
    fields = (names, scores, pvals, pvals_adj, logfoldchanges, pts)
    field_names = ("names", "scores", "pvals", "pvals_adj", "logfoldchanges", "pts")

    for values, key in zip(fields, field_names):
        if values is None or not len(values):
            continue

        if key not in adata.uns[key_added]:
            adata.uns[key_added][key] = values
        else:
            adata.uns[key_added][key] = _merge_arrays(
                recarray=adata.uns[key_added][key],
                array=np.array(values),
                groups_order=groups_order
            )

def _get_groups_order(groups_subset, group_names, reference):
    """Convert `groups` parameter of :func:`~ehrapy.tl.rank_features_groups` to a list of groups
    
    Args:
        groups_subset: Subset of groups, e.g. [`'g1'`, `'g2'`, `'g3'`], to which comparison
                       shall be restricted, or `'all'` (default), for all groups.
        group_names: list of all available group names
        reference: One of the groups of `'rest'`

    Returns:
        List of groups, subsetted or full
    """
    if groups_subset == "all":
        groups_order = group_names
    elif isinstance(groups_subset, (str, int)):
        raise ValueError("Specify a sequence of groups")
    else:
        groups_order = list(groups_subset)
        if isinstance(groups_order[0], int):
            groups_order = [str(n) for n in groups_order]
        if reference != "rest" and reference not in groups_order:
            groups_order += [reference]
    if reference != "rest" and reference not in group_names:
        raise ValueError(
            f"reference = {reference} needs to be one of groupby = {group_names}."
        )
    
    return groups_order

def _evaluate_categorical_features(
        adata,
        groupby,
        group_names,
        groups: Union[Literal["all"], Iterable[str]] = "all",
        reference: str = "rest", 
        categorical_method: _datatypes._rank_features_groups_cat_method = "g-test", 
        pts=False
):
    """Run statistical test for categorical features

    Args:
        adata: Annotated data matrix.
        groupby: The key of the observations grouping to consider.
        groups: Subset of groups, e.g. [`'g1'`, `'g2'`, `'g3'`], to which comparison
                shall be restricted, or `'all'` (default), for all groups.
        reference: If `'rest'`, compare each group to the union of the rest of the group.
                   If a group identifier, compare with respect to this group.
        pts: Whether to add 'pts' key to output. Doesn't contain useful information in this case.
        categorical_method: statistical method to calculate differences between categories

    Returns:
        *names*: `np.array` 
                  Structured array to be indexed by group id storing the feature names
        *scores*: `np.array`
                  Array to be indexed by group id storing the statistic underlying
                  the computation of a p-value for each feature for each group.
        *logfoldchanges*: `np.array`
                          Always equal to 1 for this function 
        *pvals*: `np.array`
                 p-values of a statistical test 
        *pts*: `np.array`
                 Always equal to 1 for this function
    """
    from scipy.stats import chi2_contingency

    tests_to_lambdas = {
        "chi-square": 1,
        "g-test": 0,
        "freeman-tukey": -1/2,
        "mod-log-likelihood": -1,
        "neyman": -2,
        "cressie-read": 2/3,
    }

    categorical_names = []
    categorical_scores = []
    categorical_pvals = []
    categorical_logfoldchanges = []
    categorical_pts = []

    groups_order = _get_groups_order(groups_subset=groups, group_names=group_names, reference=reference)

    groups_values = adata.obs[groupby].to_numpy()

    for feature in adata.uns["non_numerical_columns"]:
        if feature == groupby or "ehrapycat_" + feature == groupby or feature == "ehrapycat_" + groupby:
            continue
            
        feature_values = adata[:, feature].X.flatten().toarray()

        pvals = []
        scores = []

        for group in group_names:
            if group not in groups_order:
                continue

            if reference == "rest":
                reference_mask = (groups_values != group) & np.isin(groups_values, groups_order)
                contingency_table = pd.crosstab(feature_values, reference_mask)
            else:
                obs_to_take = np.isin(groups_values, [group, reference])
                reference_mask = groups_values[obs_to_take] == reference
                contingency_table = pd.crosstab(feature_values[obs_to_take], reference_mask)

            score, p_value, _, _ = chi2_contingency(
                contingency_table.values, lambda_=tests_to_lambdas[categorical_method])
            scores.append(score)
            pvals.append(p_value)
        
        categorical_names.append([feature] * len(group_names))
        categorical_scores.append(scores)
        categorical_pvals.append(pvals)
        # It is not clear, how to interpret logFC or percentages for categorical data
        # For now, leave some values so that plotting and sorting methods work
        categorical_logfoldchanges.append(np.ones(len(group_names)))
        if pts:
            categorical_pts.append(np.ones(len(group_names)))

    return (
        np.array(categorical_names), 
        np.array(categorical_scores),
        np.array(categorical_pvals),
        np.array(categorical_logfoldchanges),
        np.array(categorical_pts)
    )
