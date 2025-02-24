import scanpy as sc
import pandas as pd
import os
from pathlib import Path
from scipy.sparse import issparse


def run_umap_pipeline(
        data_matrix_filename: str,
        meta_data_filename: str,
        organism: str,
        uuid_folder_name: str,
        filter_cells: bool = True,
        filter_cells_value: int = 200,
        filter_genes: bool = True,
        filter_genes_value: int = 3,
        qc_filter: bool = True,
        qc_filter_value: float = 10,
        data_normalize: bool = True,
        data_normalize_value: int = 1e4,
        log_transform: bool = True,
        pca_components: int = 10,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = "cosine",
) -> pd.DataFrame:
    if uuid_folder_name is None:
        raise ValueError("Analysis hash id is missing")

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads/" + uuid_folder_name)
    data_matrix_path = os.path.join(upload_dir, data_matrix_filename)
    meta_data_path = os.path.join(upload_dir, meta_data_filename)

    if not Path(data_matrix_path).exists():
        raise FileNotFoundError(f"File not found: {data_matrix_path}")
    if not Path(meta_data_path).exists():
        raise FileNotFoundError(f"File not found: {meta_data_path}")

    # Load data
    print("Loading data...")
    data_matrix = pd.read_csv(data_matrix_path, delimiter="\t", index_col=0).T
    meta_data = pd.read_csv(meta_data_path, sep="\t", index_col=0)

    # Standardize index
    meta_data.index = meta_data.index.str.replace(r"[ -]", ".", regex=True)
    common_indices = data_matrix.index.intersection(meta_data.index)
    data_matrix, meta_data = data_matrix.loc[common_indices], meta_data.loc[common_indices]

    # Convert to AnnData
    adata = sc.AnnData(data_matrix)
    adata.obs = meta_data

    # Filter cells and genes
    print("Filtering data...")
    if filter_cells:
        sc.pp.filter_cells(adata, min_genes=filter_genes_value)
    if filter_genes:
        sc.pp.filter_genes(adata, min_cells=filter_cells_value)

    # Mitochondrial gene filtering (modify for organism if needed)
    print("Filtering mitochondrial genes...")
    if qc_filter:
        if organism.lower() == "human":
            adata.var["mt"] = adata.var_names.str.startswith("MT-")
        elif organism.lower() == "mouse":
            adata.var["mt"] = adata.var_names.str.startswith("mt-")
        else:
            raise ValueError(f"Unknown organism: {organism}")
        sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
        adata = adata[adata.obs.pct_counts_mt < qc_filter_value, :]
        del adata.var["mt"]

    # Normalization
    print("Normalizing data...")
    if data_normalize:
        sc.pp.normalize_total(adata, target_sum=data_normalize_value)

    # Log transformation
    print("Log transforming data...")
    if log_transform == "on":
        sc.pp.log1p(adata)

    # # Select highly variable genes
    # if highly_variable_genes:
    #     sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, subset=True)

    # PCA
    print("Running PCA...")
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=pca_components)

    # Compute nearest neighbors and run UMAP
    print("Running UMAP...")
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=pca_components, metric=metric)
    sc.tl.umap(adata, min_dist=min_dist)

    # Save UMAP results
    print("Saving UMAP coordinates...")
    umap_df = adata.obsm.to_df()
    umap_df["Cluster"] = "NNN"

    return umap_df


def run_umap_pipeling_anndata(
        adata_filename: str,
        organism: str,
        uuid_folder_name: str,
        filter_cells: bool = True,
        filter_cells_value: int = 200,
        filter_genes: bool = True,
        filter_genes_value: int = 3,
        qc_filter: bool = True,
        qc_filter_value: float = 10,
        data_normalize: bool = True,
        data_normalize_value: int = 1e4,
        log_transform: bool = True,
        pca_components: int = 10,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = "cosine",
) -> pd.DataFrame:
    if uuid_folder_name is None:
        raise ValueError("Analysis hash id is missing")

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads/" + uuid_folder_name)
    adata_path = os.path.join(upload_dir, adata_filename)

    if not Path(adata_path).exists():
        raise FileNotFoundError(f"File not found: {adata_path}")

    # Load AnnData object
    adata = sc.read_h5ad(adata_path)

    # Save gene expression and metadata
    gene_expression_df = pd.DataFrame(
        adata.X.toarray() if issparse(adata.X) else adata.X,
        index=adata.obs.index,
        columns=adata.var.index
    ).T
    gene_expression_df.to_csv(os.path.join(upload_dir, "gene_expression.tsv"), sep="\t")
    adata.obs.to_csv(os.path.join(upload_dir, "meta_data.tsv"), sep="\t")

    # Filter cells and genes
    print("Filtering data...")
    if filter_cells:
        sc.pp.filter_cells(adata, min_genes=filter_genes_value)
    if filter_genes:
        sc.pp.filter_genes(adata, min_cells=filter_cells_value)

    # Filter mitochondrial genes based on organism
    print("Filtering mitochondrial genes...")
    if qc_filter:
        if organism.lower() == "human":
            adata.var["mt"] = adata.var_names.str.startswith("MT-")
        elif organism.lower() == "mouse":
            adata.var["mt"] = adata.var_names.str.startswith("mt-")
        else:
            raise ValueError(f"Unknown organism: {organism}")
        sc.pp.calculate_qc_metrics(
            adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
        )
        adata = adata[adata.obs.pct_counts_mt < qc_filter_value, :]
        del adata.var["mt"]

    # Normalize data
    print("Normalizing data...")
    if data_normalize:
        sc.pp.normalize_total(adata, target_sum=data_normalize_value)

    # Log transformation
    print("Log transforming data...")
    if log_transform:
        sc.pp.log1p(adata)

    # # Select highly variable genes
    # if highly_variable_genes:
    #     sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, subset=True)

    # Perform PCA
    print("Running PCA...")
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=pca_components)

    # Perform UMAP
    print("Running UMAP...")
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=pca_components, metric=metric)
    sc.tl.umap(adata, min_dist=min_dist)

    print("Saving UMAP coordinates...")
    umap_df = adata.obsm.to_df()
    umap_df.index = adata.obs_names
    umap_df["Cluster"] = "NNN"

    return umap_df
