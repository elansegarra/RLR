import streamlit as st
import pandas as pd
import json, io, os

st.set_page_config(page_title="RLR: Data Input", page_icon="📈")

###########################################################################
#### Function Definitions #################################################
###########################################################################

def remove_data_file(side):
    """ Removes the data file from the deisgnated side """
    if side == 'l':
        st.session_state['rlr'].dataL_loaded = False
        st.session_state['rlr'].dataL = None
        st.session_state['rlr'].ready_to_review = False
    elif side == 'r':
        st.session_state['rlr'].dataR_loaded = False
        st.session_state['rlr'].dataR = None
        st.session_state['rlr'].ready_to_review = False
    else:
        raise NotImplementedError(f"Unrecognized side, {side}, must by 'l' or 'r'.")

def add_var_group():
    # Add empty var group to end of list of the variable group schema
    var_comp_schema = [vgroup.copy() for vgroup in st.session_state['rlr'].get_var_comp_schema()]
    var_comp_schema.append({'name': "", 'lvars': [], 'rvars': []})
    st.session_state['rlr'].set_var_comp_schema(var_comp_schema)

def del_var_group(vargp_index):
    # Delete var group at the passed index in the list of variable group schemas
    var_comp_schema = st.session_state['rlr'].get_var_comp_schema()
    del var_comp_schema[vargp_index]
    st.session_state['rlr'].set_var_comp_schema(var_comp_schema)

def remove_comp_file():
    """ Removes the comparison file """
    st.session_state['rlr'].comps_loaded = False
    st.session_state['rlr'].comp_df = None
    st.session_state['rlr'].ready_to_review = False

###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# initialize session state variable (for tracking when new rev packets are loaded)
if 'last_rev_packet' not in st.session_state:
    st.session_state['last_rev_packet'] = None

with st.sidebar:
    input_mech_options = ['Drag and Drop Files', 'Local Data Folder']
    input_mech = st.radio("Input Mechanism", input_mech_options)

    # Display upload for entire review packet
    rev_packet = st.file_uploader("Upload Review Packet", key = "rev_packet_file",
                                    accept_multiple_files=False, type = ['json'])
    if rev_packet is None:
        st.write("")
    else:
        # Check if this is a new packet (or one already loaded)
        new_packet_loaded = (st.session_state['last_rev_packet'] != rev_packet)
        if new_packet_loaded:
            # Open the review packet file and load the dictionary into RLR
            rev_packet_dict = json.load(rev_packet)
            st.session_state['rlr'].load_review_packet(rev_packet_dict)
            st.session_state['last_rev_packet'] = rev_packet
            # st.write(rev_packet_dict)
    
    # Download buttons to save a review packet
    if (st.session_state['rlr'].ready_to_review):
        rev_dict = st.session_state['rlr'].get_review_packet()
        if rev_dict is not None:
            st.write("Download Review Packet")
            with io.BytesIO() as buffer:
                buffer.write(json.dumps(rev_dict, indent = 4).encode())
                st.download_button("Download json", buffer, 
                                    file_name = "review_packet.json")
                st.write("")

###########################################################################
#### App - Inputting Data Files ###########################################
###########################################################################

