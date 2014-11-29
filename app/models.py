from app import db

class UserAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password_hash = db.Column(db.LargeBinary)
    password_salt = db.Column(db.LargeBinary)
    poll_collections = db.relationship('PollCollection', backref='author')

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
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    polls = db.relationship('Poll', backref='collection', order_by='Poll.poll_num')

    def __repr__(self):
        return '<PollCollection %r>' % self.id


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String)
    collection_id = db.Column(db.Integer, db.ForeignKey('poll_collection.id'))
    poll_num = db.Column(db.Integer)
    choices = db.relationship('Choice',
                              backref='poll',
                              order_by='Choice.choice_num')

    def __repr__(self):
        return '<Poll %r>' % self.id


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    choice_num = db.Column(db.Integer)
    votes = db.relationship('PollVoteChoice', backref='choice')

    def __repr__(self):
        return '<Choice %r>' % self.id


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
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    choices = db.relationship('PollVoteChoice',
                              backref='poll',
                              order_by='PollVoteChoice.preference')
    pollcollvote_id = db.Column(db.Integer,
                                db.ForeignKey('poll_collection_vote.id'))

    def __repr__(self):
        return '<PollVote %r>' % self.id


class PollVoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    choice_id = db.Column(db.Integer, db.ForeignKey('choice.id'))
    preference = db.Column(db.Integer)
    pollvote_id = db.Column(db.Integer, db.ForeignKey('poll_vote.id'))

    def __repr__(self):
        return '<PollVoteChoice %r>' % self.id
