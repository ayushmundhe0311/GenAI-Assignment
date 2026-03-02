import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from backend import generate_sql  


engine = create_engine(
    "postgresql+psycopg2://postgres:root@127.0.0.1:5432/genai_db"
)


st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")

st.title("🤖 GenAI SQL Chat Assistant")
st.caption("Local Llama • LangChain • PostgreSQL • Streamlit")


# CHAT HISTORY

if "messages" not in st.session_state:
    st.session_state.messages = []


# VISUALIZATION HELPERS (SAFE BLOCK)

def user_wants_visualization(query: str) -> bool:
    keywords = ["chart", "plot", "graph", "visualize", "visualization"]
    query = query.lower()
    return any(word in query for word in keywords)


def auto_visualize(df: pd.DataFrame):
    """
    Automatically create visualization based on dataframe structure
    """

    if df.empty:
        st.info("No data available for visualization.")
        return

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()

    # Too many columns → avoid messy charts
    if len(df.columns) > 6:
        st.warning("Too many columns. Visualization cannot be created automatically.")
        return

    if len(numeric_cols) == 0:
        st.warning("No numeric columns found for visualization.")
        return

    st.subheader("📊 Visualization")

    # Case 1: Category + Numeric → Bar Chart
    if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
        chart_df = df.set_index(non_numeric_cols[0])
        st.bar_chart(chart_df[numeric_cols])

    # Case 2: Only Numeric → Line Chart
    elif len(numeric_cols) >= 1:
        st.line_chart(df[numeric_cols])

    else:
        st.info("Suitable visualization not found.")


# DISPLAY PREVIOUS MESSAGES

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):

        if msg["type"] == "text":
            st.markdown(msg["content"])

        elif msg["type"] == "sql_result":
            st.subheader("Generated SQL")
            st.code(msg["sql"], language="sql")

            st.subheader("Query Result")
            st.dataframe(msg["data"], use_container_width=True)

            # show visualization for history also
            if msg.get("visualize", False):
                auto_visualize(msg["data"])

# USER INPUT

user_query = st.chat_input("Ask your database...")

if user_query:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "type": "text",
        "content": user_query
    })

    with st.chat_message("user"):
        st.markdown(user_query)

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking... Generating SQL and running query..."):

                # Generate SQL
                sql_query = generate_sql(user_query)

                # Execute SQL
                df = pd.read_sql(sql_query, engine)

                # Display results
                st.subheader("Generated SQL")
                st.code(sql_query, language="sql")

                st.subheader("Query Result")
                st.dataframe(df, use_container_width=True)

              
                # AUTO VISUALIZATION 
                visualize_flag = False

                if user_wants_visualization(user_query):
                    visualize_flag = True
                    auto_visualize(df)

        # Save assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "type": "sql_result",
            "sql": sql_query,
            "data": df,
            "visualize": visualize_flag
        })

    except Exception as e:
        error_msg = f"Error: {str(e)}"

        with st.chat_message("assistant"):
            st.error(error_msg)

        st.session_state.messages.append({
            "role": "assistant",
            "type": "text",
            "content": error_msg
        })