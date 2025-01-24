import os
import pandas as pd
import numpy as np
from scipy.stats import zscore
import requests
from scipy.special import erf
from joblib import Parallel, delayed

# This analysis using single n and all k's

# Path to the "uploads" folder (use absolute path for robustness)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def distribution_worker(max_target: int, ranks: np.array):
    cs = np.random.choice(ranks, max_target, replace=False).cumsum()
    arr = cs / np.arange(1, max_target + 1)
    return arr


def get_sd(max_target: int, total_genes: int, iters: int):
    sd_file = f"SD_anal_{max_target}_{total_genes}_{iters}.npz"
    sd_file = os.path.join(UPLOAD_DIR, sd_file)

    if os.path.isfile(sd_file):
        print("Distribution file exists. Now we have to read it.")
        return np.load(sd_file)["distribution"]

    print("Distribution file does not exist. Now we have to generate it.")

    # n = total_genes  # Sampling size for random distribution
    ranks = np.linspace(start=1, stop=total_genes, num=total_genes)
    ranks = (ranks - 0.5) / total_genes

    dist = Parallel(n_jobs=-1, verbose=2, backend="multiprocessing")(
        delayed(distribution_worker)(max_target, ranks) for _ in range(iters)
    )
    sd_dist = np.std(np.array(dist).T, axis=1)
    np.savez_compressed(file=sd_file, distribution=sd_dist)
    return sd_dist


def sample_worker(
    sample: pd.DataFrame,
    prior_network: pd.DataFrame,
    sd: np.array,
    max_target: int,
):
    sample.dropna(inplace=True)
    sample["rank"] = sample.rank(ascending=False)
    sample["rank"] = (sample["rank"] - 0.5) / len(sample)
    sample["rev_rank"] = 1 - sample["rank"]

    # Get target genes rank
    for tf_id, tf_row in prior_network.iterrows():
        targets = tf_row["target"]
        actions = tf_row["action"]

        # Valid target counts and total targets should be greater than 3
        valid_targets = len([t for t in targets if t in sample.index])
        if len(targets) < 3 or valid_targets < 3:
            prior_network.loc[tf_id, "rs"] = np.nan
            prior_network.loc[tf_id, "valid_target"] = np.nan
            continue

        acti_rs = 0
        inhi_rs = 0

        for i, action in enumerate(actions):
            if targets[i] in sample.index:
                if action == 1:
                    acti_rs += np.average(sample.loc[targets[i], "rank"])
                    inhi_rs += np.average(sample.loc[targets[i], "rev_rank"])
                else:
                    inhi_rs += np.average(sample.loc[targets[i], "rank"])
                    acti_rs += np.average(sample.loc[targets[i], "rev_rank"])

        rs = np.min([acti_rs, inhi_rs])
        rs = rs / valid_targets  # Average rank-sum
        prior_network.loc[tf_id, "rs"] = rs if acti_rs < inhi_rs else -rs
        prior_network.loc[tf_id, "valid_target"] = valid_targets

    # Identify non-NaN indices for 'rs' to filter the relevant rows
    valid_indices = ~np.isnan(prior_network["rs"])

    z_vals = (np.abs(prior_network.loc[valid_indices, "rs"]) - 0.5) / sd[
        prior_network.loc[valid_indices, "valid_target"].astype(int) - 1
    ]
    p_vals = 1 + erf(z_vals / np.sqrt(2))

    # Adjust sign based on 'rs' values
    p_vals = np.where(prior_network.loc[valid_indices, "rs"] > 0, p_vals, -p_vals)

    prior_network["p-value"] = np.nan
    prior_network.loc[valid_indices, "p-value"] = p_vals

    return prior_network["p-value"].values


