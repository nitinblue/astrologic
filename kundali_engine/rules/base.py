class Rule:
    def applies(self, kundali, time_context):
        raise NotImplementedError

    def score(self, kundali, time_context):
        raise NotImplementedError
