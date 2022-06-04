import streamlit as st

###########################################################################
#### Function Definitions #################################################
###########################################################################

def add_var_group():
    # Add empty var group to end of list
    st.session_state['var_group_schema'].append({'name': "", 'lvars': [], 'rvars': []})

def del_var_group(vargp_index):
    # Delete var group at the passed index
    del st.session_state['var_group_schema'][vargp_index]

###########################################################################
#### App - Var. Group Schema ##############################################
###########################################################################

# Heading and input description
st.title("Variable Comparison Groups")
st.write("Use the below inputs to designate which variables from each "+
            "data set should be compared to one another. Add or delete "+
            "comparison groups as necessary.")

# Initialize the group schema
if 'var_group_schema' not in st.session_state:
    st.session_state['var_group_schema'] = []

# Some temp data fields
l_vars = [f"var_{i}" for i in range(1,6)]
r_vars = [f"field_{i}" for i in range(1,7)]

# Heading and input description
st.title("Variable Comparison Groups")
st.write("Use the below inputs to designate which variables from each "+
            "data set should be compared to one another. Add or delete "+
            "comparison groups as necessary.")

# Iterate through each var group and print out related inputs
for i in range(len(st.session_state['var_group_schema'])):
    old_var_group = st.session_state['var_group_schema'][i].copy()
    col_1, col_2 = st.columns([1,3])
    var_name = col_1.text_input("Var. Group Name:", value = old_var_group['name'], key = f"vargp_{i}_name")
    vars_l = col_2.multiselect("Pick Vars from Left Data Set:", l_vars,
                                default = old_var_group['lvars'], key = f"vargp_{i}_lvars")
    vars_r = col_2.multiselect("Pick Vars from Right Data Set:", r_vars, 
                                default = old_var_group['rvars'], key = f"vargp_{i}_rvars")
    del_button = col_1.button("Delete Group", key = f"vargp_{i}_del",
                                on_click = del_var_group, args=(i, ))
    st.session_state['var_group_schema'][i] = {'name': var_name, 'lvars': vars_l, 'rvars': vars_r}
add_button = st.button("Add Group", on_click = add_var_group)

st.write(st.session_state['var_group_schema'])