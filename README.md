# Agentic AI Query System

## Overview
This project implements an agentic AI system that can process natural language queries and generate appropriate SQL and Cypher queries for database interactions. The system uses LangGraph to create a workflow that validates, regenerates, and executes queries against both PostgreSQL and Neo4j databases.

## Features
- Dual database query generation (SQL for PostgreSQL and Cypher for Neo4j)
- Automatic query validation and regeneration
- Intelligent query grading system
- End-to-end workflow from natural language to database results

## Architecture
The system uses a state-based graph architecture with the following components:
- Query generation nodes for SQL and Cypher
- Query validation nodes that check schema compatibility
- Query regeneration nodes for invalid queries
- Database execution nodes for retrieving results

## Dependencies
- LangChain and LangGraph for workflow orchestration
- ChatGroq and ChatOllama for LLM interactions
- Neo4j and PostgreSQL database connectors
- Pydantic for structured output parsing

## Setup
1. Ensure you have PostgreSQL and Neo4j databases running
2. Configure database connection parameters in the code
3. Install required Python packages:
```
pip install langchain langchain_groq langgraph neo4j psycopg2 pydantic
```

## Usage
1. Initialize the graph with your query
2. The system will generate both SQL and Cypher queries
3. Queries are validated against their respective schemas
4. Invalid queries are automatically regenerated
5. Results are returned from both database systems

## Example
```python
# Initialize the workflow with a question
result = app.invoke({
    "sql_question": "Find all courses with no reviews",
    "cypher_question": "Find all courses with no reviews"
})

# Access the results
sql_results = result["sql_ans"]
cypher_results = result["cypher_ans"]
```

## License
[Your License Here]

## Contributors
[Your Name Here]
