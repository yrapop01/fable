/*
 * Requires editor.js to be loaded!
 */

/*
 * CELL CSS & HTML TEMPLATE. 
 */
let CELL_CSS = "<style type='text/css'>\n" +
               ".editor-wrapper { " +
                    "border-radius: 0 !important;" +
                    "margin: 0 !important;" +
                    "background-color: rgba(214,219,191,1) !important;" +
               " }\n" +
               ".editor { " +
                    "font-size: normal !important;" +
                    //"border: 1px solid;" +
                    //*"border-color: #e7e8c1;" +
                    "background-color: rgba(254,255,232,1) !important;" +
               " }\n" +
               "div.output { " +
                    "border-top-left-radius: 0px !important; border-top-right-radius: 0 !important;" +
                    "border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0 !important;" +
                    "max-height: 100vh;" +
                    "overflow: scroll;" +
               " }\n" +
               "div.output { " +
                    "background-color: rgba(254,255,232,1) !important;" +
               " }\n" +
               ".hidden { " +
                    "display: none !important;" +
               " }\n" +
               ".meta-wrapper { " +
                    "font-size: x-small !important;" +
                    "display: flex;" +
                    "flex-direction: row;" +
                    "justify-content: space-between;" +
                    "border: 1px solid;" +
                    "border-color: silver;" +
                    "align-items: center;" +
               " }\n" +
               ".info-value { " +
                    "padding-right: 1em;" +
               " }\n" +
               ".info-value, .info-label { " +
                    "opacity: 0.8;" +
               " }\n" +
               ".btn-xs { " +
                    "padding-top: 0px !important;" +
                    "padding-bottom: 0px !important;" +
               " }\n" +
               "div.top { " +
                    "margin-bottom: 0px !important;" +
               " }\n" + 
               "</style>";

let CELL_HTML = "<div class='row top' id='top-{ID}'><div class='col-xs-12'>" +

                "<pre id='editor-wrapper-{ID}' class='editor-wrapper'>" +
                "<code class='code editor' contenteditable='true' id='editor-{ID}' spellcheck='false'></code>" +
                "</pre>" +

                "<!--div class='editor-wrapper_1'><div class='editor-wrapper_2'><div class='code editor' id='editor-{ID}'></div></div></div-->" +

                "<div id='output-{ID}' class='well well-sm output hidden'></div>" +

                "<div class='meta-wrapper controls-bg'>" +
                    "<span class='meta' id='controls-wrapper-{ID}'>" +
                        '<a id="select-{ID}" class="btn btn-xs btn-outline-primary">' +
                            '<span class="glyphicon glyphicon-unchecked"></span>' +
                            '<span class="glyphicon glyphicon-check hidden"></span>' +
                        '</a>' +
                        '<a id="toggle-{ID}" class="btn btn-xs btn-outline-primary">' +
                            '<span class="glyphicon glyphicon-eye-close"></span>' +
                            '<span class="glyphicon glyphicon-eye-open hidden"></span>' +
                        '</a>' +
                        '<a id="clear-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-erase"></span></a>' +
                        '<a id="up-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-up"></span></a>' +
                        '<a id="down-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-down"></span></a>' +
                        '<a id="add-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-plus"></span></a>' +
                        '<a id="del-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-trash"></span></a>' +
                        '<a id="stop-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-stop"></span></a>' +
                        '<a id="start-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-play"></span></a>' +
                    "</span>" +
                    "<span class='meta' id='info-{ID}'>" +
                        "<span class='info-label'>Item: </span>" +
                        "<span class='info-value' id='item-{ID}'>0</span>" +
                        "<span class='info-label'>Order: </span>" +
                        "<span class='info-value' id='order-{ID}'>0</span>" +
                        "<span class='info-label'>State: </span>" +
                        "<span class='info-value' id='state-{ID}'>Idle</span>" +
                    "</span>" +
                "</div>" +



                "</div></div>";

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

    var html = CELL_HTML;
    html = replaceAll(html, "{ID}", self.guid);

    anchor.insertAdjacentHTML(position, html);

    self.editorNode = document.getElementById('editor-' + self.guid);
    self.outputNode = document.getElementById('output-' + self.guid);

    // Info Nodes
    self.itemNode = document.getElementById('item-' + self.guid);
    self.stateNode = document.getElementById('state-' + self.guid);
    self.orderNode = document.getElementById('order-' + self.guid);

    self.topNode = document.getElementById('top-' + self.guid);

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

        cell = self.append(self);
        cell.focus();
    }

    self.append = function(prev, guid) {
        var cell = Cell(prev.topNode, 'afterEnd', prev.notebook, guid);

        if (prev.nextCell)
            prev.nextCell.prevCell = cell;

        cell.nextCell = prev.nextCell;
        cell.prevCell = prev;
        prev.nextCell = cell;

        if (self.notebook.events.newcell && !guid)
            self.notebook.events.newcell(prev.guid, cell.guid);

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

function Notebook(container) {
    var self = {events: {}, cells: {}, container: container};

    self.build = function(cell_guid) {
        var cell = Cell(container, 'afterBegin', self, cell_guid);
        if (self.events.newcell && !cell_guid)
            self.events.newcell(null, cell.guid);

        return cell;
    }

    self.destroy = function() {
        self.cells =  {};
        self.container.innerHTML = '';
    }

    self.container.insertAdjacentHTML('beforeBegin', CELL_CSS);

    return self;
}
