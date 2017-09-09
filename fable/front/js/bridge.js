function Connection() {
    var self = {events: {}};

    self.open = function() {
        let domain = document.domain;
        let path = location.pathname.split("/").slice(0, -1).join("/") + "/ws";
        let port = location.port;
        let url = "ws://" + domain + ":" + port + path;
        self.ws = new WebSocket(url);

        self.ws.onopen = function(event) {
            self.onopen(event);
        };

        self.ws.onmessage = function(event) {
            self.onmessage(event);
        };

        self.ws.onclose = function(event) {
            self.onclose(event);
        };

        self.ws.onerror = function(event) {
            console.log('ws error occured');
        }
    };

    self.send = function(obj) {
        self.ws.send(JSON.stringify(obj));
    }

    self.onopen = function(event) {
        console.log('opened');

        let params = (new URL(document.location)).searchParams;
        var action = {
            name: params.has('name') ? params.get('name') : ''
        };
        if (params.has('force'))
            action.force = Boolean(params.get('force'));
        self.send(['notebook', action]);
    };

    self.onclose = function(event) {
        console.log('closed');
        if (self.events.disconnected)
            self.events.disconnected();
    };

    self.onmessage = function(event) {
            let data = JSON.parse(event.data);
            let code = data['code'];
            let value = data['value'];

            if (code in self.events)
                self.events[code](value);
    };

    return self;
}

function Tasks() {
    var self = {tasks: [], current: null};

    self.add = function(cell) {
        if (cell.state != 'Idle') {
            console.log('Error: cannot execute non-idle cell');
            return;
        }
        cell.changeState('Waiting');
        self.tasks.push([cell, cell.code()]);
    };

    self.shift = function() {
        if (self.current) {
            console.log('Waiting for an old task to finish');
            return null;
        }
        if (self.tasks.length == 0) {
            console.log('No more tasks to run');
            return null;
        }
        self.current = self.tasks.shift();
        self.current[0].changeState('Sending');
        return {ids: self.current[0].guid, code: self.current[1]};
    };

    self.started = function(guid) {
        if (!self.current || guid != self.current[0].guid) {
            console.log('ERROR: Running a cell not scheduled for execution');
            return;
        }
        self.current[0].changeState('Running');
    };

    self.ended = function(guid) {
        if (!self.current || guid != self.current[0].guid) {
            console.log('ERROR: Run a cell not scheduled for execution');
            return;
        }
        self.current[0].changeState('Idle');
        self.current = null;
    };

    self.remove = function(guid) {
        var i;
        if (self.current && guid == self.current[0].guid) {
            self.current[0].changeState('Stopping');
            return false;
        }
        for (i in self.tasks) {
            if (self.tasks[i][0].guid == guid)
                break;
        }
        if (!i || i == self.tasks.length) {
            console.log('ERROR: Trying to remove unknown task');
            return true;
        }
        console.log(i);
        self.tasks[i][0].changeState('Idle');
        self.tasks.splice(i, 1);
        return true;
    }

    self.overrideRunning = function(cell) {
        if (self.current) {
            console.log('ERROR: Already running another cell');
            return;
        }

        self.current = [cell, cell.code];
        self.current[0].changeState('Running');
    }

    return self;
}

function Bridge(notebook) {
    var conn = Connection();
    var tasks = Tasks();

    function output(text, cls) {
        return "<span class=\"" + cls +"\" style=\"white-space: pre\">" + text + "</span>";
    }

    function format(outputs) {
        var out = "";
        for (var i in outputs) {
            let key = outputs[i][0];
            let value = outputs[i][1];

            if (key == "err")
                out += output(value, "text-danger");
            else if (key == "out")
                out += output(value, "text-primary");
            else if (key == "html")
                out += value;
            else if (key == "section")
                out += "<h4>" + value + "</h4>";
            else if (key == "subsection")
                out += value;
        }
        return out;
    }

    conn.events.opened = function(value) {
        let cells = value['cells'];
        let running = value['running'];

        if (!cells.length) {
            notebook.build();
            return;
        }

        var cell = null;
        for (var i in cells) {
            let desc = cells[i];
            let guid = desc['guid'];

            if (!cell)
                cell = notebook.build(guid);
            else
                cell = cell.append(cell, guid);

            cell.putCode(desc['data']);
            cell.write(format(desc['out']));
            cell.changeLanguage(desc['kind']);
        }

        if (running)
            tasks.overrideRunning(notebook.cells[running]);
    }

    conn.events.code_run = function(value) {
        let guid = value["ids"];
        let msgs = value["msg"];

        if (!(guid in notebook.cells)) {
            console.log('ERROR: printing to unknown cell');
            return;
        }

        for (var i in msgs) {
            let msg = msgs[i];
            let key = msg[0];

            if (key == "started") {
                tasks.started(guid);
                continue;
            }

            if (key == "ended") {
                tasks.ended(guid);
                continue;
            }

            var out = format([msg]);
            console.log('output', out);
            if (out)
               notebook.cells[guid].write(out);
        }
    };

    conn.events.kind_changed = function(value) {
        let guid = value['guid'];
        let kind = value['kind'];
        
        notebook.cells[guid].changeLanguage(kind);
    };

    conn.events.disconnected = function() {
        notebook.destroy();
    };

    notebook.events.submit = function(s) { 
        s.clear();
        tasks.add(s);
        conn.send(["change", {guid: s.guid, code: s.code()}]);

        var current = tasks.shift();
        if (current)
            conn.send(["run", current]);
    };

    notebook.events.interrupt = function(s) {
        if (!tasks.remove(s.guid))
            conn.send(["interrupt", null]);
    };

    notebook.events.newcell = function(prev_id, cell_id) {
        conn.send(["newcell", {prev_id: prev_id, cell_id: cell_id}]);
    }

    self.connect = function() {
        conn.open();
    }

    return self;
}
