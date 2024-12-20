from app import app

@app.route('/party-list')
def party_list():
    return "View Party List Requests Here"
