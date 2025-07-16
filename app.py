from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import requests

load_dotenv()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    sno = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(200),nullable = False)
    desc = db.Column(db.String(500),nullable = False)
    data_created = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"
@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo(title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()
        return redirect('/tasks')

    return render_template('index.html')
    

@app.route('/show')
def products():
    allTodo = Todo.query.all()
    print(allTodo)
    return 'this is products page'


@app.route('/update/<int:sno>',  methods=['GET', 'POST'])
def update(sno):
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo.query.filter_by(sno = sno).first()
        todo.title = title
        todo.desc = desc
        db.session.add(todo)
        db.session.commit()
        return redirect('/')

    
    todo = Todo.query.filter_by(sno = sno).first()
    return render_template('update.html', todo = todo)

@app.route('/tasks')
def all_tasks():
    query = request.args.get('query', '').strip()
    if query:
        allTodo = Todo.query.filter(Todo.title.ilike(f'%{query}%')).all()
    else:
        allTodo = Todo.query.all()
    return render_template('myTasks.html', allTodo=allTodo, query=query)


@app.route('/view/<int:sno>')
def view(sno):
    todo = Todo.query.get_or_404(sno)
    return render_template('view.html', todo=todo)

@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno = sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect('/tasks')

@app.route('/summarise/<int:sno>')
def summarise(sno):
    todo = Todo.query.get_or_404(sno)
    long_desc = todo.desc

    prompt = f"""Summarize the following task description in 1-2 sentences:\n\n\"\"\"{long_desc}\"\"\"\n\nSummary:"""

    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # set this in your .env

    try:
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes task descriptions clearly."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 150
            },
        )

        result = response.json()
        summary = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        summary = "Failed to generate summary: " + str(e)

    return render_template('view.html', todo=todo, summary=summary)
   


if __name__ == "__main__":
    app.run(debug=False, port=5000) 
