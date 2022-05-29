import pandas as pd
import numpy as np
import os
import warnings

class rlr:
    """ RLR: Record Linkage Review
        This class functions as the backend for reviewing and labeling pairs
        of potential links between two loaded datasets.
    """
    REV_LABEL_COL = "rlr_label"
    REV_LABEL_IND_COL = "rlr_label_ind"
    REV_DATE_COL = "rlr_choice_date"
    REV_NOTE_COL = "rlr_note"
    COMP_EXIST_THRESH = 0.8  # Set to 0 to skip checking if all comp pairs exist in data

    def __init__(self):
        self.dataL = None
        self.dataR = None
        self.comp_df = None
        self.ready_to_review = False

    def load_datasets(self, data_l_path, data_r_path, id_vars_l, id_vars_r):
        """ Loads two data sets and specifies the id variables in each 
        
        Args:
            data_l_path: (str) path to left data set file (either csv or dta)
            data_r_path: (str) path to right data set file (either csv or dta)
            id_vars_l: (str or list of str) variables that uniquely define a record in left data set
            id_vars_r: (str or list of str) variables that uniquely define a record in right data set
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
        
        # Standardize ids and check they differ
        if isinstance(id_vars_l, str): id_vars_l = [id_vars_l] # Convert to list if a string
        if isinstance(id_vars_r, str): id_vars_r = [id_vars_r] # Convert to list if a string
        id_overlap = set(id_vars_l) & set(id_vars_r)
        assert len(id_overlap) == 0, "Currently cannot handle overlapping id variables"

        # Validate left ids (check they exist and uniquely define a row) and save them
        ids_exist = pd.Series(id_vars_l).isin(self.dataL.columns).all()
        assert ids_exist, f"id variables ({id_vars_l}) not found in the left data set"
        assert self.dataL.set_index(id_vars_l).index.is_unique, f"id variables ({id_vars_l} do not uniquely identify the left data set"
        self.id_vars_l = id_vars_l
        self.dataL.set_index(self.id_vars_l, inplace=True, drop=False)
        # Validate right ids (check they exist and uniquely define a row) and save them
        ids_exist = pd.Series(id_vars_r).isin(self.dataR.columns).all()
        assert  ids_exist, f"id_vars_r ({id_vars_r}) not found in the right data set"
        assert self.dataR.set_index(id_vars_r).index.is_unique, f"id variables ({id_vars_r} do not uniquely identify the right data set"
        self.id_vars_r = id_vars_r
        self.dataR.set_index(self.id_vars_r, inplace=True, drop=False)

    def load_comp_pairs(self, comp_pairs_path):
        """ Loads a file with pairs of records to compare for review
        
        Args:
            comp_pairs_path: (str) path to tabular file containing pairs of id values
                from the dataL and dataR files. Data set should contain all columns 
                found in self.id_vars_l and self.id_vars_r
        """
        # Check that data has already been loaded
        assert self.dataL is not None, "Load a data file before loading a comparison file"
        assert self.dataR is not None, "Load a data file before loading a comparison file"
        # Validate file format and load the file
        data_ext = os.path.splitext(comp_pairs_path)[1]
        if      data_ext == ".csv":   comp_df = pd.read_csv(comp_pairs_path)
        elif    data_ext == ".dta":   comp_df = pd.read_stata(comp_pairs_path)
        else:   raise NotImplementedError(f"Filetype of {data_ext} must be either csv or dta")
        
        # Check that ids in the file are found in the data files
        l_ids_exist = pd.Series(self.id_vars_l).isin(comp_df.columns).all()
        r_ids_exist = pd.Series(self.id_vars_r).isin(comp_df.columns).all()
        assert l_ids_exist, f"Left data ids ({self.id_vars_l}) not found in passed comparison file."
        assert r_ids_exist, f"Right data ids ({self.id_vars_r}) not found in passed comparison file."

        # Check that id_vars_l and id_vars_r form a unqiue id for records in comparison file
        all_ids = self.id_vars_l + self.id_vars_r
        ids_are_unique = comp_df.set_index(all_ids).index.is_unique
        assert ids_are_unique, f"Id variables ({all_ids} do not uniquely identify records in comparison file"
        # comp_df.set_index(all_ids, inplace=True, drop=False)
        
        # Check that id value pairs are found in the data files (assuming a positive threshhold)
        num_missing = 0
        if self.COMP_EXIST_THRESH > 0:
            for i in range(comp_df.shape[0]):
                # TODO: Below logic assumes id_vars only include one variable each
                l_id = comp_df.iloc[i][self.id_vars_l[0]]
                r_id = comp_df.iloc[i][self.id_vars_r[0]]
                if (l_id not in self.dataL.index) or (r_id not in self.dataR.index):
                    comp_df.at[i, self.REV_LABEL_IND_COL] = -1
                    num_missing += 1
        perc_found = (comp_df.shape[0] - num_missing)/comp_df.shape[0]
        if perc_found < self.COMP_EXIST_THRESH:
            warnings.warn(f"Only found {np.round(perc_found*100,1)}% of comparison ids.")
        
        # Add comparison columns if not already there
        for comp_var in [self.REV_LABEL_COL, self.REV_LABEL_IND_COL, 
                        self.REV_DATE_COL, self.REV_NOTE_COL]:
            if comp_var not in comp_df: comp_df[comp_var] = None

        # Save comparison file to class instance and instantiate other relvant variables
        self.comp_df = comp_df
        self.curr_comp_pair_index = 0
        self.num_comparisons = self.comp_df.shape[0]
    
    def set_var_comp_schema(self, var_schema):
        """ Validate and load the variable comparison schema

        Args:
            var_schema: list of dicts
                Each element represents the group of variables that should be compared
                across the data sets. Each dictionary in the list has 3 keys
                'name': (str) name of variable group
                'lvars': (list of str) column names of variable in left data set
                'rvars': (list of str) column names of variable in right data set
        """
        # Check that data has already been loaded
        assert self.dataL is not None, "Load data files before loading a comparison schema"
        assert self.dataR is not None, "Load data files before loading a comparison schema"

        # Iterate through variable groups and validate each
        for var_group in var_schema:
            # Verify that var_group is properly structured
            assert 'name' in var_group, f"No 'name' key found in {var_group}"
            assert 'lvars' in var_group, f"No 'lvars' key found in {var_group}"
            assert 'rvars' in var_group, f"No 'rvars' key found in {var_group}"
            # Verify that lvars and rvars in var_group exist in the datasets
            ids_exist = pd.Series(var_group['lvars']).isin(self.dataL.columns).all()
            assert  ids_exist, f"Schema variables ({var_group['lvars']}) not found in the left data set"
            ids_exist = pd.Series(var_group['rvars']).isin(self.dataR.columns).all()
            assert  ids_exist, f"Schema variables ({var_group['rvars']}) not found in the right data set"
        # Save the variable schema to the class instance
        self.var_schema = var_schema

    def set_label_choices(self, label_choices):
        """ Set the label choices (by passing a list of strings) """ 
        # Verify that comp_options is a list of strings
        assert isinstance(label_choices, list), f"The object passed to 'label_choices' is not a list"
        self.label_choices = [str(opt) for opt in label_choices]

    def get_comp_pair(self, raw_or_grouped, comp_ind = None):
        """ Returns a dictionary of the data in the current comparison pair
            
        Args:
            raw_or_grouped: string (either "raw" or "grouped")
                Indicates whether to return the raw data (i.e. a dictionary of dictionaries 
                of the values associated with each record) or grouped data (i.e. a list of 
                dictionaries where each dictionaries corresponds with the variable group defined
                in var_schema)
            comp_ind: int, optional
                Integer index of the comparison pair (in comp_df) to return data from. If 
                it is not passed, then it defaults to the curr_comp_pair_index
        Returns: 
            If "raw" -> dictionary with two keys ('l_rec' and 'r_rec')
            If "grouped" -> list of dictionaries where each dict has three 
                                keys ('name', 'lvar_values', and 'rvar_values')
        """
        # Verify that data sets and comparison sets have been loaded
        assert self.dataL is not None, "Load data files before getting a comparison pair"
        assert self.dataR is not None, "Load data files before getting a comparison pair"
        assert self.comp_df is not None, "Load comparison data file before getting a comparison pair"

        # Sets default index if nothing passed
        if comp_ind is None: comp_ind = self.curr_comp_pair_index
        # Verify that index is valid (ie in range of rows of comp_df)
        index_in_range = (0 <= comp_ind <= len(self.comp_df)-1)
        assert index_in_range, f"Comparison index ({comp_ind}) is out of bounds"

        # Extract raw data associated with the comparison pair ids
        # TODO: Below code assumes id_vars has only one variable (need to generalize to multi-index)
        l_id = self.comp_df.loc[comp_ind,self.id_vars_l[0]]
        r_id = self.comp_df.loc[comp_ind,self.id_vars_r[0]]
        l_rec_data = self.dataL.loc[l_id].to_dict()
        r_rec_data = self.dataR.loc[r_id].to_dict()

        # Check requested data format and process accordingly
        if raw_or_grouped == "raw":
            return {'l_rec': l_rec_data, 'r_rec': r_rec_data}
        elif raw_or_grouped == "grouped":
            # Process raw data into data grouped according to var_schema
            rec_data_grouped = []
            for var_group in self.var_schema:
                # Get values of each variable in the group from the data records
                var_group_data = {'name':var_group['name'],
                                'lvals': [l_rec_data[var] for var in var_group['lvars']],
                                'rvals': [r_rec_data[var] for var in var_group['rvars']]}
                rec_data_grouped.append(var_group_data)
            return rec_data_grouped
        else:
            raise NotImplementedError(f"")

    def get_var_comp_schema(self):
        return self.var_schema
    
    def get_label_choices(self):
        return self.label_choices

    def save_comp_choice(self, choice, comp_pair_ind = None):
        # Checks and saves the choice to the current comparison pair (of that specified by comp_pair_ind)
        if choice not in self.comp_options:
            raise NotImplementedError
        else:
            pass