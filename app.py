import streamlit as st
import json
from elasticsearch import Elasticsearch
import plotly.express as px
import re
import uuid
from annotated_text import annotated_text
import pandas as pd

with st.sidebar:
    st.markdown(
        """
    <style>
        [data-testid=stSidebar] [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
    )
    st.image('https://logowik.com/content/uploads/images/elastic-search2066.jpg')
    st.markdown("<h1 style='text-align: center; color: black;'>Elastic Search</h1>",
            unsafe_allow_html=True)
    
    # Establish a connection to your Elasticsearch cluster
    es = Elasticsearch(hosts = [{"host":"localhost", "port":9200, "scheme":"http"}])

    # Listing all available indexes (projects)
    all_indexes = es.indices.get_alias().keys()
    # Filter indexes to only include 'prop_preserv' and 'index_extract'
    allowed_indexes = ['prop_preserv', 'index_extract']
    filtered_indexes = [index for index in all_indexes if index in allowed_indexes]
    # User selects an index (project) from the sidebar
    index_name = st.selectbox("Select an Index", filtered_indexes)

    choice = st.radio("Navigation", [
                      'Model Clauses', 'NLP Visualization', 'JSON Out', 'Document Management'])
    st.info("Elastic Stack empowers organizations beyond traditional enterprise search, offering a robust platform that seamlessly integrates document and language understanding. It uncovers valuable insights, supporting employees in navigating complex processes with agility and intelligence.")

if choice in ['Model Clauses', 'NLP Visualization', 'JSON Out']:
    query = st.text_input("Pass your input here")

if choice == 'Model Clauses':
    st.title('Analyse Clauses')

    if query:
        # Elasticsearch query instead of Watson Discovery query
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["Recording Date", "Job_Id", "Doc_Id", "Buyer", "Seller", "TEXT", "Doc Type"]
                            }
                        }
                    ]
                }
            }
        }
        # Searching in the selected index
        results = es.search(index=index_name, body=es_query)

        st.info(f'{results["hits"]["total"]["value"]} results found')

        for document in results["hits"]["hits"]:
            try:
                # Adjust the following lines based on your Elasticsearch document structure
                raw_result = document["_source"]["TEXT"]
                res = re.split(r"(\<em>)|(\</em>)", raw_result)

                annotated = []
                line_iter = enumerate(res)
                for idx, x in line_iter: 
                    if x not in ["<em>", "</em>", None]:
                        annotated.append(x)
                    if x == "<em>":
                        annotation = (res[idx+2], "match")
                        annotated.append(annotation)
                        line_iter.__next__() 
                        line_iter.__next__() 

                with st.expander(raw_result[:100].replace('<em>', '').replace('</em>', '')):
                    annotated_text(*annotated)
                    st.write('---------------------------------------------------------')
                    col1, col2, col3, col4 = st.columns((4, 2, 1, 1))
 
                    with col1: 
                        st.write('Relevance Score:', document["_score"])
                    with col2: 
                        st.write('**Was this helpful?**') 
                    with col3:
                        st.button('👍 Yes', key=uuid.uuid1())
                    with col4: 
                        st.button('👎 No', key=uuid.uuid1())                    

            except Exception as e:
                pass

# NLP Visualization Section
if choice == 'NLP Visualization':
    st.title('Visualize Your Documents')

    if query:
        # Elasticsearch query and aggregation
        es_query = {
            "query": {
                "match": {
                    "TEXT": query  # Assuming "TEXT" is the field you want to search
                }
            },
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "Recording Date.keyword"  # Update with the appropriate field for aggregation
                    }
                }
            }
        }

        # Searching in the selected index
        results = es.search(index=index_name, body=es_query)

        try:
            aggregation_data = results["aggregations"]["categories"]
            data_for_chart = {"Category": [], "Count": []}

            for bucket in aggregation_data['buckets']:
                data_for_chart["Category"].append(bucket['key'])
                data_for_chart["Count"].append(bucket['doc_count'])
            df_for_chart = pd.DataFrame(data_for_chart)
            #st.write("DataFrame for Chart:", df_for_chart)  # Add this line for debug
            chart = px.bar(df_for_chart, x="Category", y="Count", title="Document Categories")
            st.plotly_chart(chart)
        except Exception as e:
            pass


if choice == 'Document Management':
    st.file_uploader("Upload a new document to ElasticSearch")

if choice == 'JSON Out':
    
    if query:
        # Elasticsearch query
        es_query = {
            "query": {
                "match": {
                    "TEXT": query  # Assuming "TEXT" is the field you want to search
                }
            }
        }

        # Searching in the selected index
        results = es.search(index=index_name, body=es_query)

        st.title('Displaying Elasticsearch JSON')

        if "hits" in results and "hits" in results["hits"]:
            data = [hit["_source"] for hit in results["hits"]["hits"]]
            st.json(data)
