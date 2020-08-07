import os

import bottle

from game import gamedb

UIDIR = os.path.abspath('editorui')

@bottle.route('/')
def index():
    return bottle.static_file('index.html', root=UIDIR)

@bottle.route('/css/<filename:path>')
def send_css(filename):
    return bottle.static_file(os.path.join('css', filename), root=UIDIR)

@bottle.route('/js/<filename:path>')
def send_js(filename):
    return bottle.static_file(os.path.join('js', filename), root=UIDIR)

@bottle.route('/gdb')
def get_db():
    return gamedb.get_instance().to_dict()

@bottle.route('/schema/<datatype>')
def get_schema(datatype):
    return gamedb.get_instance().get_schema(datatype)

bottle.run(host='localhost', port=8080)
