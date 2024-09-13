import streamlit as st
import requests
import pandas as pd
import logging
import sys
import json
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(page_title="Chain ID Glossary",
                   page_icon="🔗",
                   layout="wide")


@st.cache_data(ttl=timedelta(hours=1))
def fetch_chain_data(include_evm, include_svm, only_testnets):
    url = "https://api.skip.build/v2/info/chains"
    params = {
        "include_evm": str(include_evm).lower(),
        "include_svm": str(include_svm).lower(),
        "only_testnets": str(only_testnets).lower()
    }
    try:
        logger.debug(f"Fetching data from API with params: {params}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info("API Response received successfully")
        logger.debug(f"Raw API response: {response.text}")
        data = response.json()
        return data
    except requests.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        st.error(f"Error fetching data from API: {e}")
        return None


def process_chain_data(data):
    logger.debug("Processing chain data")
    logger.debug(f"Input data structure: {type(data)}")
    logger.debug(f"Input data content: {json.dumps(data, indent=2)}")
    if not data or not isinstance(data, dict) or 'chains' not in data:
        logger.warning("Invalid or empty data received")
        return pd.DataFrame()

    chains = []
    for chain in data['chains']:
        logger.debug(f"Processing chain: {json.dumps(chain, indent=2)}")
        chain_info = {
            "Logo URI": chain.get("logo_uri", "N/A"),
            "Name": chain.get("chain_name", "N/A").lower(),
            "Chain ID": chain.get("chain_id", "N/A"),
            "PFM Enabled": chain.get("pfm_enabled", "N/A"),
            "Chain Type": chain.get("chain_type", "N/A"),
            "Is Testnet": chain.get("is_testnet", "N/A"),
            "Pretty Name": chain.get("pretty_name", "N/A"),
            "Bech32 Prefix": chain.get("bech32_prefix", "")
        }
        chains.append(chain_info)

    df = pd.DataFrame(chains)
    logger.debug(f"Processed {len(df)} chains")
    logger.debug(f"Processed DataFrame:\n{df.to_string()}")
    return df


def generate_html_table(df):
    html = '<table style="width:100%"><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            if col == 'Logo URI' and row[col] != 'N/A':
                html += f'<td><img src="{row[col]}" width="50"></td>'
            else:
                html += f'<td>{row[col]}</td>'
        html += '</tr>'
    html += '</table>'
    return html


def main():
    try:
        logger.info("Starting Chain Data Explorer application")
        st.title("🔗 Chain ID Glossary")
        st.write(
            "Explore and search through blockchain network data from Skip Go API."
        )

        # Add toggle buttons
        logger.debug("Setting up toggle buttons")
        col1, col2, col3 = st.columns(3)
        with col1:
            include_evm = st.toggle("Include EVM", value=True)
        with col2:
            include_svm = st.toggle("Include SVM", value=True)
        with col3:
            only_testnets = st.toggle("Only Testnets", value=False)

        # Fetch and process data
        logger.info("Fetching chain data")
        raw_data = fetch_chain_data(include_evm, include_svm, only_testnets)
        df = process_chain_data(raw_data)

        if df.empty:
            logger.warning("No data available")
            st.warning("No data available. Please try again later.")
            return

        # Apply default sorting to filtered_df
        filtered_df = df.sort_values(by='Name')

        # Search functionality
        logger.debug("Setting up search functionality")
        search_term = st.text_input("Search chains", "")

        # Filter dataframe based on search term
        if search_term:
            logger.debug(f"Filtering data with search term: {search_term}")
            filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(
                str).str.contains(search_term, case=False, na=False).any(),
                                                        axis=1)]

        # Sorting functionality
        logger.debug("Setting up sorting functionality")
        sort_column = st.selectbox("Sort by",
                                   options=filtered_df.columns,
                                   index=list(
                                       filtered_df.columns).index('Name'))
        sort_order = st.radio("Sort order",
                              options=["Ascending", "Descending"],
                              index=0)

        if sort_column == "Name":
            sort_key = lambda x: x.str.lower()
        else:
            sort_key = None

        sorted_df = filtered_df.sort_values(
            by=sort_column,
            key=sort_key,
            ascending=(sort_order == "Ascending"))

        # Display the table
        logger.debug("Displaying chain data table")
        st.subheader("Chain Data Table")
        html_table = generate_html_table(sorted_df)
        st.write(html_table, unsafe_allow_html=True)

        logger.info("Chain Data Explorer application completed successfully")

    except Exception as e:
        logger.exception("An unexpected error occurred")
        st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    logger.info("Chain Data Explorer script started")
    main()
