# Shared loaders. Everything reads from ../data so the repo runs from anywhere.
import os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
RESULTS = os.path.join(HERE, '..', 'results')
os.makedirs(RESULTS, exist_ok=True)


def read(name, folder='data'):
    with open(os.path.join(DATA if folder == 'data' else RESULTS, name)) as f:
        return [r for r in csv.DictReader(l for l in f if not l.startswith('#'))]


def num(x):
    return float(x) if x not in ('', None) else None


def market():
    return {r['item']: float(r['value']) for r in read('market.csv')}


def save(name, text):
    with open(os.path.join(RESULTS, name), 'w') as f:
        f.write(text)
    print(text)
