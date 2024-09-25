from flask import Flask, render_template, request, redirect, url_for, session
import cohere  # Import Cohere's Python client
import sqlite3

# Initialize Flask app
app = Flask(__name__)
app.secret_key = '61fd78be9c03ca2319dde75831e4f33b'

# Set your Cohere API key
cohere_api_key = 'VIIgvUdK6kcUYD55qo0b2W0AYQKrotu8b7PrCS7o'
co = cohere.Client(cohere_api_key)

# Database setup (Optional)
def init_db():
    conn = sqlite3.connect('budgets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            lumpsum TEXT NOT NULL,
            budget TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Route to the input form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form['description']
        lumpsum = request.form['lumpsum']
        priorities = request.form['priorities']
        
        # Generate budget using Cohere API
        budget = generate_budget(description, lumpsum, priorities)
        
        # Store input in session for editing later
        session['description'] = description
        session['lumpsum'] = lumpsum
        session['priorities'] = priorities

        # Optionally store budget in the database
        store_budget(description, lumpsum, budget)
        
        # Redirect to the budget display page
        return redirect(url_for('show_budget', budget=budget))
    
    return render_template('index.html')

# Route to display the generated budget
@app.route('/budget')
def show_budget():
    budget = request.args.get('budget')
    return render_template('budget.html', budget=budget)

# Route to edit inputs (uses session data)
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        # Update session values with new input
        session['description'] = request.form['description']
        session['lumpsum'] = request.form['lumpsum']
        session['priorities'] = request.form['priorities']
        
        # Regenerate budget
        budget = generate_budget(session['description'], session['lumpsum'], session['priorities'])
        store_budget(session['description'], session['lumpsum'], budget)
        return redirect(url_for('show_budget', budget=budget))

    # Pre-fill form with previous input (from session)
    return render_template('edit.html', 
                           description=session.get('description', ''), 
                           lumpsum=session.get('lumpsum', ''), 
                           priorities=session.get('priorities', ''))

# Function to generate the budget using Cohere
def generate_budget(description, lumpsum, priorities):
    prompt = f"""
    Create a personalized weekly budget for a user with an estimated expenditure of {lumpsum} rupees.
    The user describes their spending habits as follows: {description}. 
    Their spending priorities include: {priorities}.
    Categorize the spending into appropriate sections like food, transportation, entertainment, etc., 
    and account for any potential biases in their description. The budget should be divided accordingly and no budget should be left unallocated.
    Also make sure the total money spend equals to the {lumpsum}
    """
    
    # Use Cohere to generate the budget
    response = co.generate(
        model='command-light',  # You can adjust the model size as per your needs
        prompt=prompt,
        max_tokens=500,
        temperature=0.7
    )
    
    # Extract the generated text
    budget = response.generations[0].text.strip()
    return budget

# Store budget into SQLite (Optional)
def store_budget(description, lumpsum, budget):
    conn = sqlite3.connect('budgets.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO budgets (description, lumpsum, budget) 
        VALUES (?, ?, ?)
    ''', (description, lumpsum, budget))
    conn.commit()
    conn.close()

# Initialize database (Optional)
init_db()

if __name__ == '__main__':
    app.run(debug=True)
