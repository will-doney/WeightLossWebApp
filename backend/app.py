from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows frontend to access backend

@app.route('/')
def home():
    return "Flask backend is running!"

@app.route('/api/tasks')
def get_tasks():
    tasks = [
        {"id": 1, "task": "10-minute walk"},
        {"id": 2, "task": "Drink 2 liters of water"},
        {"id": 3, "task": "Stretch for 5 minutes"},
    ]
    return jsonify(tasks)

if __name__ == '__main__':
    app.run(debug=True)
