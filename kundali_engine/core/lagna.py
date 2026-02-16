def compute_lagna(longitude: float) -> str:
    signs = [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ]
    index = int(longitude // 30)
    return signs[index]
