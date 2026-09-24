from datetime import datetime, timezone


def event(text='Fix retry after request timeout', platform='github'):
    return {'id': 'record-1', 'platform': platform, 'author': 'author-1', 'text': text,
            'url': 'https://github.com/example/project/commit/' + 'a' * 40,
            'observed_at': datetime.now(timezone.utc).isoformat(), 'context': []}


class Backend:
    def __init__(self, choice='keep', chance=.95):
        self.choice, self.chance, self.calls = choice, chance, 0
        self.inputs = []

    def manifest(self):
        return {'contract_test_backend': 1, 'choice': self.choice, 'chance': self.chance}

    def __call__(self, state, questions):
        self.calls += 1
        self.inputs.append(state)
        return {'answers': {'signal': {'type': 'choice', 'choice': self.choice,
                'probabilities': {key: self.chance if key == self.choice else 1 - self.chance for key in ('keep', 'noise')}}}}
