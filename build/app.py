from flask import Flask

app = Flask(__name__)
@app.route("/")

def main():
    return "Hello from ECS!!7381"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)


