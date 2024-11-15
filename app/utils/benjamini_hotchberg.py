import pandas as pd
from statsmodels.stats.multitest import multipletests


def bh_frd_correction(p_value_file: str, alpha=0.05) -> pd.DataFrame:
    p_value_df = pd.read_csv(p_value_file, sep="\t")

    p_value_df.dropna(axis=1, how="all", inplace=True)

    # Make first column the index
    p_value_df.set_index("Unnamed: 0", inplace=True)

    # Create a dataframe of shape p_value_df with all NaN values
    df_reject = pd.DataFrame(index=p_value_df.index, columns=p_value_df.columns)

    for i in p_value_df.columns:
        tf_pval = p_value_df[i].dropna()

        reject, pvals_corrected, _, _ = multipletests(
            abs(tf_pval), alpha=alpha, method="fdr_bh"
        )

        tf_pval = pd.DataFrame(tf_pval)
        tf_pval["Reject"] = reject
        df_reject[i] = tf_pval["Reject"]

    return df_reject
