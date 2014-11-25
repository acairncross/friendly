from flask import redirect, render_template, request, url_for
from flask.ext.login import (login_user, logout_user, current_user,
    login_required)
from app import app, db, lm
from models import UserAccount, PollCollection, Poll, Choice, PollCollectionVote
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
            return redirect(url_for('vote', uvc=uvc))

@app.route('/vote/<uvc>', methods=['GET'])
def vote(uvc=''):
    pcv = PollCollectionVote.query.filter(
        PollCollectionVote.uvc == uvc,
        PollCollectionVote.cast == False
    ).first()

    if not pcv:
        return redirect(url_for('index'))

    pc = PollCollection.query.get(pcv.collection_id)

    return render_template('vote.html', uvc=uvc, pc=pc)

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
        num_votes = int(request.form.get('num_votes'))
        start = request.form.get('start')
        end = request.form.get('end')
        num_polls = int(request.form.get('num_polls'))

        poll_forms = dict()

        for i in range(num_polls):
            question = request.form.get('question' + str(i))
            choices = request.form.getlist('choice' + str(i))
            if question and choices:
                poll_forms[i] = {'question': question, 'choices': choices}

        # Check if the poll has no questions
        if not poll_forms:
            pass
            
        pc = PollCollection(start=utils.parseDatetime(start),
                            end=utils.parseDatetime(end),
                            author_id=current_user.id)
        db.session.add(pc)
        db.session.commit()

        # Generate UVCs
        pcvs = [PollCollectionVote(uvc=utils.generate_uvc(),
                                   cast=False,
                                   collection_id=pc.id)
                for n in range(num_votes)]
        db.session.add_all(pcvs)
        db.session.commit()

        ps = {i: Poll(question=poll_forms[i]['question'],
                      collection_id=pc.id)
              for i in poll_forms}
        db.session.add_all(ps.values())
        db.session.commit()

        cs = [Choice(text=choice,
                     poll_id=ps[i].id)
              for i in poll_forms
              for choice in poll_forms[i]['choices']]
        db.session.add_all(cs)
        db.session.commit()

        return render_template('create_poll.html')
