import sqlite3
c=sqlite3.connect('backend/data/learnmate.db')
for name,sql in c.execute("select name,sql from sqlite_master where type='table'"):
    if any(x in name for x in ('profile','chat','path')):
        print(name, sql)
for username in ('learner_a','learner_b','learner_c'):
    row=c.execute("select lp.* from learner_profiles lp join users u on u.id=lp.user_id where u.username=?",(username,)).fetchone()
    print(username, row)
