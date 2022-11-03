""" Functions to extract and transform data.
"""

import requests
import streamlit as st
import pandas as pd

HEADERS = {"Authorization": st.secrets["NFTPORT"]["APIKEY"],
           "Content-Type": "application/json"}
BASE_URL = "https://api.nftport.xyz/v0"

def clean_sale_transactions(transactions):
    """Clean the raw response from the API.

    Args:
        transactions (list of dicts): NFT sale transactions (NFTPort response)

    Returns:
        list of dicts: cleaned list of NFT sale transactions
    """
    clean_transactions = []
    for tx in transactions:
        if tx["type"] == "sale":
            clean_tx = {"tx_type": tx["type"],
                        "nft_address": tx["nft"]["contract_address"],
                        "nft_tokenid": tx["nft"]["token_id"],
                        "quantity": tx["quantity"],
                        "price_currency": tx["price_details"]["asset_type"],
                        "price_value": tx["price_details"]["price"],
                        "price_usd": tx["price_details"].get("price_usd"),
                        "hash": tx["transaction_hash"],
                        "marketplace": tx.get("marketplace"),
                        "date": tx["transaction_date"]}
            clean_transactions.append(clean_tx)
    return clean_transactions


def reset_index(df):
    """Reset the dataframe index so it starts from 1 not 0.

    Args:
        df (dataframe): dataframe to reset
    """
    df.reset_index(inplace=True)
    df.index += 1


def extract_transactions(address, chain, tx_type="sell"):
    """Extract NFT transactions using the [NFTPort API](https://docs.nftport.xyz/docs/nftport/b3A6MzAxNDQ3NzQ-retrieve-transactions-by-an-account).

    Args:
        address (string): address of an account
        chain (string): name of the blockchain (currently supports "ethereum" and "polygon")
        tx_type (string): Type of transactions to extract. Defaults to "sell".
            See other accepted types in the [docs](https://docs.nftport.xyz/docs/nftport/b3A6MzAxNDQ3NzQ-retrieve-transactions-by-an-account).

    Returns:
        dataframe: A Pandas Dataframe object containing NFT sale transactions
    """
    endpoint = f"/transactions/accounts/{address}"
    url = f"{BASE_URL}{endpoint}"
    query_params = {"chain": chain,
                    "type": tx_type}
    response = requests.get(url, headers=HEADERS, params=query_params).json()
    if "transactions" not in response:
        return None
    cleaned_transactions = clean_sale_transactions(response["transactions"])
    return pd.DataFrame.from_records(cleaned_transactions)


def extract_nft(contract_address, token_id, chain):
    endpoint = f"/nfts/{contract_address}/{token_id}"
    url = f"{BASE_URL}{endpoint}?chain={chain}"
    response = requests.get(url, headers=HEADERS).json()
    if "nft" not in response:
        return None
    return response["nft"]


def format_price(price_str):
    """Format ETH price strings

    Args:
        price_str (string): ETH value

    Returns:
        string: formatted string
    """
    return f"{price_str:.2F} ETH"


def explorer_page_url(chain="ethereum", address=None, tx_hash=None):
    """Return the explorer page URL for the given address or transaction hash.

    Args:
        chain (str, optional): Can be 'ethereum' or 'polygon'. Defaults to "ethereum".
        address (string, optional): Valid address on the selected chain.
        tx_hash (string, optional): Valid transaction hash on the selected chain.

    Returns:
        string: Explorer page URL
    """
    if (address is None and tx_hash is None) or \
       (address is not None and tx_hash is not None):
        raise ValueError("Either `address` or `tx_hash` argument must be defined!")
    explorer_url = {"ethereum": "https://etherscan.io",
                    "polygon": "https://polygonscan.com"}
    address_endpoint = f"/address/{address}"
    hash_endpoint = f"/tx/{tx_hash}"
    if address is not None:
        return f"{explorer_url[chain]}{address_endpoint}"
    return f"{explorer_url[chain]}{hash_endpoint}"
