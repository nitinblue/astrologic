class Evaluator:
    def __init__(self, rules):
        self.rules = rules

    def evaluate(self, kundali, time):
        scores = []
        for rule in self.rules:
            if rule.applies(kundali, time):
                scores.append(rule.score(kundali, time))
        return sum(scores) / len(scores) if scores else 0
