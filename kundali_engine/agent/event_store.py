"""
Event sourcing for agent interactions.

Every interaction is logged as an immutable event. User feedback
drives RL-based variant selection in the interpreter.
"""
import json
from kundali_engine.core.database.connection import get_connection


def log_event(session_id, person_id, question, intent, themes=None,
              planets=None, houses=None, chart_snapshot=None,
              variants_used=None, response=None):
    """Append one event to event_log. Returns event_id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO event_log
               (session_id, person_id, raw_question, detected_intent,
                detected_themes, planets_involved, houses_involved,
                chart_snapshot, variants_used, response_text)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id,
                person_id,
                question,
                intent,
                json.dumps(themes) if themes else None,
                json.dumps(planets) if planets else None,
                json.dumps(houses) if houses else None,
                json.dumps(chart_snapshot) if chart_snapshot else None,
                json.dumps(variants_used) if variants_used else None,
                response,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def log_feedback(event_id, rating, feedback=None):
    """Record user rating for an event."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO event_feedback (event_id, rating, feedback)
               VALUES (?,?,?)""",
            (event_id, rating, feedback),
        )
        conn.commit()
    finally:
        conn.close()


def get_variant_scores(planet, key, key_type="house"):
    """
    Get average rating per variant_id for a planet+house or planet+theme combo.

    Returns dict: {variant_id: avg_rating}
    """
    conn = get_connection()
    try:
        if key_type == "house":
            like_pattern = f'%"planet": "{planet}"%"house": {key}%'
        else:
            like_pattern = f'%"planet": "{planet}"%"theme": "{key}"%'

        rows = conn.execute(
            """SELECT j.value AS variant_json, AVG(ef.rating) AS avg_rating,
                      COUNT(ef.rating) AS cnt
               FROM event_log el
               JOIN event_feedback ef ON ef.event_id = el.id
               JOIN json_each(el.variants_used) j
               WHERE j.value LIKE ?
               GROUP BY j.value
               HAVING cnt >= 2""",
            (like_pattern,),
        ).fetchall()

        scores = {}
        for row in rows:
            try:
                v = json.loads(row["variant_json"])
                scores[v.get("variant_id", 1)] = row["avg_rating"]
            except (json.JSONDecodeError, TypeError):
                continue
        return scores
    finally:
        conn.close()


def get_last_event_id(session_id):
    """Get the most recent event_id for a session (for rating)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM event_log WHERE session_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def get_person_history(person_id, limit=50):
    """Recent events for a person — for context/continuity."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM event_log WHERE person_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (person_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
