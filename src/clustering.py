import pandas as pd
from sklearn.cluster import KMeans

def kmeans_clusters(deliveries_csv: str, k: int, out_csv: str):
    df = pd.read_csv(deliveries_csv)
    X = df[["lat", "lon"]].to_numpy()

    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    df["cluster"] = km.fit_predict(X)

    df.to_csv(out_csv, index=False)
    return df
