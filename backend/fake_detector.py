import pandas as pd
import os

class AccountVerifier:
    def __init__(self, vip_dataset="data/real_vip_accounts.csv"):
        if not os.path.exists(vip_dataset):
            raise FileNotFoundError(f"VIP dataset not found: {vip_dataset}")
        self.vip_df = pd.read_csv(vip_dataset)

    def verify(self, account_dict, id_column="Name"):
        """
        Checks if account exists in the VIP dataset.
        - If yes → Real
        - If no → Fake
        """
        if id_column not in self.vip_df.columns:
            raise ValueError(f"VIP dataset must contain column '{id_column}'")

        account_name = account_dict.get(id_column, None)
        if account_name is None:
            return {"is_fake": True, "reason": f"No {id_column} provided"}

        if account_name in self.vip_df[id_column].values:
            return {"is_fake": False, "reason": "Verified VIP account"}
        else:
            return {"is_fake": True, "reason": "Not An Official Account"}
