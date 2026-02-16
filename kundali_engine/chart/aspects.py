ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
}

def get_aspects(planet_name, house):
    return [(house + d - 1) % 12 + 1 for d in ASPECTS.get(planet_name, [])]
