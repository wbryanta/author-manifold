"""author_manifold — author-relative measurement space for stylometric placement.

Core API:

    from author_manifold.author_space import AuthorRelativeSpace, load_shelf
    from author_manifold.attribution_metrics import compute_roc_auc
"""

# 2.0.0 removed compute_c_llr() from attribution_metrics. Nothing else in
# the API moved; the removal alone is what makes it a major bump. The name
# is retained as a raising stub so the breakage names its own cause.
__version__ = "2.0.0"
