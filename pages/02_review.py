import streamlit as st
import pandas as pd

###########################################################################
#### Function Definitions #################################################
###########################################################################

def remove_comp_file():
    """ Removes the comparison file """
    st.session_state['rlr'].comps_loaded = False
    st.session_state['rlr'].comp_df = None
    st.session_state['rlr'].ready_to_review = False
    
###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# Initializing rlr backend
if 'rlr' not in st.session_state:
    st.session_state['rlr'] = rlr()

with st.sidebar:
    st.header("Load Review File")
    # Checking if it has already been loaded
    if st.session_state['rlr'].comps_loaded:
        st.write("Comparison File Loaded")
        st.button("Load a different comparison file", key = "reload", on_click = remove_comp_file)
    else:
        # Ask for file upload from user
        review_file = st.file_uploader("Upload file of linked pairs for review", 
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if review_file is None:
                st.write("")
        else:
            # Load the passed file of comparison linkages
            df_review = pd.read_csv(review_file)
            st.session_state['rlr'].load_comp_pairs(df_review)
            if st.session_state['rlr'].comps_loaded:
                msg = "Successfully loaded a file for review."
                msg_text = f'<p style="color:Green;">{msg}</p>'
                st.markdown(msg_text, unsafe_allow_html=True)

    # Display information if a file has been loaded
    if (st.session_state['rlr'].comps_loaded) or (review_file is not None):
        # Gather label counts and display a summary
        st.subheader("Label Summary")
        l_counts = st.session_state['rlr'].get_label_counts()
        l_counts_df = pd.DataFrame.from_dict(l_counts, orient = 'index', columns = ['Count'])
        l_counts_df.index.name = "Label"
        l_counts_df['%'] = l_counts_df['Count']/l_counts_df['Count'].sum()*100
        l_counts_df['%'] = l_counts_df['%'].round(1)
        st.dataframe(l_counts_df)

###########################################################################
#### App - Review #########################################################
###########################################################################

# Heading and input description
st.title("Record Linkage Review")

# Check if RLR is ready to review links
if (st.session_state['rlr'].ready_to_review):
    st.write("Review ready. TBD.")
else:
    st.write("Not all pieces necessary for review have been initialized:")
    # Check which parts are not yet initialized
    if not st.session_state['rlr'].dataL_loaded:
        st.write("  - Need to load a left data set (refer to data input page)")
    if not st.session_state['rlr'].dataR_loaded:
        st.write("  - Need to load a right data set (refer to data input page)")
    if not st.session_state['rlr'].var_schema_loaded:
        st.write("  - Need to define a variable comparison schema (refer to data input page)")
    if not st.session_state['rlr'].comps_loaded:
        st.write("  - Need to load a file of linkages for review (refer to sidebar)")
    if len(st.session_state['rlr'].label_choices) == 0:
        st.write("  - Need to define the label choices (refer to sidebar)")