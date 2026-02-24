@app.route("/")
def root():
#:if secret
#:section src/titles/secret.obun.py
#:else
#:section src/titles/default.obun.py
#:endif
