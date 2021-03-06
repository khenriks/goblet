# Goblet - Web based git repository browser
# Copyright (C) 2012-2014 Dennis Kaarsemaker
# See the LICENSE file for licensing details

from goblet.views import PathView
from goblet.filters import shortmsg
from jinja2 import escape
import json
from flask import current_app, send_file
import os

class TreeChangedView(PathView):
    def handle_request(self, repo, path):
        ref, path, tree, _ = self.split_ref(repo, path)
        try:
            if ref not in repo:
                ref = repo.lookup_reference('refs/heads/%s' % ref).target.hex
        except ValueError:
            ref = repo.lookup_reference('refs/heads/%s' % ref).target.hex
        if hasattr(repo[ref], 'target'):
            ref = repo[repo[ref].target].hex
        cache_dir = os.path.join(current_app.config['CACHE_ROOT'], 'dirlog')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cfile = os.path.join(cache_dir, 'dirlog_%s_%s.json' % (ref, path.replace('/', '_')))
        if not os.path.exists(cfile):
            tree = repo[ref].tree
            for elt in path.split('/'):
                if elt:
                    tree = repo[tree[elt].hex]
            lastchanged = repo.tree_lastchanged(repo[ref], path)
            commits = {}
            for commit in set(lastchanged.values()):
                commit = repo[commit]
                commits[commit.hex] = [commit.commit_time, escape(shortmsg(commit.message))]
            for file in lastchanged:
                lastchanged[file] = (lastchanged[file], tree[file].hex[:7])
            ret = {'files': lastchanged, 'commits': commits}
            with open(cfile, 'w') as fd:
                json.dump(ret, fd)
        return send_file(cfile)
