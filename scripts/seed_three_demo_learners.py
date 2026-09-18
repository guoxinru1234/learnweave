import json, sqlite3
from datetime import datetime, timedelta

DB='backend/data/learnmate.db'
profiles={
'learner_a':{'scores':[24,20,18,16,22,28],'pace':'慢速','style':'图解与分步演示型','motivation':'建立 Python 数据分析基础','domains':{'python_syntax':32,'numpy':18,'pandas':15,'data_cleaning':14,'visualization':20,'statistics':16,'data_thinking':22,'machine_learning':8,'performance':6,'deployment':5},'weak':['Python语法','NumPy基础','Pandas基础'],'strong':['学习意愿'],'goal':'从零掌握 Python 数据分析基础'},
'learner_b':{'scores':[58,55,50,46,60,62],'pace':'中速','style':'示例与实践结合型','motivation':'补齐数据处理短板','domains':{'python_syntax':68,'numpy':55,'pandas':52,'data_cleaning':48,'visualization':60,'statistics':54,'data_thinking':62,'machine_learning':42,'performance':38,'deployment':35},'weak':['Pandas分组','缺失值处理','排错'],'strong':['Python基础','数据思维'],'goal':'完成中等难度数据分析项目'},
'learner_c':{'scores':[88,90,86,84,89,92],'pace':'快速','style':'项目挑战与自主探索型','motivation':'提升建模、优化与部署能力','domains':{'python_syntax':94,'numpy':90,'pandas':92,'data_cleaning':88,'visualization':86,'statistics':84,'data_thinking':91,'machine_learning':82,'performance':78,'deployment':74},'weak':['性能调优','模型部署'],'strong':['编程实践','数据分析','自主学习'],'goal':'完成高阶项目与生产部署'},
}
questions=['你之前接触过 Python 或数据分析吗？','遇到一段 Python 代码时，你通常能独立读懂到什么程度？','你是否使用过 NumPy 和 Pandas 处理数据？','遇到报错时你通常如何定位问题？','你更喜欢怎样的学习节奏和讲解方式？','你希望通过这门课程达到什么目标？']
answers={
'learner_a':['几乎没有接触过，只看过少量入门内容。','简单的 print 能看懂，循环和函数还比较陌生。','没有实际用过，不清楚数组和 DataFrame 的区别。','通常不知道从哪里开始，希望能逐行提示。','希望慢一点，多用图解和分步骤代码。','先能独立完成基础的数据读取、清洗和简单分析。'],
'learner_b':['学过 Python 基础，能完成简单脚本。','常见语法能读懂，复杂函数需要结合示例。','使用过基础操作，但分组、缺失值和索引容易出错。','会看报错位置，但对类型和数据形状问题定位较慢。','喜欢先看示例，再自己完成练习。','希望完成一个完整的中等难度数据分析项目。'],
'learner_c':['有较多 Python 项目经验，也做过数据分析。','能快速理解模块化代码并进行重构。','熟练使用 NumPy、Pandas，也能优化常见处理流程。','会通过最小复现、日志和性能分析定位问题。','偏好快速学习、项目挑战和自主探索。','希望提升机器学习、性能优化与部署能力。']}

c=sqlite3.connect(DB)
now=datetime.now()
for username,p in profiles.items():
    uid=c.execute('select id from users where username=?',(username,)).fetchone()[0]
    history=[{'role':'system','content':'演示数据：由系统模拟不同学习者完成画像评估。'}]
    for q,a in zip(questions,answers[username]): history += [{'role':'assistant','content':q},{'role':'user','content':a}]
    s=p['scores']; desc=['基础知识掌握情况','代码理解与编写能力','数据处理实践能力','错误定位能力','数据分析思维','自主学习能力']
    c.execute('''INSERT INTO learner_profiles(user_id,major_background,theoretical_basis,coding_ability,practical_ops,troubleshooting,data_thinking,self_learning,theory_description,coding_description,practice_description,debug_description,data_description,self_learning_description,cognitive_style,learning_pace,learning_motivation,dialogue_step,dialogue_completed,dialogue_history,updated_at,domain_skills) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET major_background=excluded.major_background,theoretical_basis=excluded.theoretical_basis,coding_ability=excluded.coding_ability,practical_ops=excluded.practical_ops,troubleshooting=excluded.troubleshooting,data_thinking=excluded.data_thinking,self_learning=excluded.self_learning,theory_description=excluded.theory_description,coding_description=excluded.coding_description,practice_description=excluded.practice_description,debug_description=excluded.debug_description,data_description=excluded.data_description,self_learning_description=excluded.self_learning_description,cognitive_style=excluded.cognitive_style,learning_pace=excluded.learning_pace,learning_motivation=excluded.learning_motivation,dialogue_step=excluded.dialogue_step,dialogue_completed=excluded.dialogue_completed,dialogue_history=excluded.dialogue_history,updated_at=excluded.updated_at,domain_skills=excluded.domain_skills''',(uid,'Python数据分析演示学习者',*s,*[f'{x}：{v}分（模拟评估）' for x,v in zip(desc,s)],p['style'],p['pace'],p['motivation'],6,1,json.dumps(history,ensure_ascii=False),now.isoformat(),json.dumps(p['domains'],ensure_ascii=False)))
    session=f'demo-profile-{username}'
    c.execute('delete from chat_history where user_id=? and session_id=?',(uid,session))
    for i,msg in enumerate(history): c.execute('insert into chat_history(user_id,session_id,role,content,created_at) values(?,?,?,?,?)',(uid,session,msg['role'],msg['content'],(now+timedelta(seconds=i)).isoformat()))
    c.execute('''INSERT INTO user_profiles(user_id,strong_topics,weak_topics,improvement_goals,has_completed_guide) VALUES(?,?,?,?,1) ON CONFLICT(user_id) DO UPDATE SET strong_topics=excluded.strong_topics,weak_topics=excluded.weak_topics,improvement_goals=excluded.improvement_goals,has_completed_guide=1,updated_at=CURRENT_TIMESTAMP''',(uid,json.dumps(p['strong'],ensure_ascii=False),json.dumps(p['weak'],ensure_ascii=False),json.dumps([p['goal'],'[模拟演示数据]'],ensure_ascii=False)))
c.commit()
print('seeded learner_a, learner_b, learner_c')
