import scanpy as sc
import pandas as pd
import os

# Path to the "uploads" folder (use absolute path for robustness)
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def run_umap_pipeline(data_matrix_filename: str,
                      meta_data_filename: str,
                      organism: str,
                      filter_cells: str = 'on',
                      filter_cells_value: int = 200,
                      filter_genes: str = 'on',
                      filter_genes_value: int = 3,
                      qc_filter: str = 'on',
                      qc_filter_value: float = 10,
                      data_normalize: str = 'on',
                      data_normalize_value: int = 1e4,
                      log_transform: str = 'on',
                      pca_components: int = 10,
                      n_neighbors: int = 15,
                      min_dist: float = 0.1,
                      metric: str = 'cosine',
                      ) -> None:
    # Load the expression matrix and metadata
    data_matrix_filename = os.path.join(UPLOADS_DIR, data_matrix_filename)
    meta_data_filename = os.path.join(UPLOADS_DIR, meta_data_filename)

    adata = sc.read_csv(data_matrix_filename, delimiter='\t').T
    meta_data = pd.read_csv(meta_data_filename, sep="\t", index_col=0)

    # Check length of metadata and data if they are equal
    if len(adata.obs) != len(meta_data):
        raise ValueError("Length of metadata and data matrix should be equal")

    adata.obs = meta_data

    print("Filtering and normalizing data...")
    # Filter cells and genes
    if filter_cells == 'on':
        sc.pp.filter_cells(adata, min_genes=filter_genes_value)
    if filter_genes == 'on':
        sc.pp.filter_genes(adata, min_cells=filter_cells_value)

    print("Filtering mitochondrial genes...")
    # QC filter
    # if qc_filter == 'on':
    #     adata.var['mt'] = adata.var_names.str.startswith('MT-')
    #     sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)
    #     adata = adata[adata.obs.pct_counts_mt < qc_filter_value, :]
    #     del adata.var['mt']

    print("Normalizing data...")
    # Data normalization
    if data_normalize == 'on':
        sc.pp.normalize_total(adata, target_sum=data_normalize_value)
    if log_transform == 'on':
        sc.pp.log1p(adata)

    # sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    # sc.pp.scale(adata, max_value=10)

    print("Running PCA and UMAP...")
    # Perform PCA
    sc.tl.pca(adata, n_comps=pca_components)

    print("Running UMAP...")
    # Perform UMAP
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=pca_components, metric=metric)
    sc.tl.umap(adata, min_dist=min_dist)

    print("Saving UMAP coordinates...")
    cluster_column = "seurat_clusters"

    # umap_results = pd.DataFrame(adata.obsm["X_umap"], columns=["UMAP1", "UMAP2"], index=adata.obs_names)
    # umap_results["Cluster"] = (adata.obs[cluster_column] if cluster_column in adata.obs else None)

    # Save the UMAP coordinates
    umap_df = adata.obsm.to_df()
    umap_df["Cluster"] = (adata.obs[cluster_column] if cluster_column in adata.obs else None)

    umap_output_filename = os.path.join(UPLOADS_DIR, "umap_coordinates.csv")
    umap_df.to_csv(umap_output_filename)

    # umap_output_filename = os.path.join(UPLOADS_DIR, "umap_results.csv")
    # umap_results.to_csv(umap_output_filename)
