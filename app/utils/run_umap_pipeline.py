import scanpy as sc
import pandas as pd
import os
from pathlib import Path

# Path to the "uploads" folder (use absolute path for robustness)
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def run_umap_pipeline(
        data_matrix_filename: str,
        meta_data_filename: str,
        organism: str,
        filter_cells: str = "on",
        filter_cells_value: int = 200,
        filter_genes: str = "on",
        filter_genes_value: int = 3,
        qc_filter: str = "on",
        qc_filter_value: float = 10,
        data_normalize: str = "on",
        data_normalize_value: int = 1e4,
        log_transform: str = "on",
        pca_components: int = 10,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = "cosine",
) -> None:
    data_matrix_path = os.path.join(UPLOADS_DIR, data_matrix_filename)
    meta_data_path = os.path.join(UPLOADS_DIR, meta_data_filename)

    if not Path(data_matrix_path).exists():
        raise FileNotFoundError(f"File not found: {data_matrix_path}")
    if not Path(meta_data_path).exists():
        raise FileNotFoundError(f"File not found: {meta_data_path}")

    # Use pandas to read the data for better performance
    data_matrix = pd.read_csv(data_matrix_path, delimiter="\t", index_col=0).T
    meta_data = pd.read_csv(meta_data_path, sep="\t", index_col=0)

    meta_data.index = meta_data.index.str.replace(r"[ -]", ".", regex=True)

    # Match index of data_matrix and meta_data
    common_indices = data_matrix.index.intersection(meta_data.index)
    data_matrix = data_matrix.loc[common_indices]
    meta_data = meta_data.loc[common_indices]

    adata = sc.AnnData(data_matrix)
    adata.obs = meta_data

    # Filter cells and genes
    print("Filtering and normalizing data...")
    if filter_cells == "on":
        sc.pp.filter_cells(adata, min_genes=filter_genes_value)
    if filter_genes == "on":
        sc.pp.filter_genes(adata, min_cells=filter_cells_value)

    # Filter mitochondrial genes
    print("Filtering mitochondrial genes...")
    if qc_filter == 'on':
        adata.var['mt'] = adata.var_names.str.startswith('MT-')
        sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)
        adata = adata[adata.obs.pct_counts_mt < qc_filter_value, :]
        del adata.var['mt']

    # Normalize data
    print("Normalizing data...")
    if data_normalize == "on":
        sc.pp.normalize_total(adata, target_sum=data_normalize_value)

    # Log transformation
    print("Log transforming data...")
    if log_transform == "on":
        sc.pp.log1p(adata)

    # sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    # sc.pp.scale(adata, max_value=10)

    # Perform PCA
    print("Running PCA...")
    sc.tl.pca(adata, n_comps=pca_components)

    # Perform UMAP
    print("Running UMAP...")
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=pca_components, metric=metric)
    sc.tl.umap(adata, min_dist=min_dist)

    print("Saving UMAP coordinates...")
    cluster_column = "seurat_clusters"

    # Save the UMAP coordinates
    umap_df = adata.obsm.to_df()
    umap_df["Cluster"] = (
        adata.obs[cluster_column] if cluster_column in adata.obs else None
    )

    umap_output_path = os.path.join(UPLOADS_DIR, "umap_coordinates.csv")
    umap_df.to_csv(umap_output_path)
