import pandas as pd

class rlr:

    def __init__(self):
    def load_datasets(self, data_l_path, data_r_path, 
                        id_vars_both = None, id_vars_l = None, id_vars_r = None):
        """ Loads two data sets and specifies the id variables in each 
        
        Args:
            data_l_path: (str) path to left data set file (either csv or dta)
            data_r_path: (str) path to right data set file (either csv or dta)
            id_vars: (str or list of str) variables that uniquely define a record in both data sets
            id_vars_l: (str or list of str) variables that uniquely define a record in left data set
            id_vars_r: (str or list of str) variables that uniquely define a record in right data set
                note: passing id_vars will trump both id_Vars_l and id_vars_r
        """
        # Check for file and file type, then load each file into a df
        data_l_ext = os.path.splitext(data_l_path)[1]
        data_r_ext = os.path.splitext(data_r_path)[1]
        if      data_l_ext == ".csv":   self.dataL = pd.read_csv(data_l_path)
        elif    data_l_ext == ".dta":   self.dataL = pd.read_stata(data_l_path)
        else:                           
            raise NotImplementedError(f"Filetype of {data_l_path} must be either csv or dta")
        if      data_r_ext == ".csv":   self.dataR = pd.read_csv(data_r_path)
        elif    data_r_ext == ".dta":   self.dataR = pd.read_stata(data_r_path)
        else:                           
            raise NotImplementedError(f"Filetype of {data_r_path} must be either csv or dta")
        
        # Check that user passed (id_vars_both) or (id_vars_l and id_vars_r) 
        if (id_vars_both is None) and ((id_vars_l is None) or (id_vars_r is None)):
            raise NotImplementedError("User must pass at least one id variable")

        # Passing id_vars_both will ignore any values passed to either id_vars_l or id_vars_r
        if id_vars_both is not None:
            id_vars_l = id_vars_both
            id_vars_r = id_vars_both

        # Validate left ids (check they exist and uniquely define a row) and save them
        if isinstance(id_vars_l, str): id_vars_l = [id_vars_l] # Convert to list if a string
        ids_exist = pd.Series(id_vars_l).isin(self.dataL.columns).all()
        assert ids_exist, f"id variables ({id_vars_l}) not found in the left data set"
        assert self.dataL.set_index(id_vars_l).index.is_unique, f"id variables ({id_vars_l} do not uniquely identify the left data set"
        self.id_vars_l = id_vars_l
        self.dataL.set_index(self.id_vars_l, inplace=True, drop=False)
        # Validate right ids (check they exist and uniquely define a row) and save them
        if isinstance(id_vars_r, str): id_vars_r = [id_vars_r] # Convert to list if a string
        ids_exist = pd.Series(id_vars_r).isin(self.dataR.columns).all()
        assert  ids_exist, f"id_vars_r ({id_vars_r}) not found in the right data set"
        assert self.dataR.set_index(id_vars_r).index.is_unique, f"id variables ({id_vars_r} do not uniquely identify the right data set"
        self.id_vars_r = id_vars_r
        self.dataR.set_index(self.id_vars_r, inplace=True, drop=False)

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