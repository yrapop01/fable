/*
 * Requires editor.js to be loaded!
 */

function guid() {
  /* from https://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript */
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
  }
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}

function replaceAll(str, find, replace) {
    /* from https://stackoverflow.com/questions/1144783/how-to-replace-all-occurrences-of-a-string-in-javascript */
    return str.replace(new RegExp(find, 'g'), replace);
}

function toggleClassInside(elem, className) {
    for (var i in elem.childNodes) {
        var child = elem.childNodes[i];

        if (!child.classList)
            continue;

        if (child.classList.contains(className)) {
            child.classList.remove(className);
        } else {
            child.classList.add(className);
        }
    }
}

function Cell(anchor, position, notebook, cell_guid) {

    var self = {};

    self.guid = cell_guid || guid();
    self.nextCell = null;
    self.prevCell = null;
    self.state = 'Idle';
    self.type = 'Code';
    self.is_minimized = false;
    self.notebook = notebook;

    notebook.cells[self.guid] = self;

    var html = self.notebook.cellHtml;
    html = replaceAll(html, "{ID}", self.guid);

    anchor.insertAdjacentHTML(position, html);

    self.editorNode = document.getElementById('editor-' + self.guid);
    self.outputNode = document.getElementById('output-' + self.guid);

    // Info Nodes
    self.itemNode = document.getElementById('item-' + self.guid);
    self.stateNode = document.getElementById('state-' + self.guid);
    self.orderNode = document.getElementById('order-' + self.guid);

    self.topNode = document.getElementById('cell-' + self.guid);

    // Wrapper Nodes
    self.editorWrapperNode = document.getElementById('editor-wrapper-' + self.guid);

    // Control Nodes
    self.controlNodes = {
        stop: document.getElementById('stop-' + self.guid),
        select: document.getElementById('select-' + self.guid),
        toggle: document.getElementById('toggle-' + self.guid),
        clear: document.getElementById('clear-' + self.guid),
        start: document.getElementById('start-' + self.guid),
        del: document.getElementById('del-' + self.guid)
    }

    // Editor Init
    self.editor = Editor(self.editorNode, "python", "");

    self.focus = function() {
        self.editor.focus();
    }

    self.detach = function() {
        if (self.prevCell)
            self.prevCell.nextCell = self.nextCell;
        if (self.nextCell)
            self.nextCell.prevCell = self.prevCell;
    }

    self.attach = function(cell) {
        if (self.nextCell === cell)
            return cell;
        cell.detach()
        if (self.nextCell)
            self.nextCell.prevCell = cell;

        cell.nextCell = self.nextCell;
        cell.prevCell = self;
        self.nextCell = cell;      
    }

    self.next = function() {
        return self.nextCell;
    }

    self.code = function() {
        return self.editor.getCode();
    }

    self.changeState = function(state) {
        self.state = state;
        self.stateNode.innerHTML = state;
    }

    self.changeLanguage = function(kind) {
        if (kind && kind != '')
            self.editor.changeLanguage(kind);
    }

    self.write = function(answer) {
        if (!answer.length)
            return;
        if (self.outputNode.classList.contains('hidden'))
            self.outputNode.classList.remove('hidden');
        self.outputNode.innerHTML += answer;
    }

    self.putCode = function(answer) {
        self.editor.putCode(answer);
    }

    self.clear = function() {
        if (!self.outputNode.classList.contains('hidden'))
            self.outputNode.classList.add('hidden');
        self.outputNode.innerText = '';
    }

    self.forward = function() {
        if (self.nextCell) {
            self.nextCell.focus()
            return;
        }

        var cell = self.append();
        cell.focus();
    }

    self.append = function(guid) {
        var cell = Cell(self.topNode, 'afterEnd', self.notebook, guid);

        if (self.nextCell)
            self.nextCell.prevCell = cell;

        cell.nextCell = self.nextCell;
        cell.prevCell = self;
        self.nextCell = cell;

        if (self.notebook.events.newcell && !guid)
            self.notebook.events.newcell(self.guid, cell.guid);

        return cell;
    }

    self.editorNode.addEventListener('keydown', function(e) {
        var key = e.keyCode || e.charCode;
        if (key == 13 && e.shiftKey) {
            e.preventDefault();
            self.forward();
            if (self.notebook.events.submit)
                self.notebook.events.submit(self);
        }
    });

    self.controlNodes.start.addEventListener('click', function(e) {
        if (self.notebook.events.submit)
            self.notebook.events.submit(self);
    });

    self.controlNodes.stop.addEventListener('click', function(e) {
        if (self.notebook.events.interrupt)
            self.notebook.events.interrupt(self);
    });

    self.controlNodes.select.addEventListener('click', function(e) {
        toggleClassInside(self.controlNodes.select, "hidden");
    });

    self.controlNodes.clear.addEventListener('click', function(e) {
        self.clear();
    });

    self.controlNodes.toggle.addEventListener('click', function(e) {
        toggleClassInside(self.controlNodes.toggle, "hidden");

        self.is_minimized = !self.is_minimized;
        if (self.is_minimized) {
            self.editorWrapperNode.classList.add('hidden');
        } else {
            self.editorWrapperNode.classList.remove('hidden');
        }
    });

    return self;
}

function Notebook(container, controlsHtml, cellHtml) {
    var self = {events: {},
                cells: {},
                container: container,
                controlsHtml: controlsHtml,
                cellHtml: cellHtml,
                uuid: guid()}
   
    var controls = controlsHtml.replace('{ID}', self.uuid);
    container.insertAdjacentHTML('afterBegin', controls);

    self.build = function(cell_guid) {
        var cell = Cell(container, 'beforeEnd', self, cell_guid);
        if (self.events.newcell && !cell_guid)
            self.events.newcell(null, cell.guid);

        return cell;
    }

    self.destroy = function() {
        self.cells =  {};
        self.container.classList.add('notebook-disabled');
    }

    return self;
}
