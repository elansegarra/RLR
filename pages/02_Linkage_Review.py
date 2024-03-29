from fileinput import filename
import streamlit as st
import pandas as pd
from backend.rlr import rlr
import os

st.set_page_config(page_title="RLR: Linkage Review", page_icon="📈")

###########################################################################
#### Function Definitions #################################################
###########################################################################

def tformat(text, align='C', el='p'):
    align_dict = {'L':'left', 'C':'center','R':'right'}
    return(f"<{el} style='text-align: {align_dict[align]};'>{text}</{el}>")

def next_pair():
    """ Move to next comparison if not at end """
    if st.session_state['rlr'].curr_comp_pair_index < st.session_state['rlr'].comp_df.shape[0]-1:
        st.session_state['rlr'].curr_comp_pair_index += 1

def next_unlabeled_pair():
    """ Move to next comparison that is unlabeled if not at end """
    if st.session_state['rlr'].curr_comp_pair_index == st.session_state['rlr'].comp_df.shape[0]-1:
        return
    # Iterate until we find unlabeled comparison or the end of comparison list
    label_col = st.session_state['rlr'].REV_LABEL_COL
    curr_ind = st.session_state['rlr'].curr_comp_pair_index + 1
    curr_label = st.session_state['rlr'].comp_df.loc[curr_ind, label_col]
    while (curr_ind < st.session_state['rlr'].comp_df.shape[0]-1) and (curr_label != ""):
        curr_ind += 1
        curr_label = st.session_state['rlr'].comp_df.loc[curr_ind, label_col]
    st.session_state['rlr'].curr_comp_pair_index = curr_ind

def prev_pair():
    """ Move to previous comparison if not at beginning """
    if st.session_state['rlr'].curr_comp_pair_index > 0:
        st.session_state['rlr'].curr_comp_pair_index -= 1

def prev_unlabeled_pair():
    """ Move to previous comparison that is unlabeled if not at beginning """
    if st.session_state['rlr'].curr_comp_pair_index <= 0:
        return
    # Iterate until we find unlabeled comparison or the end of comparison list
    label_col = st.session_state['rlr'].REV_LABEL_COL
    curr_ind = st.session_state['rlr'].curr_comp_pair_index - 1
    curr_label = st.session_state['rlr'].comp_df.loc[curr_ind, label_col]
    while (curr_ind > 0) and (curr_label != ""):
        curr_ind -= 1
        curr_label = st.session_state['rlr'].comp_df.loc[curr_ind, label_col]
    st.session_state['rlr'].curr_comp_pair_index = curr_ind

###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# Initializing rlr backend if not done already
if 'rlr' not in st.session_state:
    st.session_state['rlr'] = rlr()
if 'review_file_name' not in st.session_state:
    st.session_state['review_file_name'] = "labeled_data.csv"

