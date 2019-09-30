import os
import os.path

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from intake import open_catalog
from markdown import markdown
from werkzeug.utils import secure_filename

CATALOGS_FOLDER = 'catalogs'
ALLOWED_CAT_EXT = {'yml', 'yaml'}
XOR_FOLDER = '/opt/inpher/xor' if os.path.exists('/opt/inpher/xor') else '/xor'
PRIVATEDATA_FOLDER = XOR_FOLDER + '/privatedata/'

app = Flask(__name__)
app.secret_key = b'*Qm6^wScTHguwPH_'
app.config['CATALOGS_FOLDER'] = CATALOGS_FOLDER
app.config['PRIVATEDATA_FOLDER'] = PRIVATEDATA_FOLDER

Bootstrap(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'alert-danger')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'alert-danger')
            return redirect(request.url)
        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['CATALOGS_FOLDER'], filename))
            flash('Datasource file imported', 'alert-success')
            return redirect(url_for('index'))
    # update catalogs list
    catalogs = open_catalog(CATALOGS_FOLDER)
    datasources = [v.describe() for _, v in catalogs.items()]
    return render_template('index.html', datasources=datasources)

@app.route('/run/<source>')
def run(source):
    catalogs = open_catalog(CATALOGS_FOLDER)
    try:
        # we only support dataframe containers for now
        assert catalogs[source].container == 'dataframe'
        # read datasource into memory
        data = catalogs[source].read()
        filename = source + '.csv'
        data.to_csv(os.path.join(app.config['PRIVATEDATA_FOLDER'], filename))
        flash('Added data file to XOR Machine', 'alert-success')
    except Exception as e:
        app.logger.exception(e)
        flash('Unable to create data file', 'alert-danger')
    return redirect(url_for('index'))

@app.route('/delete/<source>')
def delete(source):
    try:
        # check if we were given the filename or the catalog name
        filename = source if os.path.splitext(source)[1] else source + '.csv'
        os.remove(os.path.join(app.config['PRIVATEDATA_FOLDER'], filename))
        flash('Deleted data file from XOR Machine', 'alert-warning')
    except Exception as e:
        app.logger.exception(e)
        flash('Unable to delete data file', 'alert-danger')
    return redirect(request.referrer)

@app.route('/browse')
def browse():
    files = os.listdir(PRIVATEDATA_FOLDER)
    return render_template('browse.html', files=files)

@app.template_filter('parse_markdown')
def parse_markdown(text):
    return markdown(text)

def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_CAT_EXT

if __name__ == "__main__":
    import os

    if 'WINGDB_ACTIVE' in os.environ:
        app.debug = False

    app.run()