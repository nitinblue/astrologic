class Kundali:
    def __init__(self, birth_data, lagna, planets, houses):
        self.birth_data = birth_data
        self.lagna = lagna
        self.planets = planets
        self.houses = houses

    def get_planet(self, name):
        return self.planets.get(name)
