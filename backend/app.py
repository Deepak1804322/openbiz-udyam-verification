from flask import Flask, jsonify, request, send_from_directory, abort
import os, json, re, sqlite3
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, insert

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR.parent / 'frontend_dist' / 'udyam_schema.json'
if not SCHEMA_PATH.exists():
    # fallback sample schema
    SCHEMA = {
      "source_url": "local",
      "extracted_on": "",
      "steps": [
        {"heading":"Aadhaar & OTP","fields":[
          {"tag":"input","id":"aadhaar","name":"aadhaar","type":"text","placeholder":"Enter Aadhaar","label":"Aadhaar Number","required":True,"maxlength":"12","inferred_validation":{"pattern":"^\\d{12}$","description":"Aadhaar 12 digits"}},
          {"tag":"input","id":"otp","name":"otp","type":"text","placeholder":"Enter OTP","label":"OTP","required":True,"maxlength":"6","inferred_validation":{"pattern":"^\\d{4,6}$","description":"OTP 4-6 digits"}}
        ]},
        {"heading":"PAN Validation","fields":[
          {"tag":"input","id":"pan","name":"pan","type":"text","placeholder":"Enter PAN","label":"PAN Number","required":True,"maxlength":"10","inferred_validation":{"pattern":"^[A-Z]{5}[0-9]{4}[A-Z]{1}$","description":"PAN format"}}
        ]}
      ]
    }
else:
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as fh:
        SCHEMA = json.load(fh)

app = Flask(__name__, static_folder=str(BASE_DIR.parent / 'frontend_dist'), static_url_path='')

# setup sqlite via SQLAlchemy engine for simplicity
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite+pysqlite:///{BASE_DIR / 'dev.db'}")
engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()
submissions = Table('submissions', metadata,
                    Column('id', Integer, primary_key=True, autoincrement=True),
                    Column('data', Text, nullable=False))
metadata.create_all(engine)

@app.get('/schema')
def get_schema():
    return jsonify(SCHEMA)

@app.post('/submit')
def submit():
    payload = request.get_json() or {}
    data = payload.get('payload') or {}
    errors = []
    # validate based on SCHEMA
    for step in SCHEMA.get('steps', []):
        for f in step.get('fields', []):
            name = f.get('name') or f.get('id')
            if not name:
                continue
            required = f.get('required', False)
            val = data.get(name)
            if required and (val is None or str(val).strip()==''):
                errors.append(f"{name} is required")
            inferred = f.get('inferred_validation')
            if val and inferred and inferred.get('pattern'):
                pattern = inferred['pattern']
                try:
                    if not re.fullmatch(pattern, str(val)):
                        errors.append(f"{name} failed pattern {pattern}")
                except re.error:
                    pass
    if errors:
        return jsonify({'errors': errors}), 400
    # save into DB
    with engine.begin() as conn:
        res = conn.execute(insert(submissions).values(data=json.dumps(data)))
        new_id = res.inserted_primary_key[0]
    return jsonify({'ok': True, 'id': new_id})

# serve index.html and static files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    file_path = Path(app.static_folder) / filename
    if file_path.exists():
        return send_from_directory(app.static_folder, filename)
    abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
