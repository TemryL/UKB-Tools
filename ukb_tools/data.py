import pandas as pd
from .tools import split_ukb_column, filter_cols


class UKB:
    def __init__(self, data_path):
        self.path = data_path
        self.data = None

    def load_data(self, nrows=None, instance=None):
        data = pd.read_csv(self.path, nrows=nrows, low_memory=False)
        self.data = data.set_index("eid")
        if instance is not None:
            self.data = self._filter_ukb_instance(instance=instance)
        return data

    def preprocess(self, pipeline, args):
        self.data = pipeline(self.data, *args)
        return self.data

    def _filter_ukb_instance(self, instance="0"):
        cols_to_drop = []
        for col in self.data.columns:
            field_id, instance_id, _ = split_ukb_column(col)
            if (field_id is None) or (instance_id is None):
                continue
            if instance_id != instance:
                cols_to_drop.append(col)
        return self.data.drop(columns=cols_to_drop)

    def filter_cols(self, field_ids):
        cols = filter_cols(self.data.columns, field_ids)
        return self.data[cols]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, eid):
        return self.data[eid]
