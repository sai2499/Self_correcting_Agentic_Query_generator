import streamlit as st
import os

# Set page configuration
st.set_page_config(
    page_title="Agentic Database Query Generator",
    page_icon="🤖",
    layout="wide"
)
from langchain_community.chat_models import ChatOllama
try:
    from langchain_groq import ChatGroq
except ImportError:
    # Fallback if langchain_groq is not available
    ChatGroq = None
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities.sql_database import SQLDatabase
import psycopg2
from neo4j import GraphDatabase
from typing import TypedDict, Annotated
import json

# App title and description 
st.title("Agentic Database Query Generator")
st.markdown("""
This application generates SQL and Cypher queries from natural language questions,
grades them for schema relevance, and executes them against PostgreSQL and Neo4j databases.
""")

# Create a two-column layout for the database configuration
left_col, right_col = st.columns(2)

# Left column - Neo4j Configuration
with left_col:
    with st.expander("Neo4j Configuration", expanded=False):
        neo4j_uri = st.text_input("Neo4j URI", value="bolt://localhost:7687")
        neo4j_username = st.text_input("Neo4j Username", value="neo4j")
        neo4j_password = st.text_input("Neo4j Password", type="password", value="root1234")

# Right column - PostgreSQL Configuration
with right_col:
    with st.expander("PostgreSQL Configuration", expanded=False):
        pg_host = st.text_input("PostgreSQL Host", value="localhost")
        pg_port = st.text_input("PostgreSQL Port", value="5432")
        pg_database = st.text_input("PostgreSQL Database", value="postgres")
        pg_username = st.text_input("PostgreSQL Username", value="postgres")
        pg_password = st.text_input("PostgreSQL Password", type="password", value="root")

# Create another two-column layout for the schema configuration
col1, col2 = st.columns(2)

# Left column - Neo4j Schema
with col1:
    with st.expander("Neo4j Schema", expanded=False):
        neo4j_schema = st.text_area(
            "Neo4j Graph Schema",
            height=200,
            value="""Node properties:
- User: {user_id: INTEGER, username: STRING, email: STRING}
- Course: {course_id: INTEGER, title: STRING, description: STRING, price: FLOAT, level: STRING}
- Instructor: {instructor_id: INTEGER, name: STRING, bio: STRING, email: STRING}

Relationships:
- (User)-[:ENROLLED_IN]->(Course)
- (User)-[:REVIEWED]->(Course) {rating: INTEGER, comment: STRING}
- (Instructor)-[:TEACHES]->(Course)
""")

# Right column - SQL Schema
with col2:
    with st.expander("SQL Schema", expanded=False):
        sql_ddl_schema = st.text_area(
            "SQL DDL Schema",
            height=200,
            value="""CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    level VARCHAR(20) CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE instructors (
    instructor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    course_id INTEGER REFERENCES courses(course_id),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, course_id)
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    course_id INTEGER REFERENCES courses(course_id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

CREATE TABLE course_instructors (
    course_id INTEGER REFERENCES courses(course_id),
    instructor_id INTEGER REFERENCES instructors(instructor_id),
    PRIMARY KEY (course_id, instructor_id)
);"""
    )

# LangGraph Visualization Section
st.header("LangGraph Workflow Visualization")
st.image("output.png", use_column_width=False)
st.markdown("*The above graph shows the agentic workflow for query generation and execution.*")

# Query Generator Section
st.header("Query Generator")

# Question input
question = st.text_area("Enter your question", height=100, placeholder="What courses are taught by instructors with 'AI' in their bio?")

# API Key for model
with st.expander("Model Configuration", expanded=False):
    groq_api_key = st.text_input("GROQ API Key", type="password")
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key

# Process button
if st.button("Generate Queries and Execute"):
    if not question:
        st.error("Please enter a question.")
    elif not groq_api_key:
        st.error("GROQ API Key not set. Please add it above.")
    else:
        with st.spinner("Generating queries and executing..."):
            try:
                # Initialize model
                if ChatGroq is None:
                    st.error("ChatGroq is not available. Please install langchain_groq package with: pip install langchain_groq")
                    st.stop()
                model = ChatGroq(model="llama3-70b-8192")
                
                # Define SQL generation prompt
                sql_prompt = ChatPromptTemplate.from_template("""
                You are a SQL expert. Given the following SQL DDL schema and a question, generate a SQL query that answers the question.
                
                SQL DDL Schema:
                {ddl_schema}
                
                Question: {question}
                
                SQL Query:
                """)
                
                # Define Cypher generation prompt
                cypher_prompt = ChatPromptTemplate.from_template("""
                You are a Neo4j Cypher expert. Given the following Neo4j schema and a question, generate a Cypher query that answers the question.
                
                Neo4j Schema:
                {schema}
                
                Question: {question}
                
                Cypher Query:
                """)
                
                # Create chains
                sql_chain = sql_prompt | model | StrOutputParser()
                cypher_chain = cypher_prompt | model | StrOutputParser()
                
                # Generate queries
                sql_query = sql_chain.invoke({
                    "ddl_schema": sql_ddl_schema,
                    "question": question
                })
                sql_query = sql_query.replace("<s> ", "").replace("`", "")
                
                cypher_query = cypher_chain.invoke({
                    "schema": neo4j_schema,
                    "question": question
                })
                
                # Execute SQL query
                try:
                    conn = psycopg2.connect(
                        host=pg_host,
                        port=pg_port,
                        dbname=pg_database,
                        user=pg_username,
                        password=pg_password
                    )
                    cursor = conn.cursor()
                    cursor.execute(sql_query)
                    sql_results = cursor.fetchall()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    sql_results = f"Error executing SQL query: {str(e)}"
                
                # Execute Cypher query
                try:
                    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
                    with driver.session() as session:
                        result = session.run(cypher_query)
                        cypher_results = [record.data() for record in result]
                    driver.close()
                except Exception as e:
                    cypher_results = None
                    st.error(f"Error executing Cypher query: {str(e)}")
                
                # Display results
                st.subheader("Generated Queries and Results")
                
                # Create two columns for displaying results
                neo4j_col, sql_col = st.columns(2)
                
                # Neo4j Results (Left Column)
                with neo4j_col:
                    st.markdown("**Neo4j Cypher Query**")
                    st.code(cypher_query, language="cypher")
                    
                    if cypher_results is not None:
                        st.markdown("**Neo4j Result**")
                        st.json(cypher_results)
                    else:
                        st.warning("Cypher query execution failed or returned no results.")
                
                # SQL Results (Right Column)
                with sql_col:
                    st.markdown("**SQL Query**")
                    st.code(sql_query, language="sql")
                    
                    if sql_results is not None:
                        st.markdown("**SQL Result**")
                        st.dataframe(sql_results)
                    else:
                        st.warning("SQL query execution failed or returned no results.")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Created with ❤️ using LangChain and Streamlit")
