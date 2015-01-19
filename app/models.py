import json

from app import db
from exceptions import PasswordNotProvidedError, UsernameNotProvidedError
from utils import generate_hash, generate_salt, get_now, shuffle

class UserAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password_hash = db.Column(db.LargeBinary)
    password_salt = db.Column(db.LargeBinary)

    poll_collections = db.relationship('PollCollection', backref='author')

    def __init__(self, username, password):

        if not username:
            raise UsernameNotProvidedError
        
        if not password:
            raise PasswordNotProvidedError

        try:
            password = bytes(password)
        except UnicodeEncodeError:
            raise

        self.username = username
        self.password_salt = generate_salt()
        self.password_hash = generate_hash(password, self.password_salt)


    def __repr__(self):
        return '<UserAccount %r>' % self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class PollCollection(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    counted = db.Column(db.Boolean, default=False)

    polls = db.relationship('Poll', backref='collection', order_by='Poll.poll_num')
    votes = db.relationship('PollCollectionVote')

    author_id = db.Column(db.Integer, db.ForeignKey('user_account.id'))

    def __repr__(self):
        return '<PollCollection %r>' % self.id

    def is_finished(self):
        return self.end < get_now()

    def count_votes(self):
        for poll in self.polls:
            poll.count_votes()

        self.counted = True
        db.session.add(self)
        db.session.commit()


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String)
    poll_num = db.Column(db.Integer)

    candidates = db.relationship('Candidate',
                                 backref='poll',
                                 order_by='Candidate.candidate_num')
    result = db.relationship('PollResult')
    votes = db.relationship('PollVote')

    collection_id = db.Column(db.Integer, db.ForeignKey('poll_collection.id'))

    def __repr__(self):
        return '<Poll %r>' % self.id

    def count_votes(self):
        pvs = [ v for v in self.votes if v.collection.cast ]

        result = []

        while pvs:
            cur_result = { can.id: 0 for can in self.candidates }
            for pv in pvs:
                if len(pv.choices):
                    cur_result[pv.choices[0].candidate_id] += 1
            result.append(cur_result)
            majority_size = len(pvs)/2
            if any([ n > majority_size for n in cur_result.values() ]):
                break
            min_votes = min(cur_result.values())
            least_popular = [ can_id for can_id in cur_result
                                     if cur_result[can_id] == min_votes ]
            del_buffer = []
            for i, pv in enumerate(pvs):
                inner_del_buffer = []
                for choice in pv.choices:
                    for lp in least_popular:
                        if lp == choice.candidate_id:
                            inner_del_buffer.append(choice)
                for choice in inner_del_buffer:
                    pv.choices.remove(choice)
                if not pv.choices:
                    del_buffer.append(i)
            del_buffer.reverse()
            for i in del_buffer:
                del pvs[i]

        pr = PollResult(poll_id=self.id, result=result)

        db.session.add(pr)
        db.session.commit()

    def shuffle_candidates():
        utils.shuffle(self.candidates)


class PollResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.String)

    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))

    def __init__(self, poll_id=None, result=None):
        self.poll_id = poll_id
        self.result = json.dumps(result)

    def get_result(self):
        return json.loads(self.result)

    def set_result(self, result):
        self.result = json.dumps(result)

    def __repr__(self):
        return '<PollResult %r>' % self.id


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    candidate_num = db.Column(db.Integer)

    votes = db.relationship('PollVoteChoice', backref='choice')

    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))

    def __repr__(self):
        return '<Candidate %r>' % self.id


class PollCollectionVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uvc = db.Column(db.String)
    cast = db.Column(db.Boolean)

    poll_votes = db.relationship('PollVote', backref='collection')

    collection_id = db.Column(db.Integer, db.ForeignKey('poll_collection.id'))

    def __repr__(self):
        return '<PollCollectionVote %r>' % self.id


class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    choices = db.relationship('PollVoteChoice',
                              backref='poll',
                              order_by='PollVoteChoice.preference')

    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    pollcollvote_id = db.Column(db.Integer,
                                db.ForeignKey('poll_collection_vote.id'))

    def __repr__(self):
        return '<PollVote %r>' % self.id


class PollVoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    preference = db.Column(db.Integer)
    pollvote_id = db.Column(db.Integer, db.ForeignKey('poll_vote.id'))

    def __repr__(self):
        return '<PollVoteChoice %r>' % self.id
