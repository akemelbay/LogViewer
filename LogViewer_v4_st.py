import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
import os
import base64
import random

st.set_page_config(layout="wide")


#CSS intections
st.markdown("""
    <style>
    /* Inject CSS to move the download button to the right */
    .st-key-CSV_download_button{
        float: right;
        margin-right: 0;
        margin-left: auto;
        display: block;
    }
    
    /* Make all multiselect labels larger */
    label[for^="Select data to plot"] {
        font-size: 1.5em !important;
        font-weight: bold !important;
    }
    
    /* CSS to remove max-width from selected badges in st.multiselect */
     .stMultiSelect [data-baseweb=select] span{
            max-width: none !important;
        }
    /* Hide Streamlit top bar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMain .block-container {padding-top: 2rem ! important}
    </style>
""", unsafe_allow_html=True)

# Read and encode the image
with open("quantum_duck.png", "rb") as image_file:
    encoded = base64.b64encode(image_file.read()).decode()
# Generate random filter values
invert = round(random.uniform(0, 1), 2)  # 0% to 100%
sepia = round(random.uniform(0, 1), 2)
saturate = random.randint(100, 5000)    # 100% to 5000%
hue_rotate = random.randint(0, 360)     # 0deg to 360deg
brightness = round(random.uniform(0.5, 1.5), 2)  # 50% to 150%
contrast = random.randint(50, 150)      # 50% to 150%

filter_str = (
    f"invert({int(invert*100)}%) "
    f"sepia({int(sepia*100)}%) "
    f"saturate({saturate}%) "
    f"hue-rotate({hue_rotate}deg) "
    f"brightness({int(brightness*100)}%) "
    f"contrast({contrast}%)"
)

# Display logo with random filter
st.markdown(
    f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{encoded}" width="70" 
         style="margin-right: 20px; filter: {filter_str};">
        <span style="font-size: 40px; font-weight: bold;">Cluster Tool Log Viewer</span>
    </div>
    """,
    unsafe_allow_html=True
)

#st.title("Cluster Tool Log Viewer")


font_dict=dict(family='Arial',
       size=12,
       )

st.markdown("""
    <style>
    /* Change background color of multiselect badges */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: rgb(240, 242, 246) !important;   /* Your color here */
        color: black !important;                /* Optional: text color */
        border-radius: 5px !important;          /* Optional: rounded corners */
    }
    </style>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, index_col=False)
    if ' Elapsed Time' in df.columns:
        df['Elapsed Time (str)'] = df[' Elapsed Time']
        df[' Elapsed Time'] = pd.to_datetime(df[' Elapsed Time'], format="%H:%M:%S.%f", errors='coerce')
    else:
        st.error('Column " Elapsed Time" not found!')
        st.stop()

    selectable_cols = [col for col in df.columns if col != ' Elapsed Time' and pd.api.types.is_numeric_dtype(df[col])]
    selected_cols = st.multiselect("Select data to plot", options=selectable_cols)
    
    fig = go.Figure()
    colors = pc.qualitative.Plotly
    x = df[' Elapsed Time']

    # Inject CSS to color badges according to selection order
    badge_css = ""
    for i, col in enumerate(selected_cols):
        color = colors[i % len(colors)]
        # nth-child is 1-based
        badge_css += f"""
        .stMultiSelect [data-baseweb="tag"]:nth-child({i+1}) {{
            background-color: {color} !important;
            color: white !important;
        }}
        """

    yaxis_layouts = {}
    for i, col in enumerate(selected_cols):
        axis_name = 'y' if i == 0 else f'y{i+1}'
        color = colors[i % len(colors)]
        fig.add_trace(go.Scattergl(
            x=x,
            y=df[col],
            mode='lines',
            name=col,
            yaxis=axis_name,
            line=dict(color=color)
        ))

        yaxis_dict = dict(
            title=dict(
                text=col,
                font=dict(color=color)
            ),
            tickfont=dict(color=color),
            overlaying='y' if i > 0 else None,  # Only overlay after the first
            side='left' if i > 0 else None,  # Only overlay after the first
            anchor='free' if i > 0 else None,  # Only overlay after the first
            autoshift=True if i > 0 else None,  # Only overlay after the first
            title_standoff=0,
            showgrid=(i == 0),
        )
        # Remove None values (overlaying for first axis)
        yaxis_dict = {k: v for k, v in yaxis_dict.items() if v is not None}
        yaxis_layouts[f'yaxis{i+1}' if i > 0 else 'yaxis'] = yaxis_dict

    fig.update_layout(
        xaxis=dict(
            title='Elapsed Time',
            spikemode='across+toaxis',
            spikedash='solid',
            spikecolor='gray',
            spikethickness=1,
            showgrid=True,
            tickformat="%H:%M:%S"
        ),
        height=800,
        template="plotly_white",
        margin=dict(l=80, r=40, t=40, b=40),
        showlegend=False,
        hovermode="x",
        **yaxis_layouts
    )


    if selected_cols:
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<style>{badge_css}</style>", unsafe_allow_html=True)
        # Show selected columns in an expander
        with st.expander("Show selected data as table"):
            cols_to_show = ['Elapsed Time (str)'] + selected_cols
            csv = df[cols_to_show].to_csv(index=False).encode('utf-8')
            # Get original filename
            original_name = uploaded_file.name  # e.g. "data.csv"
            # Split into name and extension
            name, ext = os.path.splitext(original_name)  # ('data', '.csv')
            # Create new filename
            new_filename = f"{name}_exported{ext}"  # 'data_exported.csv'
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=new_filename,
                mime='text/csv',
                key="CSV_download_button"
            )
            st.dataframe(df[cols_to_show])
    #else:
        #st.info("Select one or more columns to plot.")
#else:
    #st.info("Please upload a CSV file.")