def run_analysis(
    tfs,
    gene_exp: pd.DataFrame,
    prior_network: pd.DataFrame,
    sd_dist: np.array,
    max_target: int,
) -> pd.DataFrame:
    gene_exp = gene_exp.T
    parallel = Parallel(n_jobs=-1, verbose=2, backend="multiprocessing")
    output = parallel(
        delayed(sample_worker)(pd.DataFrame(row), prior_network, sd_dist, max_target)
        for idx, row in gene_exp.iterrows()
    )
    output = pd.DataFrame(output, columns=tfs, index=gene_exp.index)
    return output


def main(prior_network: pd.DataFrame, gene_exp: pd.DataFrame, iters: int):
    gene_exp = gene_exp.apply(zscore, axis=1, nan_policy="omit")

    # Grouping prior_network network
    prior_network = prior_network.groupby("tf").agg({"action": list, "target": list})
    prior_network["updown"] = prior_network["target"].apply(lambda x: len(x))

    max_target = np.max(prior_network["updown"])
    sd_dist = get_sd(
        max_target=max_target,
        total_genes=len(gene_exp),
        iters=iters,
    )

    return run_analysis(
        tfs=prior_network.index,
        gene_exp=gene_exp,
        prior_network=prior_network,
        sd_dist=sd_dist,
        max_target=max_target,
    )


def read_mouse_to_human_mapping_file():
    mth_file = "mouse_to_human.tsv"
    mth_file_path = os.path.join(UPLOAD_DIR, mth_file)

    if os.path.isfile(mth_file_path):
        print("Mouse to human mapping file exists. Let's read")
        return pd.read_csv(mth_file_path, sep="\t")

    print("Mouse to human mapping file does not exist. Let's download it.\n")
    file_url = "https://www.cs.umb.edu/~kisan/data/mouse_to_human.tsv"

    try:
        response = requests.get(file_url)
        with open(mth_file_path, "wb") as f:
            f.write(response.content)
        print("Mouse to human mapping file downloaded successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the mouse to human map file: {e}")
        raise Exception(f"Failed to download the mouse to human map file: {e}")

    return pd.read_csv(mth_file_path, sep="\t")


def read_data(p_file: str, g_file: str, upload_dir):
    p_file_path = os.path.join(upload_dir, p_file)

    prior_network = pd.read_csv(
        p_file_path,
        sep="\t",
        header=None,
        usecols=[0, 1, 2],
        names=["tf", "action", "target"],
        converters={
            "action": lambda x: (
                1
                if x == "upregulates-expression"
                else -1 if x == "downregulates-expression" else None
            )
        },
    ).dropna()
    prior_network = prior_network.reset_index(drop=True)

    g_file_path = os.path.join(upload_dir, g_file)
    gene_exp = pd.read_csv(g_file_path, sep="\t", index_col=0)

    # Mouse to human Mapping process
    mouse_to_human = read_mouse_to_human_mapping_file()

    # Replace index with human gene IDs, filter, clean, and explode
    gene_exp = gene_exp.rename(
        index=dict(zip(mouse_to_human["Mouse"], mouse_to_human["Human"]))
    )
    gene_exp = gene_exp[gene_exp.index.str.match(r"^\[.*\]$")]
    gene_exp.index = gene_exp.index.str.strip("[]")
    gene_exp = (
        gene_exp.assign(index=gene_exp.index.str.split(","))
        .explode("index")
        .reset_index(drop=True)
    )
    gene_exp = gene_exp.set_index("index")

    gene_exp = gene_exp.replace(0.0, np.nan).dropna(
        thresh=int(len(gene_exp.columns) * 0.05)
    )

    return prior_network, gene_exp


def get_pvalues(prior_file: str, gene_file: str, iters: int, upload_dir) -> pd.DataFrame:
    try:
        prior_net, gene_e = read_data(prior_file, gene_file, upload_dir)
        p_values = main(prior_net, gene_e, iters)
        p_values.dropna(axis=1, how="all", inplace=True)
        return p_values

    except Exception as e:
        raise Exception(f"Failed to run the analysis: {e}")
