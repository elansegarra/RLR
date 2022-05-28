import pandas as pd

class rlr:

    def __init__(self):
        self.dataL = None
        self.dataR = None

    def load_datasets(self, dataL, dataR, id_vars):
        pass

    def load_comp_pairs(self, comp_pairs):
        self.comp_pairs = comp_pairs
        self.curr_comp_pair_index = 0
    
    def load_comp_schema(self, var_schema = None, comp_options = None):
        pass

    def get_curr_comp_pair(self):
        return self.comp_pairs[self.curr_comp_pair_index]

    def get_var_schema(self):
        return self.var_schema
    
    def get_comp_options(self):
        return self.comp_options