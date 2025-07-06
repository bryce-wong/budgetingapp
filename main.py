from flask import Flask, request, render_template_string
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Expense Tracker</title>
    <style>
        body { font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        input { width: 100%; padding: 8px; margin-top: 5px; }
        button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
        .success { color: green; margin-top: 10px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #4CAF50; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Add Expense</a>
        <a href="/stats">View Stats</a>
    </div>
    <h2>Add Expense</h2>
    <form method="POST">
        <div class="form-group">
            <label>Item:</label>
            <input type="text" name="item" required>
        </div>
        <div class="form-group">
            <label>Category:</label>
            <input type="text" name="category" required>
        </div>
        <div class="form-group">
            <label>Price:</label>
            <input type="number" step="0.01" name="price" required>
        </div>
        <button type="submit">Add Expense</button>
    </form>
    {% if message %}
    <p class="success">{{ message }}</p>
    {% endif %}
</body>
</html>
'''

STATS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Expense Stats</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 40px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        input, select { width: 100%; padding: 8px; margin-top: 5px; }
        button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #4CAF50; }
        .stats-box { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .category-item { margin: 5px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Add Expense</a>
        <a href="/stats">View Stats</a>
    </div>
    <h2>Monthly Statistics</h2>
    <form method="POST">
        <div class="form-group">
            <label>Select Month:</label>
            <select name="month" required>
                <option value="">-- Select a month --</option>
                {% for month in available_months %}
                <option value="{{ month }}" {% if month == selected_month %}selected{% endif %}>{{ month }}</option>
                {% endfor %}
            </select>
        </div>
        <button type="submit">Get Stats</button>
    </form>

    {% if stats %}
    <div class="stats-box">
        <h3>Budget Analysis for {{ selected_month }}</h3>

        <h4>Spending by Category:</h4>
        {% for category, data in stats.category_analysis.items() %}
        <div class="category-item">
            <strong>{{ category.title() }}:</strong> ${{ data.spent }}
            {% if data.budget > 0 %}<br><small>{{ data.status }}</small>{% endif %}
        </div>
        {% endfor %}

        <div style="margin-top: 20px; padding-top: 15px; border-top: 2px solid #4CAF50;">
            <strong>Overall Total:</strong> ${{ stats.overall_total }}<br>
            <small>{{ stats.overall_status }}</small>
        </div>

        <form method="POST" action="/save_summary" style="margin: 20px 0;">
            <input type="hidden" name="month" value="{{ selected_month }}">
            <input type="hidden" name="summary_data" value="{{ stats.summary_json }}">
            <button type="submit" style="background: #2196F3; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px;">
                Save Summary to Google Sheet
            </button>
        </form>

        <h4>All Expenses:</h4>
        <table>
            <tr>
                <th>Item</th>
                <th>Category</th>
                <th>Price</th>
            </tr>
            {% for expense in stats.expenses %}
            <tr>
                <td>{{ expense.item }}</td>
                <td>{{ expense.category }}</td>
                <td>${{ expense.price }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        today = datetime.now()
        add_row = {
            "expense": {
                "month": today.strftime("%B %Y"),
                "item": request.form['item'],
                "category": request.form['category'],
                "price": request.form['price']
            }
        }

        TOKEN = os.environ["TOKEN"]
        PROJECT = os.environ["PROJECT"]
        TAB = os.environ["TAB"]
        USER = os.environ["USER"]

        headers = {"Authorization": TOKEN}
        sheet_endpoint = f"https://api.sheety.co/{USER}/{PROJECT}/{TAB}"

        row_to_add = requests.post(url=sheet_endpoint,
                                   json=add_row,
                                   headers=headers)
        message = 'Expense added successfully!'

    return render_template_string(HTML_TEMPLATE, message=message)


@app.route('/stats', methods=['GET', 'POST'])
def stats():
    stats_data = {}
    selected_month = ''

    # Get available months for dropdown
    TOKEN = os.environ["TOKEN"]
    PROJECT = os.environ["PROJECT"]
    TAB = os.environ["TAB"]
    USER = os.environ["USER"]

    headers = {"Authorization": TOKEN}
    sheet_endpoint = f"https://api.sheety.co/{USER}/{PROJECT}/{TAB}"

    response = requests.get(url=sheet_endpoint, headers=headers)
    data = response.json()

    # Extract unique months and sort by latest descending
    months = list(
        set(
            expense.get('month', '') for expense in data.get('expenses', [])
            if expense.get('month')))

    def sort_months(month_str):
        try:
            return datetime.strptime(month_str, "%B %Y")
        except:
            return datetime.min

    available_months = sorted(months, key=sort_months, reverse=True)

    if request.method == 'POST':
        selected_month = request.form['month']

        # Filter expenses for selected month
        month_expenses = [
            expense for expense in data.get('expenses', [])
            if expense.get('month') == selected_month
        ]

        if month_expenses:
            # Define budget goals for each category
            budget_goals = {
                'food': 450,
                'home+health': 100,
                'beauty+clothes': 100,
                'other': 150,
                'transport': 100,
                'entertainment': 200,
                'splitwise': 200
            }

            # Calculate category totals (normalize category names)
            category_totals = {}
            for expense in month_expenses:
                category = expense.get('category',
                                       'other').lower().replace(" ", "")
                price = float(expense.get('price', 0))
                category_totals[category] = category_totals.get(category,
                                                                0) + price

            # Calculate budget analysis for each category
            category_analysis = {}
            for category, spent in category_totals.items():
                if category in budget_goals:
                    budget = budget_goals[category]
                    difference = spent - budget
                    if difference > 0:
                        status = f"You were ${round(abs(difference), 2)} over budget."
                    elif difference < 0:
                        status = f"Congrats! You were ${round(abs(difference), 2)} under budget."
                    else:
                        status = "Congrats! You were exactly at budget."
                else:
                    status = "No budget set for this category."

                category_analysis[category] = {
                    'spent': round(spent, 2),
                    'budget': budget_goals.get(category, 0),
                    'status': status
                }

            # Calculate overall total
            total_spent = sum(category_totals.values())
            overall_budget = 1700
            overall_difference = total_spent - overall_budget

            if overall_difference > 0:
                overall_status = f"Uh oh, you were ${round(overall_difference, 2)} over your overall total budget"
            elif overall_difference < 0:
                overall_status = f"Nice! You were ${round(abs(overall_difference), 2)} under your overall total budget!"
            else:
                overall_status = "Whoa! You were exactly at budget!"

            # Prepare summary data for saving to sheet
            summary_for_sheet = {
                'category_analysis': category_analysis,
                'overall_total': round(total_spent, 2),
                'overall_status': overall_status
            }

            stats_data = {
                'category_analysis': category_analysis,
                'overall_total': round(total_spent, 2),
                'overall_status': overall_status,
                'expenses': month_expenses,
                'summary_json': json.dumps(summary_for_sheet)
            }

    return render_template_string(STATS_TEMPLATE,
                                  stats=stats_data,
                                  selected_month=selected_month,
                                  available_months=available_months)


@app.route('/save_summary', methods=['POST'])
def save_summary():
    month = request.form['month']
    summary_data = json.loads(request.form['summary_data'])

    TOKEN = os.environ["TOKEN"]
    PROJECT = os.environ["PROJECT"]
    TAB = "summaries"
    USER = os.environ["USER"]

    headers = {"Authorization": TOKEN}

    summary_sheet_endpoint = f"https://api.sheety.co/{USER}/{PROJECT}/{TAB}"

    try:
        # Add a separator row first
        separator_row = {
            "summary": {
                "month": month,
                "item": f"=== SUMMARY FOR {month.upper()} ===",
                "category": "Summary",
                "price": "0"
            }
        }
        response = requests.post(url=summary_sheet_endpoint,
                                 json=separator_row,
                                 headers=headers)
        print(
            f"Separator row response: {response.status_code}, {response.text}")

        # Add category data rows
        for category, data in summary_data['category_analysis'].items():
            category_row = {
                "summary": {
                    "month": month,
                    "item":
                        f"{category.title()}: ${data['spent']} ({data['status']})",
                    "category": "Summary",
                    "price": str(data['spent'])
                }
            }
            response = requests.post(url=summary_sheet_endpoint,
                                     json=category_row,
                                     headers=headers)
            print(
                f"Category row response: {response.status_code}, {response.text}"
            )

        # Add overall total row
        total_row = {
            "summary": {
                "month": month,
                "item":
                    f"OVERALL TOTAL: ${summary_data['overall_total']} ({summary_data['overall_status']})",
                "category": "Summary",
                "price": str(summary_data['overall_total'])
            }
        }
        response = requests.post(url=summary_sheet_endpoint,
                                 json=total_row,
                                 headers=headers)
        print(f"Total row response: {response.status_code}, {response.text}")

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Summary Saved</title>
            <style>
                body {{ font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; text-align: center; }}
                .success {{ color: green; font-size: 18px; margin: 20px 0; }}
                a {{ color: #4CAF50; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h2>Success!</h2>
            <p class="success">Summary for {month} has been saved to your Google sheet!</p>
            <a href="/stats">← Back to Stats</a>
        </body>
        </html>
        '''

    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error Saving Summary</title>
            <style>
                body {{ font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; text-align: center; }}
                .error {{ color: red; font-size: 18px; margin: 20px 0; }}
                a {{ color: #4CAF50; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h2>Error</h2>
            <p class="error">Failed to save summary: {str(e)}</p>
            <p>Error details: {str(e)}</p>
            <a href="/stats">← Back to Stats</a>
        </body>
        </html>
        '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
