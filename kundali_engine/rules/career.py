from kundali_engine.rules.base import Rule

class SaturnCareerRule(Rule):
    def applies(self, kundali, time):
        saturn = kundali.get_planet("Saturn")
        return saturn and saturn.house == 10

    def score(self, kundali, time):
        return 0.8
