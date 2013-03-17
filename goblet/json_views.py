from goblet.views import PathView
from goblet.filters import humantime, shortmsg
from jinja2 import escape
import json
from flask import send_file, request, redirect, config, current_app
import os

class TreeChangedView(PathView):
    def handle_request(self, repo, path):
        ref, path, tree, _ = self.split_ref(repo, path)
        if ref not in repo:
            ref = repo.lookup_reference('refs/heads/%s' % ref).hex
        cfile = os.path.join(repo.cpath, 'dirlog_%s_%s.json' % (ref, path.replace('/', '_')))
        if not os.path.exists(cfile):
            tree = repo[ref].tree
            for elt in path.split('/'):
                if elt:
                    tree = repo[tree[elt].hex]
            lastchanged = repo.tree_lastchanged(repo[ref], path)
            commits = {}
            for commit in set(lastchanged.values()):
                commit = repo[commit]
                commits[commit.hex] = [humantime(commit.commit_time), escape(shortmsg(commit.message))]
            for file in lastchanged:
                lastchanged[file] = (lastchanged[file], tree[file].hex[:7])
            ret = {'files': lastchanged, 'commits': commits}
            with open(cfile, 'w') as fd:
                json.dump(ret, fd)
        if 'wsgi.version' in request.environ:
            # Redirect to the file, let the webserver deal with it
            return redirect(cfile.replace(current_app.config['REPO_ROOT'], ''))
        else:
            return send_file(cfile)
