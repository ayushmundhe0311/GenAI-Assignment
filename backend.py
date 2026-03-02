from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import SQLDatabase

# Database connection
db = SQLDatabase.from_uri(
    "postgresql+psycopg2://postgres:root@127.0.0.1:5432/genai_db"
)

schema = db.get_table_info()

# Local Llama Model
llm = ChatOllama(
    model="llama3.2:1b",
    temperature=0
)

prompt = ChatPromptTemplate.from_template("""
You are an expert PostgreSQL SQL generator.

Your job:
Convert a natural language question into a VALID PostgreSQL SQL query.

=====================
STRICT RULES (MANDATORY)
=====================
Use alias in column names where required dont use it for every column
If only one table exists in schema,
Use aggregations table directly.
1. Use ONLY columns present in schema.
2. NEVER invent tables or columns.
3. NEVER use 'timestamp' unless it exists in schema.
4. Return ONLY SQL query.
5. Do NOT add explanations or markdown.
6. Always include selected columns explicitly.
7. Every aggregation must have an alias.
8. When using GROUP BY:
   - All non-aggregated columns MUST appear in GROUP BY.
9. Use LIMIT only when question asks for top/bottom/latest.
10. *Prefer simple SQL over complex nested queries.*
11. NEVER create table aliases that are not defined.
12. NEVER use JOIN unless multiple tables are explicitly present in schema.
13. If query can be solved using ONE table, DO NOT use subqueries or JOIN.
14. Prefer SIMPLE queries over complex queries.

=====================
AVAILABLE SCHEMA
=====================
{schema}

=====================
EXAMPLES (Few-shot learning)
=====================

Q: total number of records
SQL:
SELECT COUNT(*) AS total_records
FROM aggregations;

Q: count records per machine
SQL:
SELECT machine_name, COUNT(*) AS record_count
FROM aggregations
GROUP BY machine_name;

Q: average OEE per machine
SQL:
SELECT machine_name, AVG(oee) AS avg_oee
FROM aggregations
GROUP BY machine_name;

Q: total production per machine
SQL:
SELECT machine_name, SUM(production) AS total_production
FROM aggregations
GROUP BY machine_name;

Q: total rejection per machine
SQL:
SELECT machine_name, SUM(rejection) AS total_rejection
FROM aggregations
GROUP BY machine_name;

Q: show records from shift I
SQL:
SELECT *
FROM aggregations
WHERE shift_name = 'I';

Q: average availability for each shift
SQL:
SELECT shift_name, AVG(availability) AS avg_availability
FROM aggregations
GROUP BY shift_name;

Q: machine with highest average OEE
SQL:
SELECT machine_name, AVG(oee) AS avg_oee
FROM aggregations
GROUP BY machine_name
ORDER BY avg_oee DESC
LIMIT 1;

Q: top 5 machines by production
SQL:
SELECT machine_name, SUM(production) AS total_production
FROM aggregations
GROUP BY machine_name
ORDER BY total_production DESC
LIMIT 5;

Q: production per day
SQL:
SELECT shift_date, SUM(production) AS total_production
FROM aggregations
GROUP BY shift_date
ORDER BY shift_date;

Q: latest production day
SQL:
SELECT shift_date, SUM(production) AS total_production
FROM aggregations
GROUP BY shift_date
ORDER BY shift_date DESC
LIMIT 1;

Q: average performance per machine
SQL:
SELECT machine_name, AVG(performance) AS avg_performance
FROM aggregations
GROUP BY machine_name;

Q: records where OEE is greater than 80
SQL:
SELECT *
FROM aggregations
WHERE oee > 80;

Q: minimum production recorded
SQL:
SELECT MIN(production) AS min_production
FROM aggregations;

Q: maximum production per machine
SQL:
SELECT machine_name, MAX(production) AS max_production
FROM aggregations
GROUP BY machine_name;

=====================
NOW GENERATE SQL
=====================
*JUST SQL CODE NO EXPLANANTION*
Question:
{question}
*Prefer simple SQL over complex nested queries.*
*create SQL Query based on user_query it should check the column_name and then generate SQL query*
                                          USE AGGREGATION TABLE ONLY there is no other table
                                          create simple queries only
#SQL COMMAND ONLY
""")

# Chain
sql_chain = prompt | llm | StrOutputParser()


def generate_sql(question: str):

    sql_query = sql_chain.invoke({
        "schema": schema,
        "question": question
    })

    # cleanup if LLM adds markdown
    sql_query = (
        sql_query.replace("```sql", "")
        .replace("```", "")
        .strip()
    )

    return sql_query