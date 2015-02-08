from functools import partial

from flask import redirect, render_template, request, url_for, make_response
from flask.ext.login import (login_user, logout_user, current_user,
    login_required)
from sqlalchemy.exc import IntegrityError

from app import app, db, lm
from exceptions import PasswordNotProvidedError, UsernameNotProvidedError
from models import (UserAccount, PollCollection, Poll, Candidate,
    PollCollectionVote, PollVote, PollVoteChoice)
from utils import (parseDatetime, generate_uvc, get_now, generate_salt,
    generate_hash)


@lm.user_loader
def load_user(id):
    return UserAccount.query.get(int(id))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        render = partial(render_template, 'index.html')

        uvc = request.form.get('uvc')

        if not uvc:
            return render(error='No UVC entered')

        uvc = uvc.upper()

        pcv = PollCollectionVote.query.filter(
            PollCollectionVote.uvc == uvc).first()

        if not pcv:
            return render(error='UVC does not exist')

        pc = PollCollection.query.get(pcv.collection_id)

        # Check that the poll is currently open
        now = get_now()
        if now < pc.start:
            return render(error='Voting for this poll has not started yet')
        elif pc.end < now:
            return render(error='Voting for this poll has closed')

        ps = pc.polls
        for p in ps:
            p.shuffle_candidates()

        return render_template('vote.html', uvc=uvc, pc=pc)


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

    pvs = [ PollVote(poll_id=p.id,
                     pollcollvote_id=pcv.id)
            for p in ps ]
    db.session.add_all(pvs)
    db.session.commit()

    css = [ p.candidates for p in ps ]

    pvcs = [ PollVoteChoice(candidate_id=css[poll_num][can_num].id,
                            preference=preference,
                            pollvote_id=pvs[poll_num].id)
             for poll_num in range(num_polls)
             for preference,can_num in enumerate(choices[poll_num]) ]
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
        render = partial(render_template, 'signup.html')
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = UserAccount(username=username, password=password)
        except UsernameNotProvidedError:
            return render(error='No username provided')
        except PasswordNotProvidedError:
            return render(error='Password not provided',
                          username=username)
        except UnicodeEncodeError:
            return render(error='Invalid characters used in password',
                          username=username)

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render(error='Username is already in use',
                          username=username)
        else:
            login_user(user)
            return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        render = partial(render_template, 'login.html')

        username = request.form.get('username')
        if not username:
            return render(error='No username provided')

        render_u = partial(render, username=username)

        user = UserAccount.query.filter(UserAccount.username==username).first()
        if not user:
            return render_u(error='Username does not exist')

        password = request.form.get('password')
        if not password:
            return render_u(error='No password entered')

        try:
            password = bytes(password)
        except UnicodeEncodeError:
            return render_u(error='Invalid characters used in password')

        password_salt = user.password_salt
        password_hash = generate_hash(password, password_salt)

        if password_hash != user.password_hash:
            return render_u(error='Password for this username is incorrect')

        login_user(user)
        next = request.args.get('next')
        return redirect(next) if next else redirect(url_for('index'))


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
        title = data.get('title')
        num_votes = data.get('numVotes')
        start = data.get('start')
        end = data.get('end')

        num_polls = len(polls)

        pc = PollCollection(title=title,
                            start=parseDatetime(start),
                            end=parseDatetime(end),
                            author_id=current_user.id)
        db.session.add(pc)
        db.session.commit()

        # Generate UVCs
        pcvs = [ PollCollectionVote(uvc=generate_uvc(),
                                    cast=False,
                                    collection_id=pc.id)
                 for i in range(num_votes) ]
        db.session.add_all(pcvs)
        db.session.commit()

        ps = [ Poll(question=poll['question'],
                    collection_id=pc.id,
                    poll_num=poll_num)
               for poll_num,poll in enumerate(polls) ]
        db.session.add_all(ps)
        db.session.commit()

        cs = [ Candidate(text=can,
                         poll_id=ps[poll_num].id,
                         candidate_num=can_num)
               for poll_num,poll in enumerate(polls)
               for can_num,can in enumerate(poll['candidates']) ]
        db.session.add_all(cs)
        db.session.commit()

        return ('', 204)


@app.route('/manage_polls', methods=['GET'])
@login_required
def manage_polls():
    pcs = (PollCollection.query
          .filter(PollCollection.author == current_user)
          .order_by(PollCollection.start.desc())
          )
    return render_template('manage_polls.html', pcs=pcs)


@app.route('/uvcs')
@login_required
def view_uvcs():
    pc_id = request.args.get('pc')
    print pc_id

    try:
        pc_id = int(pc_id)
    except ValueError:
        return ('', 404)

    pc = PollCollection.query.get(pc_id)
    pcvs = pc.votes
    uvcs = [ pcv.uvc for pcv in pcvs ]
    return render_template('uvcs.html', uvcs=uvcs)


@app.route('/count_votes', methods=['POST'])
@login_required
def count_votes():
    pc_id = request.form.get('pcId')
    
    if not pc_id:
        return ('', 204)

    pc = PollCollection.query.get(pc_id)
    pc.count_votes()

    app.logger.debug(pc_id)

    return ('', 204)