st.header("Loading Left and Right Data Sets")
with st.expander("Left Data Set:", expanded = True):
    # Checking if left data has already been loaded
    if st.session_state['rlr'].dataL_loaded:
        left_name = " " if (st.session_state['rlr'].dataL_name is None) else f" ({st.session_state['rlr'].dataL_name}) "
        st.write(f"Left Data Set{left_name}Already Loaded")
        st.dataframe(st.session_state['rlr'].dataL.head())
        st.write(f"IDs: {st.session_state['rlr'].id_vars_l}")
        st.button("Load a different data set", key = "reload_l", on_click = remove_data_file, args=('l', ))
    else:
        # Input the first data file
        data_file_L = st.file_uploader("Upload file", key = "L_file",
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if data_file_L is None:
            st.write("")
        else:
            # Open the data file (after determining type)
            data_ext = os.path.splitext(data_file_L.name)[1]
            if      data_ext == ".csv":   dfL = pd.read_csv(data_file_L)
            elif    data_ext == ".dta":   dfL = pd.read_stata(data_file_L)
            else:                           
                raise NotImplementedError(f"Filetype of {data_file_L.name} must be either .csv or .dta")
            # Print the first few rows
            st.dataframe(dfL.head())

            # Let the user determine which fields make up the row id
            dfL_id_vars = st.multiselect("Choose which fields uniquely identify rows:", dfL.columns, key = "L_file_ids")
            
            # Verify that passed variables uniquely identify a row
            if len(dfL_id_vars) == 0:
                msg = "** Please choose which columns uniquely identify each row. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_L_loaded'] = False
            elif dfL.set_index(dfL_id_vars).index.is_unique:
                msg = "Variables chosen are valid identifiers. Loading of the left data set is complete."
                msg_text = f'<p style="color:Green;">{msg}</p>'
                st.session_state['data_L_loaded'] = True
                st.session_state['rlr'].load_dataset(dfL, dfL_id_vars, 'l')
            else:
                msg = "** Variables chosen do not uniquely identify rows. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_L_loaded'] = False
            st.markdown(msg_text, unsafe_allow_html=True)


with st.expander("Right Data Set:", expanded = True):
    # Checking if left data has already been loaded
    if st.session_state['rlr'].dataR_loaded:
        right_name = " " if (st.session_state['rlr'].dataR_name is None) else f" ({st.session_state['rlr'].dataR_name}) "
        st.write(f"Right Data Set{right_name}Already Loaded")
        st.dataframe(st.session_state['rlr'].dataR.head())
        st.write(f"IDs: {st.session_state['rlr'].id_vars_r}")
        st.button("Load a different data set", key = "reload_r", on_click = remove_data_file, args=('r', ))
    else:
        # Input the second data file
        data_file_R = st.file_uploader("Upload file", key = "R_file",
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if data_file_R is None:
            st.write("")
        else:
            # Open the data file (after determining type)
            data_ext = os.path.splitext(data_file_R.name)[1]
            if      data_ext == ".csv":   dfR = pd.read_csv(data_file_R)
            elif    data_ext == ".dta":   dfR = pd.read_stata(data_file_R)
            else:                           
                raise NotImplementedError(f"Filetype of {data_file_R.name} must be either .csv or .dta")
            # Print the first few rows
            st.dataframe(dfR.head())

            # Let the user determine which fields make up the row id
            dfR_id_vars = st.multiselect("Choose which fields uniquely identify rows:", dfR.columns, key = "R_file_ids")
            
            # Verify that passed variables uniquely identify a row
            if len(dfR_id_vars) == 0:
                msg = "** Please choose which columns uniquely identify each row. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_R_loaded'] = False
            elif dfR.set_index(dfR_id_vars).index.is_unique:
                msg = "Variables chosen are valid identifiers. Loading of the right data set is complete."
                msg_text = f'<p style="color:Green;">{msg}</p>'
                st.session_state['data_R_loaded'] = True
                st.session_state['rlr'].load_dataset(dfR, dfR_id_vars, 'r')
            else:
                msg = "** Variables chosen do not uniquely identify rows. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_R_loaded'] = False
            st.markdown(msg_text, unsafe_allow_html=True)

###########################################################################
#### App - Setting Up Variable Comparison Schema ##########################
###########################################################################

st.header("Defining Variable Comparison Groups")
# Checking if both data sets have been properly loaded
if (st.session_state['rlr'].dataL_loaded) and (st.session_state['rlr'].dataR_loaded):
    # Input description
    st.write("Use the below inputs to designate which variables from each "+
                "data set should be compared to one another. For example, comparing "+
                "variable 'name' in the left dataset with the variables 'first_name' "+
                "and 'last_name' in the right data set. Add or delete "+
                "comparison groups as necessary.")

    # Gathering variables from loaded dataset
    l_vars = st.session_state['rlr'].dataL.columns
    r_vars = st.session_state['rlr'].dataR.columns

    # Gather var schema from rlr instance if loaded
    if (st.session_state['rlr'].var_schema_loaded):
        curr_var_comp_schema = [vgroup.copy() for vgroup in st.session_state['rlr'].get_var_comp_schema()]
    else:
        curr_var_comp_schema = [{'name': "", 'lvars': [], 'rvars': []}]

    # Gather names of data sets if they have been set
    left_name = "Left Data Set" if (st.session_state['rlr'].dataL_name is None) else st.session_state['rlr'].dataL_name
    right_name = "Right Data Set" if (st.session_state['rlr'].dataR_name is None) else st.session_state['rlr'].dataR_name

    # Iterate through each var group and print out related inputs
    new_var_comp_schema = []
    for i in range(len(curr_var_comp_schema)):
        var_group = curr_var_comp_schema[i].copy()
        with st.expander(f"Var. Group: {var_group['name']}", expanded = True):
            col_1, col_2 = st.columns([1,3])
            var_name = col_1.text_input("Var. Group Name:", value = var_group['name'], key = f"vargp_{i}_name")
            vars_l = col_2.multiselect(f"Pick Vars from {left_name}:", l_vars,
                                        default = var_group['lvars'], key = f"vargp_{i}_lvars")
            vars_r = col_2.multiselect(f"Pick Vars from {right_name}:", r_vars, 
                                        default = var_group['rvars'], key = f"vargp_{i}_rvars")
            del_button = col_1.button("Delete Group", key = f"vargp_{i}_del",
                                        on_click = del_var_group, args=(i, ))
            new_var_comp_schema.append({'name': var_name, 'lvars': vars_l, 'rvars': vars_r})
    st.session_state['rlr'].set_var_comp_schema(new_var_comp_schema)
    add_button = st.button("Add Group", on_click = add_var_group)

    # st.write(st.session_state['rlr'].get_var_comp_schema())
else:
    st.write("User must load two data sets with identifying variables before defining the comparison schema.")

###########################################################################
#### App - Loading Comparison File ########################################
###########################################################################

st.header("Loading Comparison File")
# Checking if both data sets have been properly loaded
if (st.session_state['rlr'].dataL_loaded) and (st.session_state['rlr'].dataR_loaded):
    st.write(f"""Load a comparison file which contains the pairs of records which the user would like
                to review and label. Every row of this file represents a pair of records to be reviewed.
                Therefore this file should have columns that identify a record in the left data set
                (i.e. {", ".join(st.session_state['rlr'].id_vars_l)}) and columns that identify a record 
                in the right data set (i.e. {", ".join(st.session_state['rlr'].id_vars_r)}). """)
    # Checking if it has already been loaded
    if st.session_state['rlr'].comps_loaded:
        if st.session_state['rlr'].comp_pairs_file_path is not None:
            filename = st.session_state['rlr'].comp_pairs_file_path
        else: filename = "File name unknown"
        st.write(f"Comparison File Loaded: {filename}")
        st.button("Load a different comparison file", key = "reload", on_click = remove_comp_file)
    else:
        # Ask for file upload from user
        review_file = st.file_uploader("Upload file of linked pairs for review", 
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if review_file is None:
                st.write("")
        else:
            # Open the data linkage file (after determining type)
            data_ext = os.path.splitext(review_file.name)[1]
            if      data_ext == ".csv":   df_review = pd.read_csv(review_file)
            elif    data_ext == ".dta":   df_review = pd.read_stata(review_file)
            else:                           
                raise NotImplementedError(f"Filetype of {review_file.name} must be either .csv or .dta")

            # Load the passed file of comparison linkages
            st.session_state['rlr'].load_comp_pairs(df_review)
            if st.session_state['rlr'].comps_loaded:
                msg = "Successfully loaded a file for review."
                msg_text = f'<p style="color:Green;">{msg}</p>'
                st.markdown(msg_text, unsafe_allow_html=True)
                st.session_state['review_file_name'] = review_file.name

    # Display information if a file has been loaded
    if (st.session_state['rlr'].comps_loaded) or (review_file is not None):
        # Gather label counts and display a summary
        st.subheader("Comparison File Label Summary")
        l_counts = st.session_state['rlr'].get_label_counts()
        l_counts_df = pd.DataFrame.from_dict(l_counts, orient = 'index', columns = ['Count'])
        l_counts_df.index.name = "Label"
        l_counts_df['%'] = l_counts_df['Count']/l_counts_df['Count'].sum()*100
        l_counts_df['%'] = l_counts_df['%'].round(1)
        st.dataframe(l_counts_df)
else:
    st.write("User must load two data sets with identifying variables before loading a comparison file.")