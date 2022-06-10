import pandas as pd
import numpy as np
import os, sys
import warnings
import datetime
import json
from math import isnan

class rlr:
    """ RLR: Record Linkage Review
        This class functions as the backend for reviewing and labeling pairs
        of potential links between two loaded datasets.
    """
    REV_LABEL_COL = "rlr_label"
    REV_LABEL_IND_COL = "rlr_label_ind"
    REV_DATE_COL = "rlr_modified"
    REV_NOTE_COL = "rlr_note"
    COMP_EXIST_THRESH = 0.8  # Set to 0 to skip checking if all comp pairs exist in data
    COMP_PRINT_COL_WEIGHT = [0.4, 0.2, 0.4]
    COMP_DEFAULT_LINE_WIDTH = 80
    ADDTL_OPTION_TEXTS = ["(P) Previous", "(N) Next", "(G) Go to", 
                            "(A) Annotate", "(S) Summary", "(E) Exit"]
    ADDTL_OPTION_TAGS = [text[1].lower() for text in ADDTL_OPTION_TEXTS]
    DEFAULT_LABELS = ["Match", "Not a Match"]
    DEFAULT_AUTOSAVE = False

    def __init__(self, rev_packet_path = None):
        self.dataL_loaded = False
        self.dataR_loaded = False
        self.comps_loaded = False
        self.var_schema_loaded = False
        self.ready_to_review = False
        self.label_choices = self.DEFAULT_LABELS
        self.autosave = self.DEFAULT_AUTOSAVE

        # Load all the parameters in the review packet if passed
        if rev_packet_path is not None:
            # Read the parameter file
            with open(rev_packet_path, 'r') as openfile:
                rev_packet = json.load(openfile)
            # Load the parameters in the parameter dictionary
            self.load_review_packet(rev_packet)

    def check_ready_to_review(self):
        data_loaded = self.dataL_loaded and self.dataR_loaded and self.comps_loaded
        if data_loaded and self.var_schema_loaded and (len(self.label_choices) > 0):
            self.ready_to_review = True
        else:
            self.ready_to_review = False
    
    def load_dataset(self, data_path, id_vars, side):
        """ Loads two data sets and specifies the id variables in each 
        
        Args:
            data_path: (str or dataframe) path to data set file (either csv or dta) or the dataframe itself
            id_vars: (str or list of str) variables that uniquely define a record in data set
            side: (str) Either 'l' or 'r' indicating which side is being loaded
        """
        # Check if passed object was a str (ie path) or dataframe
        if isinstance(data_path, str):
            path_was_passed = True
            data_ext = os.path.splitext(data_path)[1]
            # Check for file and file type, then load each file into a df
            if      data_ext == ".csv":   data_df = pd.read_csv(data_path)
            elif    data_ext == ".dta":   data_df = pd.read_stata(data_path)
            else:                           
                raise NotImplementedError(f"Filetype of {data_path} must be either .csv or .dta")
        elif isinstance(data_path, pd.DataFrame):
            path_was_passed = False
            data_df = data_path
        else:
            raise NotImplementedError("Must pass either a str path or a dataframe to load_dataset")
        
        # Standardize ids and side and check the value of side
        if isinstance(id_vars, str): id_vars = [id_vars] # Convert to list if a string
        side = side.lower()
        assert side in ['r', 'l'], f"Side argument, {side}, unrecognized. It should be 'r' or 'l'."
        
        # Checking for overlap with current id variables (if they exist)
        if (side == 'r') and (self.dataL_loaded):
            id_overlap = set(self.id_vars_l) & set(id_vars)
        elif (side == 'l') and (self.dataR_loaded):
            id_overlap = set(self.id_vars_r) & set(id_vars)
        else:
            id_overlap = []
        assert len(id_overlap) == 0, "Currently cannot handle overlapping id variables"

        # Validate ids (check they exist and uniquely define a row) and save them
        if side == 'l':
            ids_exist = pd.Series(id_vars).isin(data_df.columns).all()
            assert ids_exist, f"id variables ({id_vars}) not found in the left data set"
            assert data_df.set_index(id_vars).index.is_unique, f"id variables ({id_vars} do not uniquely identify the left data set"
            self.id_vars_l = id_vars
            self.dataL = data_df
            self.dataL_loaded = True
            self.dataL.set_index(self.id_vars_l, inplace=True, drop=False)
            if path_was_passed: self.dataL_file_path = data_path
            else:               self.dataL_file_path = None
        if side == 'r':
            ids_exist = pd.Series(id_vars).isin(data_df.columns).all()
            assert  ids_exist, f"id_vars_r ({id_vars}) not found in the right data set"
            assert data_df.set_index(id_vars).index.is_unique, f"id variables ({id_vars} do not uniquely identify the right data set"
            self.id_vars_r = id_vars
            self.dataR = data_df
            self.dataR_loaded = True
            self.dataR.set_index(self.id_vars_r, inplace=True, drop=False)
            if path_was_passed: self.dataR_file_path = data_path
            else:               self.dataR_file_path = None
        # Flag that var schema and comp_df has to be added again (since data might have changed)
        self.var_schema_loaded = False
        self.comps_loaded = False

    def load_comp_pairs(self, comp_pairs_path):
        """ Loads a file with pairs of records to compare for review
        
        Args:
            comp_pairs_path: (str) path to tabular file containing pairs of id values
                from the dataL and dataR files. Data set should contain all columns 
                found in self.id_vars_l and self.id_vars_r
        """
        # Check that data has already been loaded
        assert self.dataL_loaded, "Load a data file before loading a comparison file"
        assert self.dataR_loaded, "Load a data file before loading a comparison file"

        # Check if passed object was a str (ie path) or dataframe
        if isinstance(comp_pairs_path, str):
            path_was_passed = True
            data_ext = os.path.splitext(comp_pairs_path)[1]
            # Check for file and file type, then load each file into a df
            if      data_ext == ".csv":   comp_df = pd.read_csv(comp_pairs_path)
            elif    data_ext == ".dta":   comp_df = pd.read_stata(comp_pairs_path)
            else:                           
                raise NotImplementedError(f"Filetype of {comp_pairs_path} must be either .csv or .dta")
        elif isinstance(comp_pairs_path, pd.DataFrame):
            path_was_passed = False
            comp_df = comp_pairs_path
        else:
            raise NotImplementedError("Must pass either a str path or a dataframe to load_comp_pairs")
        
        # Check that ids in the file are found in the data files
        l_ids_exist = pd.Series(self.id_vars_l).isin(comp_df.columns).all()
        r_ids_exist = pd.Series(self.id_vars_r).isin(comp_df.columns).all()
        assert l_ids_exist, f"Left data ids ({self.id_vars_l}) not found in passed comparison file."
        assert r_ids_exist, f"Right data ids ({self.id_vars_r}) not found in passed comparison file."

        # Check that id_vars_l and id_vars_r form a unqiue id for records in comparison file
        all_ids = self.id_vars_l + self.id_vars_r
        ids_are_unique = comp_df.set_index(all_ids).index.is_unique
        if not ids_are_unique:
            warnings.warn(f"Id variables ({all_ids}) do not uniquely identify records in comparison file.")
        # comp_df.set_index(all_ids, inplace=True, drop=False)
        comp_df.reset_index(inplace = True, drop = True) # Changes index to 0,1,2,....

        # Add comparison columns if not already there
        if self.REV_LABEL_IND_COL not in comp_df:
            comp_df[self.REV_LABEL_IND_COL] = 0
        for comp_var in [self.REV_LABEL_COL, self.REV_DATE_COL, self.REV_NOTE_COL]:
            if comp_var not in comp_df: comp_df[comp_var] = ""
        
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

        # Save comparison file to class instance and instantiate other relvant variables
        self.comp_df = comp_df
        self.comps_loaded = True
        self.check_ready_to_review()
        self.curr_comp_pair_index = 0
        if path_was_passed: self.comp_pairs_file_path = comp_pairs_path
        else:               self.comp_pairs_file_path = None
    
    def load_review_packet(self, rev_packet):
        """ Loads all the review parameters found in the passed review packet 
        
            Args:
                rev_packet: dict containing review parameters
                    The dict should have the following keys and values:
                    'file_L': str path to the first data file 
                    'file_L_ids': str or list of str indicating the row ids in file_L
                    'file_R': str path to the second data file 
                    'file_R_ids': str or list of str indicating the row ids in file_R
                    'file_comps': str path to the data file containing record pairs
                    'var_group_schema': dict of variable comparisons (see set_var_comp_schema)
                    'label_choices': list of str that make up the label choices
            optional: 'curr_comp_pair_index': int of the current comparison index
        """
        # Validate the structure of the review packet file 
        nec_keys = ['file_L', 'file_L_ids', 'file_R', 'file_R_ids', 'file_comps', 
                        'var_group_schema', 'label_choices']
        for key in nec_keys:
            assert key in rev_packet, f"Review packet must include '{key}' as a key"
        
        # Load the various parts from the review packet file
        self.load_dataset(rev_packet['file_L'], rev_packet['file_L_ids'], 'l')
        self.load_dataset(rev_packet['file_R'], rev_packet['file_R_ids'], 'r')
        self.load_comp_pairs(rev_packet['file_comps'])
        self.set_var_comp_schema(rev_packet['var_group_schema'])
        self.set_label_choices(rev_packet['label_choices'])
        if 'curr_comp_pair_index' in rev_packet:
            rev_ind = rev_packet['curr_comp_pair_index']
            # Set to the current comparison index to this index if it is valid
            if (0 <= rev_ind <= self.comp_df.shape[0]-1):
                self.curr_comp_pair_index = rev_ind
        self.check_ready_to_review()

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
        assert self.dataL_loaded, "Load data files before loading a comparison schema"
        assert self.dataR_loaded, "Load data files before loading a comparison schema"

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
        self.var_schema_loaded = True
        self.check_ready_to_review()

    def set_label_choices(self, label_choices):
        """ Set the label choices (by passing a list of strings) """ 
        # Verify that comp_options is a list of strings
        assert isinstance(label_choices, list), f"The object passed to 'label_choices' is not a list"
        assert len(label_choices)>0, f"The passed list of label choices must be non-empty"
        self.label_choices = [str(opt) for opt in label_choices]

    def set_autosave(self, autosave_bool):
        """ Sets autosaving on or off """
        assert isinstance(autosave_bool, bool), "Argument to set_autosave must be a boolean"
        # Need to have a comp_file path to turn autosave on
        if (autosave_bool == True) and (self.comp_pairs_file_path is None):
            warnings.warn("Cannot turn on autosave when there is no file path for comparison file")
        else:
            self.autosave = autosave_bool

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
        assert self.dataL_loaded, "Load data files before getting a comparison pair"
        assert self.dataR_loaded, "Load data files before getting a comparison pair"
        assert self.comps_loaded, "Load comparison data file before getting a comparison pair"

        # Sets default index if nothing passed
        if comp_ind is None: comp_ind = self.curr_comp_pair_index
        # Verify that index is valid (ie in range of rows of comp_df)
        index_in_range = (0 <= comp_ind <= self.comp_df.shape[0]-1)
        assert index_in_range, f"Comparison index ({comp_ind}) is out of bounds"

        # Check if this comparison pair was identified as having unfound ids
        if self.comp_df.loc[comp_ind, self.REV_LABEL_IND_COL] == -1:
            warnings.warn(f"This record pair (at index {comp_ind}) included ids that were not found in the data sets")
            return None

        # Extract raw data associated with the comparison pair ids
        l_id = tuple(self.comp_df.loc[comp_ind,self.id_vars_l])
        r_id = tuple(self.comp_df.loc[comp_ind,self.id_vars_r])
        l_rec_data = self.dataL.loc[l_id].to_dict()
        r_rec_data = self.dataR.loc[r_id].to_dict()

        # Check requested data format and process accordingly
        if raw_or_grouped == "raw":
            return {'l_rec': l_rec_data, 'r_rec': r_rec_data}
        elif raw_or_grouped == "grouped":
            assert self.var_schema_loaded, "Must set the variable comparison schema before grouping data."
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
            raise NotImplementedError(f"Argument raw_or_grouped ({raw_or_grouped}) must be either 'raw' or 'grouped'")

    def get_label_counts(self):
        """ Returns a summary of the current label counts (as dictionary) """
        # Check that a comparison file has been loaded
        assert self.comps_loaded, "Must have a comparison file loaded before generating a summary"

        # Gather the number of unlabeled
        no_label_num = self.comp_df.shape[0] - self.comp_df[self.REV_LABEL_COL].count()
        no_label_num += (self.comp_df[self.REV_LABEL_COL]=="").sum()

        # Create dictionary of counts by labels found in self.label_choices 
        #       (need to iterate in case a label hasn't been used)
        label_counts = {"Unlabeled": (no_label_num)}
        for label in self.label_choices:
            label_counts[label] = sum(self.comp_df[self.REV_LABEL_COL]==label)

        # Adding in counts if there are labels not in self.label_choices
        labels_found = self.comp_df[self.REV_LABEL_COL].value_counts().to_dict()
        for key in self.label_choices + [""]:
            labels_found.pop(key, None)
        label_counts.update(labels_found)

        # Double check counts add up to number of comparison pairs
        if sum(label_counts.values()) != self.comp_df.shape[0]:
            print("Counts don't match, check the dataframe:")
            print(self.comp_df)
            warnings.warn("Counts don't match, check the above dataframe.")
        
        return label_counts

    def get_var_comp_schema(self):
        if self.var_schema_loaded:
            return self.var_schema
        else:
            return None
    
    def CL_print_comparison_var_group(self, var_group_data, table_width = None, margin = 0):
        """ Prints a single variable group of a comparison to the command line """
        # If no table width is passed, use the default line width
        if table_width is None: table_width = self.COMP_DEFAULT_LINE_WIDTH
        # Calculate the column widths and number or rows needed
        l_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[0])-1
        m_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[1])
        r_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[2])-1
        row_num = max(len(var_group_data['lvals']), len(var_group_data['rvals']))

        # Print each line (or skip if nothing to print for that column)
        for i in range(row_num):
            line_text = " "*margin+"|"
            # Append left variable value right aligned (if it exists)
            if i < len(var_group_data['lvals']):
                line_text += str(var_group_data['lvals'][i]).rjust(l_col_width)
            else: line_text += " "*l_col_width

            # Append variable group name (for first row) and spaces for others
            if i == 0 : # Print group name on first line
                line_text += str(var_group_data['name']).center(m_col_width)
            else: line_text += " "*m_col_width

            # Append right variable value left aligned (if it exists)
            if i < len(var_group_data['rvals']):
                line_text += str(var_group_data['rvals'][i]).ljust(r_col_width)

            # Add finish to table row
            line_text += " "*(margin+table_width-len(line_text)-1) + "|"

            # Print compiled line of text
            print(line_text)

    def CL_print_comparison_full(self, comp_ind, table_width = None, margin = 0):
        """ Prints out the full comparison (based on var_schema) between the
            records identified in the passed index (of comp_df)"""
        assert self.ready_to_review, "Must load all data, comparison files, and var schema before reviewing."
        # First get the associated grouped data of the pair (and exit if not found)
        val_groups = self.get_comp_pair("grouped", comp_ind)
        if val_groups is None:
            print("**** At least one id was not found in the data sets of this pair of records ****")
            return
        # Set line width if not passed
        if table_width is None: table_width = self.COMP_DEFAULT_LINE_WIDTH

        # Print headings (after calculating column widths)
        l_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[0])-1
        m_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[1])
        r_col_width = int(table_width*self.COMP_PRINT_COL_WEIGHT[2])-1
        heading = " "*margin+"|"+"Left Data Record".rjust(l_col_width)
        heading += "Vars".center(m_col_width)
        heading += "Right Data Record".ljust(r_col_width)
        heading += " "*(margin+table_width-len(heading)-1) + "|"
        print(heading)

        # Print each group of the variable groups found (with lines in between)
        for val_group in val_groups:
            print(" "*margin+"+"+"-"*(table_width-2)+"+")
            self.CL_print_comparison_var_group(val_group, table_width = table_width, 
                                                        margin = margin)
        print(" "*margin+"+"+"-"*(table_width-2)+"+")

    def CL_print_input_options(self, sel_label = None, line_width = None):
        """ Prints option choices (label options and addtl options) to the command line 
        
            Args:
                sel_label: int (0 for no label, and 1,2,3... for indices of self.label_choices
                line_width: int, optional
                    Line width (in number of characters) for printing comparisons
        """
        # Sets default line width
        if line_width is None: line_width = self.COMP_DEFAULT_LINE_WIDTH

        # Print heading for option choices 
        print("Label Options (<> = current label):")

        # Assemble and print input options (temporarily adding "No Label")
        options_line = ""
        temp_label_choices = ["No Label"] + self.label_choices
        for i in range(len(temp_label_choices)):
            # Add label option (and selection indication)
            if i == sel_label:
                label_option = f"<{i}> {temp_label_choices[i]} "
            else:
                label_option = f"({i}) {temp_label_choices[i]} "
            # Go to next line if too long
            if (len(options_line)+len(label_option)) > line_width:
                print(options_line)
                options_line = ""
            options_line += label_option
        print(options_line)

        # Print additional options
        print("Other Options:")
        options_line = ""
        for addtl_option in self.ADDTL_OPTION_TEXTS:
            # Go to next line if too long
            if (len(options_line)+len(addtl_option)) > line_width:
                print(options_line)
                options_line = ""
            options_line += addtl_option + ' '
        print(options_line)

    def CL_print_label_summary(self, line_width = None, detailed = False):
        """ Prints a summary of the current label to the command line 
        
            Args:
                line_width: int, optional
                    Line width (in number of characters) for printing comparisons
                detailed: bool, optional
                    Default is to print coutns of each label, detailed includes every specific label
        """
        # Sets default line width
        if line_width is None: line_width = self.COMP_DEFAULT_LINE_WIDTH

        # Gather the label counts
        label_counts = self.get_label_counts()

        # Calculate max label length and count length (and margin so table is centered)
        max_label_len = max([len(str(lab)) for lab in label_counts.keys()])
        max_count_len = max([len(str(lab)) for lab in label_counts.values()])
        margin = line_width//2 - (max_label_len+max_count_len+7)//2
        
        if detailed:
            # TODO: Iterate through each record pair and print current label
            raise NotImplementedError("Have not yet implemented the 'detailed' option for label summaries.")
        else:
            print("")
            print(" "*margin + "+" + "-"*(max_label_len+max_count_len+5) + "+")
            print(" "*margin + "+" + "Label Summary".center(max_label_len+max_count_len+5) + "+")
            print(" "*margin + "+" + "-"*(max_label_len+max_count_len+5) + "+")
            for label in label_counts:
                line_text = " "*margin
                line_text += f"| {label.rjust(max_label_len)} | "
                line_text += f"{str(label_counts[label]).rjust(max_count_len)} |"
                print(line_text)
            print(" "*margin + "+" + "-"*(max_label_len+max_count_len+5) + "+")

    def get_label_choices(self):
        return self.label_choices

    def CL_comparison_query(self, comp_ind = None, min_table_width = None,
                                valid_choices = None):
        """ Prints a full comparison, to the command line, of the passed comparison index and 
            gathers (validated) option input and returns the result 
        
            Args:
                comp_ind: int, optional
                    Index (in comp_df) of the comparison pair to be review. If nothing 
                    is passed it assumes the user refers to curr_comp_pair_index
                min_table_width: int, optional
                    Minimum table width (in number of characters) for printing comparisons
                valid_choices: None or list of str
                    Query will repeat until user enters an option in valid_choices
                    Value of None means all inputs are valid
            
            Returns: string or None
                If a label option is chosen it will return the associated number (which is +1 of
                the associated index in self.label_choices) or if another option is chosen it
                returns the letter associated with option in ADDTL_OPTION_TEXTS

        """
        # Verifies that datasets and comparison files and choices have all been set
        if not self.ready_to_review:
            warnings.warn("Cannot review a comparison when datasets, comparison pairs, var schema, and/or choices have not been set")
            return None

        # Sets default comparison index (and table_width) and checks if valid 
        if comp_ind is None: comp_ind = self.curr_comp_pair_index
        index_in_range = (0 <= comp_ind <= self.comp_df.shape[0]-1)
        assert index_in_range, f"Comparison index ({comp_ind}) is out of bounds"

        # Calculating the table width from the column data
        table_data = self.get_comp_pair("raw", comp_ind = comp_ind)
        max_l_val = max([len(str(v)) for v in table_data['l_rec'].values()])
        max_r_val = max([len(str(v)) for v in table_data['r_rec'].values()])
        table_data = self.get_comp_pair("grouped", comp_ind = comp_ind)
        max_m_val = max([len(g['name']) for g in table_data])
        table_width = 2*max(max_l_val, max_r_val) + max_m_val + 8

        # Enforcing minimum table width and calulating margin to center table
        if min_table_width is None: min_table_width = 0
        table_width = max(min_table_width, table_width)
        margin = (self.COMP_DEFAULT_LINE_WIDTH-table_width)//2

        # Prints a heading for comparison
        head_text = f"Record Pair {self.curr_comp_pair_index+1}/{self.comp_df.shape[0]}"
        print(" "*margin+"+"+"-"*(table_width-2)+"+")
        print(" "*margin+"|"+head_text.center(table_width-2)+"|")
        print(" "*margin+"+"+"-"*(table_width-2)+"+")

        # Prints the comparison of this pair of records
        self.CL_print_comparison_full(comp_ind, table_width = table_width, margin = margin)
        print("")

        # Print a note if there is anything there
        # TODO: Make note last row of comparison table (and so it wraps around if necessary)
        note = self.comp_df.loc[comp_ind, self.REV_NOTE_COL]
        if (isinstance(note,str) and note!= "") or (isinstance(note,float) and not isnan(note)):
            print(f"Note: {self.comp_df.loc[comp_ind, self.REV_NOTE_COL]}")

        # Print the option choices (and highlights the current label if one is there)
        curr_label = self.comp_df.loc[comp_ind, self.REV_LABEL_COL]
        if curr_label in self.label_choices: curr_label = self.label_choices.index(curr_label)+1
        else:                                curr_label = 0
        self.CL_print_input_options(sel_label = curr_label)

        # Gather option choice from user until they pass a valid one
        choice = input("Enter Choice: ").lower()
        while (valid_choices is not None) and (choice not in valid_choices):
            print("*** Invalid Choice ***")
            choice = input("Enter Choice: ").lower()
            
        return choice

    def CL_process_choice(self, comp_choice, comp_pairs_path = None):
        """ Take appropriate action associated with passed choice
        
            Args:
                comp_choice: str
                    The tag (ie single letter) associated with a label or other option
                comp_pairs_path: string, optional
                    Filename (and path) that the current version of the comp_df will be saved
                    to. If nothing is passed it uses the same path as original comparison file

        """
        # Create list of tags associated with label choices and valid comp pair indices
        label_choice_tags = list(map(str,range(1,len(self.label_choices)+1)))
        valid_comp_indices = list(map(str,range(1,self.comp_df.shape[0]+1)))

        # Take action according to choice passed
        if comp_choice == '0':  # No label chosen
            self.save_label_or_note("", label_or_note = 'label', comp_ind = self.curr_comp_pair_index, 
                                comp_pairs_path = comp_pairs_path)
        elif comp_choice in label_choice_tags: # Label chosen
            self.save_label_or_note(self.label_choices[int(comp_choice)-1], 
                            label_or_note = 'label', 
                            comp_ind = self.curr_comp_pair_index,
                            comp_pairs_path = comp_pairs_path)
        elif comp_choice == 'p': # Previous comparison
            # Check if this is first comparison pair or not (if not decrease by one)
            if self.curr_comp_pair_index == 0:
                print("** This was first comparison pair, can't go to previous **")
            else:
                self.curr_comp_pair_index -= 1
        elif comp_choice == 'n': # Next comparison
            # Check if this is last comparison pair or not (if not advance by one)
            if self.curr_comp_pair_index == self.comp_df.shape[0]-1:
                print("** This was final comparison pair, can't go to next **")
            else:
                self.curr_comp_pair_index += 1
        elif comp_choice == 'g': # Go to another comparison
            # Get index entry and check if valid (and go there if so)
            go_to_index = input(f"Enter Comp. Number (1-{self.comp_df.shape[0]}): ")
            while go_to_index not in valid_comp_indices:
                print(f"** This index is not valid, must be integer between 1 and {self.comp_df.shape[0]} **")
                go_to_index = input(f"Enter Comp. Number (1-{self.comp_df.shape[0]}): ")
            self.curr_comp_pair_index = int(go_to_index)-1
        elif comp_choice == 'a': # Add a note to this comparison
            note_text = input("Enter note (replaces current note): ")
            self.save_label_or_note(note_text, label_or_note = 'note', 
                            comp_ind = self.curr_comp_pair_index,
                            comp_pairs_path = comp_pairs_path)
        elif comp_choice == 's': # Summary (print labeling summary)
            self.CL_print_label_summary(line_width = self.COMP_DEFAULT_LINE_WIDTH)
        elif comp_choice == 'e': # Exit (do nothing here)
            return
        else:
            raise NotImplementedError("Impossible! An invalid comp_choice ({comp_choice}) got through!?")

    def CL_review_comparisons(self, line_width = None, comp_pairs_path = None):
        """ Start the command line reviewer using self.curr_comp_pair_index of self.comp_df
        
            Args:
                line_width: int, optional
                    Line width (in number of characters) for printing comparisons
                comp_pairs_path: string, optional
                    Filename (and path) that the current version of the comp_df will be saved
                    to. If nothing is passed it uses the same path as original comparison file

        """
        # Verifies that datasets and comparison files and choices have all been set
        if not self.ready_to_review:
            warnings.warn("Cannot review a comparison when datasets, comparison pairs, var schema, and/or choices have not been set")
            return None

        # Sets default line_width
        if line_width is None: line_width = self.COMP_DEFAULT_LINE_WIDTH

        # Creating list of acceptable choice answers
        label_choice_tags = list(map(str,range(1,len(self.label_choices)+1)))
        valid_choices = ['0'] + label_choice_tags + self.ADDTL_OPTION_TAGS

        # Print comparison, gather input, and process the choice
        comp_choice = self.CL_comparison_query(self.curr_comp_pair_index, 
                                                min_table_width = 60,
                                                valid_choices = valid_choices)
        self.CL_process_choice(comp_choice, comp_pairs_path = comp_pairs_path)
        print(" "*line_width+"\n")
        
        # Continue comparing record pairs and processing options until user exits
        while comp_choice != 'e':
            comp_choice = self.CL_comparison_query(self.curr_comp_pair_index, 
                                                    min_table_width = 60,
                                                    valid_choices = valid_choices)
            self.CL_process_choice(comp_choice, comp_pairs_path = comp_pairs_path)
            print(" "*line_width+"\n")
            
    def save_comp_df(self, comp_pairs_path = None):
        """ Saves the current value of the comparison dataframe """
        # Sets default file path if nothing passed
        if comp_pairs_path is None: comp_pairs_path = self.comp_pairs_file_path

        # Check file format and save file accordingly
        data_ext = os.path.splitext(comp_pairs_path)[1]
        if      data_ext == ".csv":   self.comp_df.to_csv(comp_pairs_path, index = False)
        elif    data_ext == ".dta":   self.comp_df.to_stata(comp_pairs_path, write_index = False)
        else:   raise NotImplementedError(f"Filetype of {data_ext} must be either csv or dta")

    def save_label_or_note(self, text, label_or_note = 'label', comp_ind = None, 
                            comp_pairs_path = None):
        """ Validates and saves the label choice or note to the indicated comparison pair. 
        
            Args:
                label: str
                    The label that will be saved for this record pair (should be among label_choices)
                label_or_note: str (either 'label' or 'note')
                    Indicates whether to save 'text' to the label or note
                comp_ind: int, optional
                    Index (in comp_df) of the comparison pair the label is being applied to.
                    If nothing is passed it assumes the user refers to curr_comp_pair_index
                comp_pairs_path: string, optional
                    Filename (and path) that the current version of the comp_df will be saved
                    to. If nothing is passed it uses the same path as original comparison file
        """
        # Verifies that datasets and comparison files and choices have all been set
        if not self.ready_to_review:
            warnings.warn("Cannot save a label when datasets, comparison pairs, var schema, and/or choices have not been set")
            return

        # Sets default comparison index
        if comp_ind is None: comp_ind = self.curr_comp_pair_index

        # Check that comp_ind is valid
        index_in_range = (0 <= comp_ind <= self.comp_df.shape[0]-1)
        assert index_in_range, f"Comparison index ({comp_ind}) is out of bounds"

        # Save label or note to the comp_df table
        if label_or_note == 'label':
            # Check that label is valid and comp_ind is valid
            assert text in [""]+self.label_choices, f"Label passed ({text}) is not among valid choices"
            # Update comparison df with the label and the indicator column
            self.comp_df.loc[comp_ind,self.REV_LABEL_COL] = text
            self.comp_df.loc[comp_ind,self.REV_LABEL_IND_COL] = 1 if (text != "") else 0
        elif label_or_note == 'note':
            # Update comparison df with the note
            self.comp_df.loc[comp_ind,self.REV_NOTE_COL] = text
        else:
            raise NotImplementedError(f"Unrecognized value of 'label_or_note' ({label_or_note}) in function.")

        # Update the comparison df changed timestamp variable
        self.comp_df.loc[comp_ind,self.REV_DATE_COL] = datetime.datetime.now()

        # Save the comparison dataframe (if not delayed)
        if (self.autosave):
            self.save_comp_df(comp_pairs_path = comp_pairs_path)

    def get_review_packet(self):
        """ Creates and returns a review packet containing current parameters """
        # Check that all pieces are present (should be review ready)
        if not self.ready_to_review:
            warnings.warn("Cannot save a review packet when datasets, comparison pairs, var schema, and/or choices have not been set")
            return None
        
        # Check if any data files were not loaded by paths (cannot save review packet in these cases)
        if (self.dataL_file_path is None) or (self.dataR_file_path is None) or (self.comp_pairs_file_path is None):
            warnings.warn("One of the data files was loaded without a path, so a review packet cannot be saved.")
            return None
        
        # Assemble the review packet
        rev_packet = {'file_L': self.dataL_file_path,
                        'file_L_ids': self.id_vars_l,
                        'file_R': self.dataR_file_path,
                        'file_R_ids': self.id_vars_r,
                        'file_comps': self.comp_pairs_file_path,
                        'var_group_schema': self.var_schema,
                        'label_choices': self.label_choices,
                        'curr_comp_pair_index': self.curr_comp_pair_index}
        
        return rev_packet

    def save_review_packet(self, rev_packet_path):
        """ Saves current parameters to a review packet in the designated file path """
        # Get the review packet
        rev_packet_dict = self.get_review_packet()

        if rev_packet_dict is None:
            return
        else:
            # Save the review packet
            with open(rev_packet_path, 'w') as fp:
                json.dump(rev_packet_dict, fp, indent = 4)

def main():
    # Check if a file was passed
    if len(sys.argv) > 1:
        # Open the configuration file with the review parameters
        rev_packet_path = sys.argv[1]
        
        # Load the review parameters and start reviewing (assuming they were passed)
        rev = rlr(rev_packet_path)
        rev.CL_review_comparisons()

if __name__ == "__main__":
    main()