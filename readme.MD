# RDFa Query and Rules Engine

A Flask-based web application that processes RDFa data from URLs, applies custom inference rules, and executes SPARQL queries.

## Features

- Parse RDFa content from any web URL
- Execute SPARQL queries (SELECT, ASK, CONSTRUCT, DESCRIBE)
- Apply custom inference rules to RDF graphs
- RESTful API endpoint for query processing
- Cross-origin resource sharing (CORS) enabled
- Browser-based web interface

## Installation
1. Clone the repository:
```bash
git clone https://github.com/raufur-simanto/jena-qr-rdf
```
2. Create a virtual environment:
```bash
python3.10 -m venv venv
```
3. Activate the virtual environment:
```bash
source venv/bin/activate # On Windows: venv\Scripts\activate
```
4. Install the required packages:
```bash
pip install -r requirements.txt
```
5. Run the application:
```bash
python app.py
```
6. Access the application in your browser at http://localhost:5000.

