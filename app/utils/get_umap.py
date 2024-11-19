import pandas as pd


def get_umap_coordinates(umap_path):
    """
    Get UMAP coordinates from the UMAP output file
    :param umap_path: Path to the UMAP output file
    :return: UMAP coordinates as a pandas DataFrame
    """
    umap_df = pd.read_csv(umap_path, index_col=0)
    return umap_df
