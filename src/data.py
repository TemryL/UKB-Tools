import pandas as pd
from .tools import split_ukb_column


class UKBData:
    def __init__(self, data_path, ukb_dict_path):
        self.path = data_path
        self.ukb_dict_path = ukb_dict_path
    
    def load_data(self, nrows=None, instance=None):
        data = pd.read_csv(self.path, nrows=nrows, low_memory=False)
        data = data.set_index('eid')
        if instance is not None:
            data = self.filter_ukb_instance(data, instance=instance)
        self.data = data    
        return data

    def filter_ukb_instance(self, instance='0'):
        cols_to_drop = []
        for col in self.data.columns:
            field_id, instance_id, _ = split_ukb_column(col)
            if (field_id is None) or (instance_id is None):
                continue
            if instance_id != instance:
                cols_to_drop.append(col)
        return self.data.drop(columns=cols_to_drop)