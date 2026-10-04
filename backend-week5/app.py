import os
import time
import logging

from flask import Flask, jsonify, request
import pymysql
import redis


app = Flask(__name__)

# -----------------------------
# Logging configuration
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)


# -----------------------------
# Environment variables
# -----------------------------
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "appdb")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_APP_PORT", "6379"))


# -----------------------------
# Database connections
# -----------------------------
def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )


# -----------------------------
# Request logging
# -----------------------------
@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def log_request(response):
    duration_ms = round(
        (time.time() - request.start_time) * 1000,
        2
    )

    logger.info(
        "method=%s path=%s status=%s response_time_ms=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms
    )

    return response


# -----------------------------
# Week 6 health endpoint
# -----------------------------
@app.route("/healthz")
def healthz():
    return jsonify({
        "status": "healthy"
    }), 200


# -----------------------------
# Existing Week 5 endpoints
# -----------------------------
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/api/dbtime")
def dbtime():
    try:
        connection = get_db()

        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW() AS db_time")
            result = cursor.fetchone()

        connection.close()

        return jsonify({
            "database": "connected",
            "db_time": str(result["db_time"])
        })

    except Exception as e:
        logger.exception("Database time request failed")

        return jsonify({
            "database": "error",
            "error": str(e)
        }), 500


@app.route("/api/visit")
def visit():
    try:
        connection = get_db()

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE statistics SET visits = visits + 1 WHERE id = 1"
            )

            connection.commit()

            cursor.execute(
                "SELECT visits FROM statistics WHERE id = 1"
            )

            result = cursor.fetchone()

        connection.close()

        return jsonify({
            "visits": result["visits"]
        })

    except Exception as e:
        logger.exception("Visit request failed")

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/status")
def status():
    try:
        connection = get_db()

        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW() AS db_time")
            time_result = cursor.fetchone()

            cursor.execute(
                "SELECT visits FROM statistics WHERE id = 1"
            )
            visit_result = cursor.fetchone()

        connection.close()

        return jsonify({
            "name": "Cloud Services App",
            "database": "connected",
            "db_time": str(time_result["db_time"]),
            "visits": visit_result["visits"]
        })

    except Exception as e:
        logger.exception("Status request failed")

        return jsonify({
            "database": "error",
            "error": str(e)
        }), 500


@app.route("/api/cache")
def cache():
    try:
        r = get_redis()

        cached_value = r.get("week5-demo")

        if cached_value:
            return jsonify({
                "redis": "connected",
                "source": "value retrieved from Redis cache",
                "value": cached_value
            })

        value = "Hello from Redis!"

        r.setex(
            "week5-demo",
            300,
            value
        )

        return jsonify({
            "redis": "connected",
            "source": "new value stored in Redis",
            "value": value
        })

    except Exception as e:
        logger.exception("Redis cache request failed")

        return jsonify({
            "redis": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000
    )