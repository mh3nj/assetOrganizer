/*
affinity_pipeline.js

Asset Organizer automation for the new unified Affinity (Canva-era).

Runs inside Affinity via its MCP execute_script tool. Only documented
SDK patterns are used: require('/application'), app.documents.current,
mutations through doc.executeCommand, results via console.log.

Save / close / layer-visibility APIs differ between Affinity builds,
so every function probes several strategies and ALWAYS prints one
JSON line: {"ok":true,...} or {"ok":false,...}. The Python controller
reads that line and degrades gracefully (warn + continue) instead of
ever failing a job on an Affinity API mismatch.
*/


function aoCurrentDocName()
{
    try {
        var app = require('/application').app;
        var doc = app.documents.current;
        if (!doc) {
            console.log(JSON.stringify({ ok: true, name: null }));
            return;
        }
        console.log(JSON.stringify({ ok: true, name: doc.name || doc.title || null }));
    } catch (e) {
        console.log(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
}


function aoProbe()
{
    // Reports which automation surface this Affinity build has, so the
    // controller (and the user, via the log) can see what will work.
    try {
        var app = require('/application').app;
        var doc = app.documents.current;
        var info = { ok: true, hasDoc: !!doc, docName: null, can: {} };
        if (doc) {
            info.docName = doc.name || doc.title || null;
            info.can.save = (typeof doc.save === 'function');
            info.can.close = (typeof doc.close === 'function');
        }
        info.can.executeCommand = !!(doc && typeof doc.executeCommand === 'function');
        var docs = app.documents;
        info.can.docsOpen = (typeof docs.open === 'function');
        info.can.docsClose = (typeof docs.close === 'function');
        console.log(JSON.stringify(info));
    } catch (e) {
        console.log(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
}


function aoHideVisibleLayers()
{
    // Best-effort: walk the live node graph for visible flags and flip
    // them. Bounded (visited set + depth/node caps) so it can never hang
    // on huge or cyclic documents. Direct sets may throw on builds that
    // require DocumentCommands — those nodes are skipped and counted.
    try {
        var app = require('/application').app;
        var doc = app.documents.current;
        if (!doc) {
            console.log(JSON.stringify({ ok: false, error: 'no open document' }));
            return;
        }
        var SKIP = { parent: 1, document: 1, app: 1, application: 1 };
        var visited = [];
        var hidden = 0, skipped = 0, seen = 0;
        var CAP_NODES = 8000, MAX_DEPTH = 12;

        function alreadySeen(obj) {
            for (var i = 0; i < visited.length; i++) {
                if (visited[i] === obj) return true;
            }
            return false;
        }

        function visit(obj, depth) {
            if (!obj || depth > MAX_DEPTH || seen > CAP_NODES) return;
            if ((typeof obj !== 'object' && typeof obj !== 'function') || alreadySeen(obj)) return;
            visited.push(obj);
            seen++;
            var isVisible = obj.visible === true || obj.isVisible === true;
            if (isVisible) {
                try {
                    if (obj.visible === true) obj.visible = false;
                    else obj.isVisible = false;
                    hidden++;
                } catch (e) { skipped++; }
            }
            var keys = [];
            try { keys = Object.keys(obj); } catch (e) { return; }
            for (var i = 0; i < keys.length; i++) {
                var k = keys[i];
                if (SKIP[k]) continue;
                var child;
                try { child = obj[k]; } catch (e) { continue; }
                if (child && (typeof child === 'object' || typeof child === 'function')) {
                    if (typeof child.length === 'number' && typeof child !== 'string') {
                        for (var j = 0; j < child.length && seen <= CAP_NODES; j++) {
                            try { visit(child[j], depth + 1); } catch (e) { skipped++; }
                        }
                    } else {
                        visit(child, depth + 1);
                    }
                }
                if (seen > CAP_NODES) return;
            }
        }

        var roots = [];
        try {
            if (doc.layers) roots.push(doc.layers);
            if (doc.spreads) roots.push(doc.spreads);
            if (doc.pages) roots.push(doc.pages);
            if (doc.children) roots.push(doc.children);
        } catch (e) {}
        if (roots.length === 0) roots.push(doc);
        for (var r = 0; r < roots.length; r++) visit(roots[r], 0);

        console.log(JSON.stringify({ ok: true, hidden: hidden, skipped: skipped }));
    } catch (e) {
        console.log(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
}


function aoSave()
{
    try {
        var app = require('/application').app;
        var doc = app.documents.current;
        if (!doc) {
            console.log(JSON.stringify({ ok: false, error: 'no open document' }));
            return;
        }
        var tried = [];
        var strategies = [
            function () { doc.save(); },
            function () { doc.saveToFile(); },
            function () { app.documents.save(doc); },
            function () { app.saveActiveDocument(); }
        ];
        for (var i = 0; i < strategies.length; i++) {
            try {
                strategies[i]();
                console.log(JSON.stringify({ ok: true, strategy: i }));
                return;
            } catch (e) { tried.push(i + ':' + String(e && e.message || e)); }
        }
        console.log(JSON.stringify({ ok: false, tried: tried }));
    } catch (e) {
        console.log(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
}


function aoClose()
{
    try {
        var app = require('/application').app;
        var doc = app.documents.current;
        if (!doc) {
            console.log(JSON.stringify({ ok: true, alreadyClosed: true }));
            return;
        }
        var tried = [];
        var strategies = [
            function () { doc.close(); },
            function () { doc.closeWithoutSaving(); },
            function () { app.documents.close(doc); },
            function () { app.closeActiveDocument(); }
        ];
        for (var i = 0; i < strategies.length; i++) {
            try {
                strategies[i]();
                console.log(JSON.stringify({ ok: true, strategy: i }));
                return;
            } catch (e) { tried.push(i + ':' + String(e && e.message || e)); }
        }
        console.log(JSON.stringify({ ok: false, tried: tried }));
    } catch (e) {
        console.log(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
}
