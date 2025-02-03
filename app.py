from flask import Flask, send_file, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# PostgreSQL connection string from Render
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://image_logs_db_2_user:jfKei3QhpBfcvJdalnovfssSyuzQTqUu@dpg-cugev3tumphs73cqjb40-a/image_logs_db_2")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define the Logs table
class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(500))
    email = db.Column(db.String(255))  # Store recipient's email

# Create the database tables (only needed once)
with app.app_context():
    db.create_all()

@app.route("/image")
def serve_image():
    """ Tracking pixel that logs email opens """
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    user_agent = request.headers.get("User-Agent")
    email = request.args.get("email", "unknown")  # Get recipient email from URL

    # Save log to the database
    log_entry = AccessLog(ip=ip, user_agent=user_agent, email=email)
    db.session.add(log_entry)
    db.session.commit()

    return send_file("image.jpg", mimetype="image/jpeg")

@app.route("/logs")
def view_logs():
    """ View the last 10 tracking logs """
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
    return "<br>".join([f"{log.timestamp} - {log.email} - {log.ip} - {log.user_agent}" for log in logs])

@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    """ Secure log deletion using a secret key """
    SECRET_KEY = os.getenv("test_1", "1223334444")
    key = request.args.get("key")
    
    if key != SECRET_KEY:
        return "Unauthorized!", 403

    try:
        db.session.query(AccessLog).delete()
        db.session.commit()
        return "Logs cleared successfully!"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
