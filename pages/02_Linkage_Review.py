from fileinput import filename
import streamlit as st
import pandas as pd
from backend.rlr import rlr

st.set_page_config(page_title="RLR: Linkage Review", page_icon="📈")

###########################################################################
#### Function Definitions #################################################
###########################################################################

def remove_comp_file():
    """ Removes the comparison file """
    st.session_state['rlr'].comps_loaded = False
    st.session_state['rlr'].comp_df = None
    st.session_state['rlr'].ready_to_review = False

def tformat(text, align='C', el='p'):
    align_dict = {'L':'left', 'C':'center','R':'right'}
    return(f"<{el} style='text-align: {align_dict[align]};'>{text}</{el}>")

def next_pair():
    """ Move to next comparison if not at end """
    if st.session_state['rlr'].curr_comp_pair_index < st.session_state['rlr'].comp_df.shape[0]-1:
        st.session_state['rlr'].curr_comp_pair_index += 1

def prev_pair():
    """ Move to previous comparison if not at beginning """
    if st.session_state['rlr'].curr_comp_pair_index > 0:
        st.session_state['rlr'].curr_comp_pair_index -= 1

###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# Initializing rlr backend if not done already
if 'rlr' not in st.session_state:
    st.session_state['rlr'] = rlr()
if 'review_file_name' not in st.session_state:
    st.session_state['review_file_name'] = "labeled_data.csv"

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
                st.session_state['review_file_name'] = review_file.name

    # Display information if a file has been loaded
    if (st.session_state['rlr'].comps_loaded) or (review_file is not None):
        # Gather label counts and display a summary
        st.subheader("File Label Summary")
        l_counts = st.session_state['rlr'].get_label_counts()
        l_counts_df = pd.DataFrame.from_dict(l_counts, orient = 'index', columns = ['Count'])
        l_counts_df.index.name = "Label"
        l_counts_df['%'] = l_counts_df['Count']/l_counts_df['Count'].sum()*100
        l_counts_df['%'] = l_counts_df['%'].round(1)
        st.dataframe(l_counts_df)
    
    # Display and allow editing of current label choices
    st.header("Label Choices")
    new_label_choices = []
    curr_labels = "\n".join(st.session_state['rlr'].label_choices)
    new_labels = st.text_area("Enter choices (each line is a separate label)", value = curr_labels)
    st.session_state['rlr'].set_label_choices(new_labels.split('\n'))
    # st.session_state['rlr'].label_choices = new_labels.split('\n')
    st.write("")

    # Download buttons to save linkage review results
    if (st.session_state['rlr'].comps_loaded):
        st.header("Download Labeled Data")
        comp_data = st.session_state['rlr'].comp_df.to_csv().encode('utf-8')
        col1, col2 = st.columns(2)
        col1.download_button("Download csv", comp_data, file_name = st.session_state['review_file_name'],
                            mime = 'text/csv')
        col2.download_button("Download dta", comp_data, file_name = st.session_state['review_file_name'],
                            mime = 'text/csv')
        st.write("")

###########################################################################
#### App - Review #########################################################
###########################################################################

# Heading and input description
st.markdown(tformat("Record Linkage Review", el = 'h1'), unsafe_allow_html=True)

# Check if RLR is ready to review links
if (st.session_state['rlr'].ready_to_review):
    # Grab the current variable data associated with current record pair
    curr_comp_data = st.session_state['rlr'].get_comp_pair("grouped")
    curr_comp_index = st.session_state['rlr'].curr_comp_pair_index
    num_comparisons = st.session_state['rlr'].comp_df.shape[0]

    # Data Comparison Titles
    comp_heading_text = f"Linkage {curr_comp_index+1}/{num_comparisons}"
    st.markdown(tformat(comp_heading_text, el = 'h3'),  unsafe_allow_html=True)
    tcol1, tcol2 = st.columns(2)
    tcol1.markdown(tformat("Left Data"),  unsafe_allow_html=True)
    tcol2.markdown(tformat("Right Data"),  unsafe_allow_html=True)

    # Print actual data in comparison (iterate through var schemas)
    for var_group in curr_comp_data:
        Lcol, Mcol, Rcol = st.columns([4,1,4])
        # Print all data values in left column
        for val in var_group['lvals']:
            Lcol.markdown(tformat(str(val),'R'),  unsafe_allow_html=True)
        # Print the name of the comparison group in the middle column
        Mcol.markdown(tformat(var_group['name']),  unsafe_allow_html=True)
        # Print all data values in left column
        for val in var_group['rvals']:
            Rcol.markdown(tformat(str(val),'L'),  unsafe_allow_html=True)

    # Print any note associated with this comparison pair
    note_col = st.session_state['rlr'].REV_NOTE_COL
    old_note = st.session_state['rlr'].comp_df.loc[curr_comp_index, note_col]
    new_note = st.text_input("Note:", value = old_note, key = f"note_{curr_comp_index}")
    # st.session_state['rlr'].comp_df.loc[curr_comp_index, note_col] = new_note
    st.session_state['rlr'].save_label_or_note(new_note, 'note', delay_file_save = True)

    # Grab the label choices and the label for current comparison
    choices = ["No Label"] + st.session_state['rlr'].get_label_choices()
    label_col = st.session_state['rlr'].REV_LABEL_COL
    curr_label = st.session_state['rlr'].comp_df.loc[curr_comp_index, label_col]
    if curr_label in choices:
        curr_label_ind = choices.index(curr_label)
    else:
        # TODO: Unrecognized labels are considered unlabeled (fix so it displays labels outside of choices)
        curr_label_ind = 0

    # Display buttons for link determinations
    prev_col, sp_1, choice_col, sp_2, next_col = st.columns([1,1,2,1,1])
    prev_col.button("<< Previous Pair", disabled=(curr_comp_index==0), on_click=prev_pair)
    prev_col.button("<< Previous Unlabeled")
    # choice_col.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
    new_label = choice_col.radio("Choose label determination:", choices,
                                key = f"lab_choices_{curr_comp_index}",
                                index = curr_label_ind)
    next_col.button("Next Pair >>", disabled=(curr_comp_index==num_comparisons-1), on_click=next_pair)
    next_col.button("Next Unlabeled >>")
    # Save the label choice to rlr instance
    if new_label == "No Label": new_label = ""
    st.session_state['rlr'].save_label_or_note(new_label, 'label', delay_file_save = True)

    # Note about local version of data
    st.write("Note: All labels and notes are only stored temporarily in browser cache. To save locally use the download button in the sidebar.")
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