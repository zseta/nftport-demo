import streamlit as st
import pandas as pd
from plotly import express as px
import data_utils


# set some basic info about the demo
title = "NFTs sold by account - Powered by NFTPort"
st.set_page_config(page_title=title,
                   page_icon=None,
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={
                        'About': "https://nftport.xyz"
                    })


st.title(title)
    
example_addresses = ("0x7FA6ff8c0c938030FA58d1959fB991455DFB12F6",
                     "0xBc5B7a4fc2Cd56489050c1004C1F7d5a14cf435e",
                     "0xce90a7949bb78892f159f428d0dc23a8e3584d75",
                     "0x3DB46c06140817b18F2c2031B7d42180349b122D",
                     "0x39179D59CF8cC2D3A86a1569089b84A47B3bB22A",
                     "0xe2ceDC47153286f185939d7bDd2f5ec09F8C1F2a",
                     "")
chains = ("ethereum", "polygon")
filters = {
    "address": example_addresses[0],
    "chain": chains[0]
}

df = None

# sidebar with filters
with st.sidebar:
    filters["address"] = st.selectbox("example ETH addresses",
                                                  example_addresses)
    custom_address = st.text_input("use a custom address instead:", value="")
    if custom_address != "":
        filters["address"] = custom_address

    df = data_utils.extract_transactions(filters["address"], filters["chain"])
    if df is None:
        st.error("Account address not found!")
    elif len(df) == 0:
        st.error("Sale transactions not found!")
    else:
        df["date"] = pd.to_datetime(df['date'])
    st.info(
        """Want to build an app like this? [Check out NFTPort](https://www.nftport.xyz/data-api) for NFT data APIs"""
    )       
    

# high-level metrics
st.subheader(f"High-level metrics")

# blockchain explorer url
address_explorer_url = data_utils.explorer_page_url(filters["chain"], address=filters['address'])
st.markdown(f"Address: [{filters['address']}]({address_explorer_url})")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Number of sale transactions", value=len(df))
with col2:
    avg_price = df["price_value"].mean()
    st.metric(label="Average price", value=data_utils.format_price(avg_price))
with col3:
    min_price = df["price_value"].min()
    st.metric(label="Lowest price", value=data_utils.format_price(min_price))
with col4:
    max_price = df["price_value"].max()
    st.metric(label="Highest price", value=data_utils.format_price(max_price))



col1, col2, col3 = st.columns(3)
# per marketplace
with col1:
    st.subheader("Marketplace breakdown ")
    count_df = df.groupby(by=df["marketplace"]).count().rename(columns={"hash": "count"})
    data_utils.reset_index(count_df)
    chart = px.bar(count_df, x="marketplace", y="count",
                   color="marketplace")
    chart.update_layout(showlegend=False)
    st.plotly_chart(chart, use_container_width=True)
    
# most recently sold NFT
most_recent_tx = df.head(1)[["nft_address", "nft_tokenid", "hash"]].to_dict()
nft_contract_address = most_recent_tx["nft_address"][0]
nft_token_id = most_recent_tx["nft_tokenid"][0]
most_recent_nft = data_utils.extract_nft(nft_contract_address,
                                             nft_token_id,
                                             filters["chain"])
with col2:
    st.subheader("Most recently sold NFT")
    if most_recent_nft is None:
        st.text("NFT not found in database.")
    else:
        if most_recent_nft.get('metadata') is None:
            st.text("Metadata not available for this NFT")
        else:
            st.text(f"name: {most_recent_nft['metadata'].get('name')}")
            st.text(f"minted: {most_recent_nft['mint_date']}")
            st.text(f"contract address: {most_recent_nft['contract_address']}")
            st.text(f"token id: {most_recent_nft['token_id']}")
            explorer_url = data_utils.explorer_page_url(filters["chain"], tx_hash=most_recent_tx["hash"][0])
            st.markdown(f"[Look it up on blockchain explorer!]({explorer_url})")
        
with col3:
    if most_recent_nft is not None:
        st.image(most_recent_nft["cached_file_url"], width=400)
    


# most recent transactions
st.subheader(f"Most recent transactions")
df.index += 1
st.table(df.head(5)[["date", "marketplace", "price_currency", "price_value", "quantity", "hash"]])


# sales volume & count
st.subheader(f"Sales volume & count")
volume_df = df.groupby(by=df["date"].dt.date) \
              .agg({"price_value": "sum", "hash": "count"}) \
              .rename(columns={"price_value": "sales_volume",
                               "hash": "sales_count"})
data_utils.reset_index(volume_df)
chart_volume = px.line(volume_df, x="date", y=["sales_volume"],
                    markers=True, title="Sales volume")
chart_count = px.line(volume_df, x="date", y=["sales_count"],
                    markers=True, title="Sales count")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(chart_volume, use_container_width=True)
with col2:
    st.plotly_chart(chart_count, use_container_width=True)
with st.expander("See data"):
    st.table(volume_df)
