def assign_houses(lagna_sign: str) -> dict:
    signs = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ]
    start = signs.index(lagna_sign)
    return {i+1: signs[(start+i)%12] for i in range(12)}
