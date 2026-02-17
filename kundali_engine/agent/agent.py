"""
AstroLogic Agent — transport-agnostic conversational core.

Usage:
    agent = AstroAgent()
    response = agent.handle("show my chart", session_id="cli")

The same agent instance works for CLI, Flask, WhatsApp — only the
transport layer changes. Session state is keyed by session_id.
"""

import re
from kundali_engine.agent import handlers

# ── Intent patterns (most specific first) ──────────────────────────────────

INTENT_PATTERNS = [
    ("create_chart",   r"(?:create|add|make|new|generate)\b.*(?:kundali|chart|horoscope|birth)"),
    ("show_chart",     r"(?:show|display|view|see|open)\b.*(?:chart|kundali|horoscope|planets)"),
    ("list_people",    r"(?:list|who all|show all|everyone|all people|all charts|who do you)"),
    ("dasha_info",     r"(?:dasha|period|mahadasha|antardasha|current period)"),
    ("sector_advice",  r"(?:sector|gold|silver|crude|commodity|nifty|bank.?nifty|metal)"),
    ("trading_regime", r"(?:trad|market|regime|should i (?:buy|sell|trade)|stock)"),
    ("today_guidance", r"(?:today|daily|guidance|how.?s today|what should|good day|bad day)"),
    ("planet_info",    r"(?:tell me about|what is|explain|about)\s+(?:sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)"),
    ("compare",        r"(?:compare|compatibility|match)"),
    ("switch_person",  r"(?:switch|set me as|use|change to|select)\b.*(?:person|chart|\w+)"),
    ("rate",           r"(?:rate|rating|stars?|thumbs|helpful|not helpful|good answer|bad answer|\b[1-5]\s*(?:star|out of))"),
    ("help",           r"(?:help|what can you|commands|menu|options|capabilities)"),
    ("greeting",       r"(?:^hi$|^hello|^hey|^namaste|^good\s*(?:morning|evening|afternoon))"),
    # interpret is the catch-all for any chart-based question — MUST be last
    ("interpret",      r"(?:what (?:does|is|are|should|would|can|will)|how (?:does|will|should|would|can|do)|universe|traits?|strengths?|weaknesses?|spirit|karma|personality|impact|prepare|affect|leverage|avoid|improve|career|job|health|wealth|money|relationship|marriage|invest|property|real estate|children|education|purpose|emotion|anxiety|stress|depress|fear|courage|business|who am i|tell me about my|my strengths|my weaknesses|my personality|my career|my health)"),
]


def _make_session(session_id):
    """Create a fresh session dict."""
    return {
        "session_id": session_id,
        "active_person_id": 1,        # default: Nitin (first person)
        "active_person_name": None,    # lazy-loaded on first use
        "flow": None,                  # current multi-step flow name
        "flow_data": {},               # partial data for incomplete flow
    }


class AstroAgent:
    """Transport-agnostic conversational agent for Vedic astrology."""

    def __init__(self):
        self.sessions = {}

    def _get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = _make_session(session_id)
        return self.sessions[session_id]

    # ── Public entry point ──────────────────────────────────────────────

    def handle(self, message, session_id="cli"):
        """
        Process one user message and return a response string.

        Parameters
        ----------
        message : str
            Raw user input.
        session_id : str
            Unique session key.  CLI uses "cli", WhatsApp could use
            the phone number, web could use a cookie/token.

        Returns
        -------
        str   Plain-text response (works in any transport).
        """
        session = self._get_session(session_id)
        message = message.strip()

        if not message:
            return "I didn't catch that. Type 'help' to see what I can do."

        # If we're mid-flow (e.g. multi-step chart creation), stay there
        if session["flow"]:
            return self._continue_flow(message, session)

        # Detect intent and route
        intent = self._detect_intent(message)
        return self._route(intent, message, session)

    # ── Intent detection ────────────────────────────────────────────────

    def _detect_intent(self, message):
        msg_lower = message.lower().strip()
        for intent, pattern in INTENT_PATTERNS:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return intent
        return "unknown"

    # ── Routing ─────────────────────────────────────────────────────────

    def _route(self, intent, message, session):
        route_map = {
            "greeting":       handlers.handle_greeting,
            "help":           handlers.handle_help,
            "create_chart":   handlers.handle_create_chart,
            "show_chart":     handlers.handle_show_chart,
            "list_people":    handlers.handle_list_people,
            "dasha_info":     handlers.handle_dasha_info,
            "today_guidance": handlers.handle_today_guidance,
            "trading_regime": handlers.handle_trading_regime,
            "sector_advice":  handlers.handle_sector_advice,
            "planet_info":    handlers.handle_planet_info,
            "switch_person":  handlers.handle_switch_person,
            "compare":        handlers.handle_compare,
            "interpret":      handlers.handle_interpret,
            "rate":           handlers.handle_rate,
        }
        handler = route_map.get(intent)
        if handler:
            return handler(message, session)

        return (
            "I'm not sure what you mean. Here's what I can help with:\n\n"
            + handlers.HELP_TEXT
        )

    # ── Multi-step flow continuation ────────────────────────────────────

    def _continue_flow(self, message, session):
        if message.lower() in ("cancel", "stop", "nevermind", "quit flow"):
            session["flow"] = None
            session["flow_data"] = {}
            return "Cancelled. What else can I help with?"

        if session["flow"] == "create_chart":
            return handlers.continue_create_chart_flow(message, session)

        # Unknown flow — reset
        session["flow"] = None
        session["flow_data"] = {}
        return "Something went wrong. Let's start fresh. Type 'help' for options."
