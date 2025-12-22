import os
import sys
import shutil
import select
from pathlib import Path
from contextlib import closing
from datetime import datetime, timezone
from email.utils import format_datetime

# Use pip-installed pysqlite3 as sqlite3 on non-macOS systems
if sys.platform != 'darwin':
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3

# ========================= Meta Configuration =================================

DB_FILE = 'knowledge.db'
DIST_DIR = Path('dist')
TMPL_DIR = Path('templates')
CMPS_DIR = Path('components')
ASSETS_DIR = Path('assets')

# ISO 8601 date string for December 10, 2003 at 1:30 PM Rome time (CET, UTC+1)
AUTHOR_BIRTHDAY = "2003-12-10T13:30:00+01:00"

BASE_URL = "https://danielfalbo.com"

USAGE_STR = f'Usage: python3 {sys.argv[0]} [ --watch <table> <slug> ]'

KB14_URL = 'https://endtimes.dev/why-your-website-should-be-under-14kb-in-size'

# ==================== Relationships Context Configuration =====================

#
# See '{context}' token section of the 'TEMPLATES' paragraph of README.
#
# Format:
# 'this_table': [
#     ('junction_table', 'this_id_col', 'this_junction_id_col',
#       'other_table', 'other_id_col', 'other_junction_id_col'),
# ]
#
# Note: assumes 'other_tables' has a 'slug' column and gets compiled at
# /<table>/[slug].html
#
RELATIONSHIPS = {
    'resources': [
        ('resource_authors', 'id', 'resource_id',
         'authors', 'id', 'author_id')
    ],
    'authors': [
        ('resource_authors', 'id', 'author_id',
         'resources', 'id', 'resource_id')
    ]
}

# =============================== Utils ========================================

def die_with_honor(msg):
    """
    Prints the given 'msg' to stderr and exits with status code 1.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)

def write_file(path, content):
    """
    Writes the given 'content' to file at given 'path'
    ensuring all parent dirs exits.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    size_kb = path.stat().st_size / 1024
    print(f"[OK] Wrote {size_kb:.2f}kB to {path}")

    if size_kb >= 14.0:
        print(f"[WARN] {path} over 14kB")
        print(f'[WARN] See {KB14_URL}')

def get_db_tables(db):
    """
    Returns a set of user table names in the database.
    """

    q = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
    return {row[0] for row in db.execute(q)}

# =========================== Site Generation ==================================

def load_global_css():
    """
    Reads the global.css file from the template dir
    and returns its string.
    """
    return (TMPL_DIR / 'global.css').read_text()

def load_tmpl(name):
    """
    Returns the content of the html file with given 'name' from the TMPL_DIR.
    """
    return (TMPL_DIR / f'{name}.html').read_text()

def load_cmps():
    """
    Returns a dictionary from 'name' to html content of file at
    CMPS_DIR / 'name'.html.
    """
    cmps = {}

    for path in CMPS_DIR.rglob('*.html'):
        stem = path.stem
        cmps[stem] = path.read_text()

    return cmps

def gen_tmpl_values(db, table, cmps):
    """
    Returns a dict from slug to a key-value object with the values to
    replace each placeholder key when rendering pages from template.
    """

    # Fetch entries from the given table
    rows = db.execute(f'SELECT * FROM {table}').fetchall()

    # Construct a map from slug to key-value replacements
    tmpl_values_by_slug = { r['slug']: {**dict(r), 'context': ''} for r in rows}

    # Replace the '{dateage}' placehoder in entries' 'html'
    dateage_cmp = cmps['dateage']
    for slug in tmpl_values_by_slug:
        html = tmpl_values_by_slug[slug].get('html', None)
        created_time = tmpl_values_by_slug[slug].get('created_time', None)

        if html is None or created_time is None:
            continue

        tmpl_values_by_slug[slug]['html'] = html.format(
            dateage=dateage_cmp.format(created_time=created_time,
                                       AUTHOR_BIRTHDAY=AUTHOR_BIRTHDAY)
        )

    # Construct the 'context' value to contain hyperlinks to all pages related
    # to the one with the given slug, based on the defined 'RELATIONSHIPS'.
    if table not in RELATIONSHIPS:
        return tmpl_values_by_slug

    a = table
    for j, a_id, j_a_id, b, b_id, j_b_id in RELATIONSHIPS[table]:
        # Query the database for the given relationship
        q = f"""
            SELECT a.slug as a_slug, b.slug as b_slug
            FROM {b} b
            JOIN {j} j ON b.id = j.{j_b_id}
            JOIN {a} a ON a.id = j.{j_a_id}
        """
        relations_map = {}
        for rel in db.execute(q):
            src_slug = rel['a_slug']
            if src_slug not in relations_map: relations_map[src_slug] = []
            relations_map[src_slug].append(rel['b_slug'])

        # Add links to the results at `tmpl_values_by_slug[row_slug]['context']`
        for row_slug, rel_slugs in relations_map.items():
            if row_slug in tmpl_values_by_slug:
                links = "".join([
                    f'<p><a href="../{b}/{s}.html">/{b}/{s}</a></p>'
                    for s in rel_slugs
                ])

                tmpl_values_by_slug[row_slug]['context'] += links

    return tmpl_values_by_slug

