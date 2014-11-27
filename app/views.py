from flask import redirect, render_template, request, url_for, make_response
from flask.ext.login import (login_user, logout_user, current_user,
    login_required)
from app import app, db, lm
from models import (UserAccount, PollCollection, Poll, Choice, PollCollectionVote,
    PollVote, PollVoteChoice)
import utils

@lm.user_loader
def load_user(id):
    return UserAccount.query.get(int(id))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        uvc = request.form.get('uvc')
        if uvc:
            return redirect(url_for('vote', uvc=uvc), code=307)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'GET':
        return render_remplate('index.html')
    elif request.method == 'POST':
        uvc = request.form.get('uvc')

        pcv = PollCollectionVote.query.filter(
            PollCollectionVote.uvc == uvc).first()

        if not pcv:
            return redirect(url_for('vote'))

        pc = PollCollection.query.get(pcv.collection_id)
        ps = pc.polls
        for p in ps:
            utils.shuffle(p.choices)

        return render_template('vote.html', uvc=uvc, ps=ps)

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    uvc = data.get('uvc')
    choices = data.get('choices')
    num_polls = len(choices)

    pcv = PollCollectionVote.query.filter(
        PollCollectionVote.uvc == uvc).first()

    pc = PollCollection.query.get(pcv.collection_id)
    ps = pc.polls

    pvs = [PollVote(poll_id=p.id,
                    pollcollvote_id=pcv.id)
           for p in ps]
    db.session.add_all(pvs)
    db.session.commit()

    css = [p.choices for p in ps]

    pvcs = [PollVoteChoice(choice_id=css[poll_num][choice_num].id,
                           preference=preference,
                           pollvote_id=pvs[poll_num].id)
            for poll_num in range(num_polls)
            for preference,choice_num in enumerate(choices[poll_num])]
    db.session.add_all(pvcs)
    db.session.commit()

    pcv.cast = True
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = UserAccount(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        user = UserAccount.query.filter(UserAccount.username==username).first()
        password = request.form.get('password')
        if password != user.password:
            return redirect(url_for('signup'))
        login_user(user)
        return redirect(url_for('index'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'GET':
        return render_template('logout.html')
    elif request.method == 'POST':
        logout_user()
        return redirect(url_for('index'))

@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    if request.method == 'GET':
        return render_template('create_poll.html')
    elif request.method == 'POST':
        data = request.get_json()

        polls = data.get('polls')
        num_votes = data.get('numVotes')
        start = data.get('start')
        end = data.get('end')

        num_polls = len(polls)

        pc = PollCollection(start=utils.parseDatetime(start),
                            end=utils.parseDatetime(end),
                            author_id=current_user.id)
        db.session.add(pc)
        db.session.commit()

        # Generate UVCs
        pcvs = [PollCollectionVote(uvc=utils.generate_uvc(),
                                   cast=False,
                                   collection_id=pc.id)
                for i in range(num_votes)]
        db.session.add_all(pcvs)
        db.session.commit()

        ps = [Poll(question=poll['question'],
                   collection_id=pc.id,
                   poll_num=poll_num)
              for poll_num,poll in enumerate(polls)]
        db.session.add_all(ps)
        db.session.commit()

        cs = [Choice(text=choice,
                     poll_id=ps[poll_num].id,
                     choice_num=choice_num)
              for poll_num,poll in enumerate(polls)
              for choice_num,choice in enumerate(poll['choices'])]
        db.session.add_all(cs)
        db.session.commit()

        return ('', 204)
