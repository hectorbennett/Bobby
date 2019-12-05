import json
import random
import html
from urllib.request import urlopen

class Quiz(object):

    def __init__(self, rounds=10, difficulty='medium'):
        self.player_results = {}
        self.rounds = rounds
        self.difficulty = difficulty
        self.current_round = 0
        self.questions = self.get_questions()
        self.finished = False

    def get_questions(self):
        url = 'https://opentdb.com/api.php?amount={}&difficulty={}&type=multiple'.format(
            self.rounds, self.difficulty
        )
        data = json.loads(urlopen(url).read().decode('utf8'))
        questions = []
        for result in data['results']:
            questions.append(Question(
                html.unescape(result['question']),
                html.unescape(result['correct_answer']),
                [html.unescape(x) for x in result['incorrect_answers']]
            ))
        return questions

    @property
    def current_scores(self):
        y = sorted(self.player_results.items(), key=lambda x: x[1], reverse=True)
        s = 'Scores:\n'
        for user_id, score in y:
            s += '{}: {}\n'.format(user_id, score)
        return s

    def next_round(self):
        self.current_round += 1
        if self.current_round == self.rounds:
            self.finished=True
            return

    @property
    def current_question(self):
        if self.current_round == self.rounds:
            return 'Fin!'
        s = 'ROUND: {}\n'.format(self.current_round + 1)
        s += str(self.questions[self.current_round])
        return s

    def make_attempt(self, user_id, attempt):
        attempt = attempt.upper().strip()
        if attempt == self.questions[self.current_round].correct_answer:
            self.correct(user_id)
            self.next_round()
            return """{}
            {}

            {}
            """.format('Yes!!', self.current_scores, self.current_question)
        else:
            self.incorrect(user_id)
            return """{}
            {}
            """.format('Nope!', self.current_scores)
        return self.current_scores

    def correct(self, user_id):
        try:
            self.player_results[user_id] += 1
        except KeyError:
            self.player_results[user_id] = 1

    def incorrect(self, user_id):
        try:
            self.player_results[user_id]
        except KeyError:
            self.player_results[user_id] = 0


class Question(object):

    def __init__(self, question, correct_answer, incorrect_answers):
        self.question = question
        self.answers = [correct_answer] + incorrect_answers
        random.shuffle(self.answers)
        self.answers = {
            'A': self.answers[0],
            'B': self.answers[1],
            'C': self.answers[2],
            'D': self.answers[3]
        }
        for answer in self.answers:
            if self.answers[answer] == correct_answer:
                self.correct_answer = answer

    def __str__(self):
        return """{}
            A: {}
            B: {}
            C: {}
            D: {}
        """.format(
            self.question,
            self.answers['A'],
            self.answers['B'],
            self.answers['C'],
            self.answers['D'],
        )


if __name__ == 'main':
    quiz = Quiz(rounds=10)
    quiz.start()
    while True:
        attempt = input('...')
        quiz.make_attempt(random.choice(['Hector', 'Irina', 'Rich']), attempt)
        if quiz.finished:
            break