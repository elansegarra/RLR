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
        """ Validate and load either the variable schema or comparison options

        Args:
            var_schema: (list of dicts) where each dictionary has 3 keys
                'name': (str) name of variable group
                'lvars': (list of str) column names of variable in left data set
                'rvars': (list of str) column names of variable in right data set
            comp_options: (list of str) indicates the possible choice for a match determination
        """
        if var_schema is not None:
            # Verify that var_schema is properly structured
            for var_group in var_schema:
                assert 'name' in var_group, f"No 'name' key found in {var_group}"
                assert 'lvars' in var_group, f"No 'lvars' key found in {var_group}"
                assert 'rvars' in var_group, f"No 'rvars' key found in {var_group}"
            self.var_schema = var_schema
        if comp_options is not None:
            # Verify that comp_options is a list of strings
            assert isinstance(comp_options, list), f"The object passed to 'comp_options' is not a list"
            self.comp_options = [str(opt) for opt in comp_options]

        pass

    def get_curr_comp_pair(self):
        return self.comp_pairs[self.curr_comp_pair_index]

    def get_var_schema(self):
        return self.var_schema
    
    def get_comp_options(self):
        return self.comp_options