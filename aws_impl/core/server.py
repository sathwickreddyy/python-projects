from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    """
    Trigger the execution of main.py and return the output.
    """
    try:
        # Run main.py as a subprocess
        result = subprocess.run(['python3', '/home/ec2-user/main.py'], capture_output=True, text=True)
        return jsonify({
            "status": "success",
            "output": result.stdout,
            "error": result.stderr
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Start Flask server on port 80
    app.run(host='0.0.0.0', port=80)