with st.sidebar:
    # Display information if a file has been loaded
    if (st.session_state['rlr'].comps_loaded):
        # Gather label counts and display a summary
        st.subheader("File Label Summary")
        l_counts = st.session_state['rlr'].get_label_counts()
        l_counts_df = pd.DataFrame.from_dict(l_counts, orient = 'index', columns = ['Count'])
        l_counts_df.index.name = "Label"
        l_counts_df['%'] = l_counts_df['Count']/l_counts_df['Count'].sum()*100
        l_counts_df['%'] = l_counts_df['%'].round(1)
        st.dataframe(l_counts_df)
    
    st.header("Options")
    if (st.session_state['rlr'].comps_loaded):
        # Check box for auto saving label
        autosave_val = st.checkbox("Autosave Labels", value = st.session_state['rlr'].autosave,
                help = "Automatically save labels and notes to comparison file as they are changed")
        if (autosave_val != st.session_state['rlr'].autosave):
            st.session_state['rlr'].set_autosave(autosave_val)

    # Display and allow editing of current label choices
    new_label_choices = []
    curr_labels = "\n".join(st.session_state['rlr'].label_choices)
    new_labels = st.text_area("Label Choices", help = "Edit the label choices here (each line is a separate label choice)", value = curr_labels)
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

    # Check if a pair was indeed grabbed (might not work if indices weren't found)
    if curr_comp_data is None:
        l_id = st.session_state['rlr'].comp_df.loc[curr_comp_index,st.session_state['rlr'].id_vars_l]
        r_id = st.session_state['rlr'].comp_df.loc[curr_comp_index,st.session_state['rlr'].id_vars_r]
        st.write(f"No records found for id={l_id} or id={r_id} (maybe both)")
    else:
        # Print left and right side headings (with names if passed)
        left_name = "" if (st.session_state['rlr'].dataL_name is None) else f" ({st.session_state['rlr'].dataL_name})"
        right_name = "" if (st.session_state['rlr'].dataR_name is None) else f" ({st.session_state['rlr'].dataR_name})"
        tcol1, tcol2 = st.columns(2)
        tcol1.markdown(tformat("Left Data"+left_name),  unsafe_allow_html=True)
        tcol2.markdown(tformat("Right Data"+right_name),  unsafe_allow_html=True)

        # Print actual data in comparison (iterate through var schemas)
        for var_group in curr_comp_data:
            Lcol, Mcol, Rcol = st.columns([4,1,4])
            # Print all data values in left column
            l_val = "<br>".join([str(item) for item in var_group['lvals']])
            Lcol.markdown(tformat(l_val,'R'),  unsafe_allow_html=True)
            # Print the name of the comparison group in the middle column
            Mcol.markdown(tformat(var_group['name']),  unsafe_allow_html=True)
            # Print all data values in right column
            r_val = "<br>".join([str(item) for item in var_group['rvals']])
            Rcol.markdown(tformat(r_val,'L'),  unsafe_allow_html=True)

        # Print any note associated with this comparison pair
        note_col = st.session_state['rlr'].REV_NOTE_COL
        old_note = st.session_state['rlr'].comp_df.loc[curr_comp_index, note_col]
        new_note = st.text_input("Note:", value = old_note, key = f"note_{curr_comp_index}")
        # st.session_state['rlr'].comp_df.loc[curr_comp_index, note_col] = new_note
        st.session_state['rlr'].save_label_or_note(new_note, 'note')

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
    prev_col, sp_1, choice_col, sp_2, next_col = st.columns([2.5,1,2,1,2.5])
    prev_col.button("<< Previous Pair", disabled=(curr_comp_index==0), on_click=prev_pair)
    prev_col.button("<< Previous Unlabeled", disabled=(curr_comp_index==0), on_click=prev_unlabeled_pair)
    # choice_col.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
    new_label = choice_col.radio("Choose label:", choices,
                                key = f"lab_choices_{curr_comp_index}",
                                index = curr_label_ind, disabled=(curr_comp_data is None))
    next_col.button("Next Pair >>", disabled=(curr_comp_index==num_comparisons-1), on_click=next_pair)
    next_col.button("Next Unlabeled >>", disabled=(curr_comp_index==num_comparisons-1),
                        on_click=next_unlabeled_pair)
    # Save the label choice to rlr instance (but first grab the labeled count before this label)
    if new_label == "No Label": new_label = ""
    num_labeled_before = st.session_state['rlr'].comp_df[st.session_state['rlr'].REV_LABEL_IND_COL].sum()
    num_pairs = st.session_state['rlr'].comp_df.shape[0]
    st.session_state['rlr'].save_label_or_note(new_label, 'label')
    # Check if this was the final pair to be labeled (if so celebrate!)
    num_labeled_after = st.session_state['rlr'].comp_df[st.session_state['rlr'].REV_LABEL_IND_COL].sum()
    if (num_labeled_before == num_pairs-1) and (num_labeled_after == num_pairs):
        st.balloons()

    # Note about local version of data
    st.write("Note: All labels and notes are only stored temporarily in browser cache. To save locally use the download button in the sidebar.")
else:
    st.write("Not all pieces necessary for review have been initialized:")
    # Check which parts are not yet initialized
    text = ""
    if not st.session_state['rlr'].dataL_loaded:
        text += "  - Need to load a left data set (refer to Data Input page)\n"
    if not st.session_state['rlr'].dataR_loaded:
        text += "  - Need to load a right data set (refer to Data Input page)\n"
    if not st.session_state['rlr'].var_schema_loaded:
        text += "  - Need to define a variable comparison schema (refer to Data Input page)\n"
    if not st.session_state['rlr'].comps_loaded:
        text += "  - Need to load a file of linkages for review (refer to Data Input page)\n"
    if len(st.session_state['rlr'].label_choices) == 0:
        text += "  - Need to define the label choices (refer to sidebar)\n"
    st.markdown(text)