import logging
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Node, Variable, BNode
import requests
from io import StringIO
from pyRdfa import pyRdfa


app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_rules(g, rules_text):
    """Apply custom rules to the RDF graph"""
    app.logger.info("Applying rules...")
    new_triples = []
    triples = list(g)
    rules = [r.strip() for r in rules_text.split('\n') if r.strip() and not r.startswith('@prefix')]
    app.logger.info(f"Rules: {rules}")
    
    for rule in rules:
        app.logger.info(f"getting rule {rule}")
        if '=>' not in rule:
            continue
            
        condition, conclusion = rule.split('=>')
        conditions = [c.strip() for c in condition.split(')') if c.strip()]
        conditions = [c.replace('[', '').replace('(', '').strip() for c in conditions]
        
        matches = {}
        for condition in conditions:
            app.logger.info(f"getting condition {condition}")
            if not condition:
                continue
            vars = condition.split()
            if len(vars) != 3:
                continue
                
            s, p, o = vars
            for triple in triples:
                if (p.startswith('?') or p == str(triple[1])) and \
                   (o.startswith('?') or o == str(triple[2])):
                    if s.startswith('?'):
                        matches.setdefault(s, set()).add(triple[0])
                    if p.startswith('?'):
                        matches.setdefault(p, set()).add(triple[1])
                    if o.startswith('?'):
                        matches.setdefault(o, set()).add(triple[2])

        conclusion = conclusion.replace('(', '').replace(')', '').strip()
        app.logger.info(f"getting conclusion {conclusion}")
        if conclusion:
            s, p, o = [x.strip() for x in conclusion.split()]
            for match_s in matches.get(s, [str(s)]):
                for match_p in matches.get(p, [str(p)]):
                    for match_o in matches.get(o, [str(o)]):
                        new_triple = (
                            g.URIRef(match_s) if not isinstance(match_s, rdflib.term.URIRef) else match_s,
                            g.URIRef(match_p) if not isinstance(match_p, rdflib.term.URIRef) else match_p,
                            g.URIRef(match_o) if not isinstance(match_o, rdflib.term.URIRef) else match_o
                        )
                        new_triples.append(new_triple)

    for triple in new_triples:
        app.logger.info(f"Adding triple {triple}")
        g.add(triple)
    
    return g

def parse_rdfa_from_url(url):
    """Parse RDFa content from URL."""
    graph = Graph()
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        
        processor = pyRdfa()
        rdfa_graph = processor.graph_from_source(StringIO(response.text))
        
        for triple in rdfa_graph:
            graph.add(triple)
            
        return graph
        
    except Exception as e:
        logger.error(f"Error parsing RDFa: {e}", exc_info=True)
        raise ValueError(f"Error parsing RDFa: {e}")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        url = data.get('url')
        rules = data.get('rules', '')
        sparql_query = data.get('sparqlQuery')

        app.logger.info(f"Received URL: {url}")
        app.logger.info(f"Received rules: {rules}")
        app.logger.info(f"Received SPARQL query: {sparql_query}")

        # Parse the RDFa data using lxml
        g = parse_rdfa_from_url(url)
        app.logger.info(f"Number of triples in graph: {len(g)}")

        if rules:
            g = apply_rules(g, rules)

        qres = g.query(sparql_query)

        if sparql_query.lower().startswith('select'):
            results = []
            for row in qres:
                result_row = {}
                for var, value in zip(qres.vars, row):
                    result_row[str(var)] = str(value)
                results.append(result_row)
            return jsonify(results)

        elif sparql_query.lower().startswith('ask'):
            return jsonify({'result': bool(qres)})

        elif sparql_query.lower().startswith('construct'):
            result_graph = qres.graph
            triples = []
            for s, p, o in result_graph:
                triple = {
                    's': str(s),
                    'p': str(p),
                    'o': str(o) if not isinstance(o, Literal) else o.value
                }
                triples.append(triple)
            return jsonify({'triples': triples})

        elif sparql_query.lower().startswith('describe'):
            return jsonify({'triples': [{'s': str(s), 'p': str(p), 'o': str(o)} 
                                      for s, p, o in qres.graph]})

        else:
            return jsonify({'error': 'Unsupported query type'}), 400

    except Exception as e:
        logging.exception("Error processing query")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)