def generate_section(db, css, cmps, table):
    """
    Generate html pages for index and all entries of given 'table' within 'db'
    and writes them to DIST_DIR/<table>.html and DIST_DIR/<table>/[slug].html.
    """

    tmpl = load_tmpl(table)

    values = gen_tmpl_values(db, table, cmps)

    list_cmpn = cmps['list']

    index_content_html = ''


    for slug, row in values.items():
        # Generate entry page
        html = tmpl.format(css=css, **row)
        path = DIST_DIR / table / f"{slug}.html"
        write_file(path, html)

        # Append page href row to table index html accumulator
        index_content_html += (f'''<p>
            <a href="./{table}/{slug}.html">/{table}/{slug}</a>
        </p>''')

    # Generate table index
    index_path = DIST_DIR / f"{table}.html"
    index_html = list_cmpn.format(css=css, table=table,
                                  content=index_content_html)
    write_file(index_path, index_html)

def generate_rss(db, table):
    """
    Generates the RSS 2.0 XML feed for the given table at 'dist/<table>/rss'.
    """
    # Schema check: authors use 'name', others use 'title'
    title_col = 'name' if table == 'authors' else 'title'

    # Fetch all entries ordered by creation date (newest first)
    q = f"SELECT slug, {title_col}, created_time, html FROM {table} ORDER BY created_time DESC"
    rows = db.execute(q).fetchall()

    items_xml = ""
    for r in rows:
        # Vercel with cleanUrls: true serves /table/slug (without .html)
        link = f"{BASE_URL}/{table}/{r['slug']}"

        # XML Escape the title
        title = str(r[title_col]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Convert SQLite date string to RSS 2.0 RFC 822 format.
        #
        # SQLite assumes UTC and formats as YYYY-MM-DD HH:MM:SS
        # but some dates may have been updated manually to be just YYYY-MM-DD.
        #
        # Run
        #   'SELECT created_time FROM notes' or
        #   'SELECT created_time FROM notes'
        # to see what does the DB look like in practice.
        dt = r['created_time'].split(' ')[0]
        dt = datetime.strptime(dt, "%Y-%m-%d")
        dt = dt.replace(tzinfo=timezone.utc)
        dt = format_datetime(dt)

        items_xml += f"""
    <item>
      <title>{title}</title>
      <guid>{link}</guid>
      <link>{link}</link>
      <pubDate>{dt}</pubDate>
      <description>
        <![CDATA[ {r['html']} ]]>
      </description>
    </item>"""

    rss_content = f"""<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
  <channel>
    <title>{table} | danielfalbo</title>
    <link>{BASE_URL}/{table}</link>
    <description>Latest entries from {table}</description>
    {items_xml}
  </channel>
</rss>"""

    write_file(DIST_DIR / table / "rss", rss_content)

def generate_standalone_page(css, name):
    """
    Generates a standalone HTML page from the template with the given 'name'
    and writes it to DIST_DIR/[name].html.
    """
    template = load_tmpl(name)

    html = template.replace('{css}', css)

    path = DIST_DIR / f'{name}.html'
    write_file(path, html)

def generate_all(db):
    # Clean output dir
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    # Copy assets
    shutil.copytree(ASSETS_DIR, DIST_DIR / 'assets', dirs_exist_ok=True)
    print(f"[OK] Copied assets to {DIST_DIR / 'assets'}")

    css = load_global_css()

    cmps = load_cmps()

    tables = get_db_tables(db)

    # For each available template, find its database table and generate
    # a section with one html page per entry, replacing any placeholder value
    # from the template with its value on the given entry row.
    # If template name is not a table name, generate the page as standalone.
    for path in TMPL_DIR.rglob('*.html'):
        stem = path.stem

        if stem in tables:
            generate_section(db, css, cmps, stem)
            generate_rss(db, stem)
        else:
            generate_standalone_page(css, stem)

# =========================== Live Watch Mode ==================================

def watch_buffer(table, slug):
    buf_file = f'buf_{table}_{slug}.html'

    # Get entry title from database given 'table' and 'slug'.
    with closing(sqlite3.connect(DB_FILE)) as db:
        db.row_factory = sqlite3.Row # Access columns by name
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table} WHERE slug='{slug}'")
        row = cursor.fetchone()

    if not row:
        die_with_honor(f"Slug '{slug}' not found in table '{table}'")

    print(f"Watching {buf_file} as html content of {table}/{slug}...")

    fd = os.open(buf_file, os.O_RDONLY | os.O_CREAT, 0o644)
    kq = select.kqueue()
    kevent = select.kevent(fd, filter=select.KQ_FILTER_VNODE,
                           flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                           fflags=select.KQ_NOTE_WRITE)

    # Register filter, wait for 0 events just yet
    kq.control([kevent], 0)

    template = (TMPL_DIR / f'{table}.html').read_text()
    css = load_global_css()

    try:
        while True:
            kq.control(None, 1) # Wait for 1 event
            print('>> Change detected, rebuilding...')

            # Read html buffer size
            size = os.lseek(fd, 0, os.SEEK_END)

            # Rewind and read full file
            os.lseek(fd, 0, os.SEEK_SET)
            html = os.read(fd, size).decode('utf-8')

            # Generate just this file
            row = {**row, 'html': html}
            content = template.format(css=css, **row, context='')

            out_path = DIST_DIR / table / f'{slug}.html'
            write_file(out_path, content)

    except KeyboardInterrupt:
        print("\nStopping...")
        os.close(fd)

# ================================ Main ========================================

def main():
    if len(sys.argv) == 1:
        with closing(sqlite3.connect(DB_FILE)) as db:
            db.row_factory = sqlite3.Row # Access columns by name
            generate_all(db)

    elif len(sys.argv) == 4 and sys.argv[1] == '--watch':
        table, slug = sys.argv[2], sys.argv[3]
        watch_buffer(table, slug)

    else:
        die_with_honor(USAGE_STR)

if __name__ == '__main__':
    main()
