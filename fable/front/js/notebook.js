/*
 * Requires editor.js to be loaded!
 */

/*
 * CELL CSS & HTML TEMPLATE. 
 */
let CELL_CSS = "<style type='text/css'>\n" +
               "pre.editor-wrapper { " +
                    "border-top-left-radius: 0px !important; border-top-right-radius: 0 !important;" +
                    "border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0 !important;" +
               " }\n" +
               "code.editor { " +
                    "font-size: normal !important;" +
               " }\n" +
               "div.output { " +
                    "border-top-left-radius: 0px !important; border-top-right-radius: 0 !important;" +
                    "border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0 !important;" +
                    "max-height: 50vh;" +
                    "overflow: scroll;" +
               " }\n" +
               "div.output { " +
                    "background-color: white;" +
               " }\n" +
               ".hidden { " +
                    "display: none !important;" +
               " }\n" +
               ".meta-wrapper { " +
                    "border-top-left-radius: 5px !important; border-top-right-radius: 5px !important;" +
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
               ".btn-xs { " +
                    "padding-top: 0px !important;" +
                    "padding-bottom: 0px !important;" +
               " }\n" +
               "div.top { " +
                    "margin-bottom: 0px !important;" +
               " }\n" + 
               "</style>";

let CELL_HTML = "<div class='row top' id='top-{ID}'><div class='col-xs-12'>" +

                "<div class='meta-wrapper'>" +
                    "<span class='meta' id='controls-{ID}'>" +
                        '<a id="play-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-play"></span></a>' +
                        '<a id="stop-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-stop"></span></a>' +
                        '<a id="add-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-plus"></span></a>' +
                        '<a id="toggle-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-resize-small"></span></a>' +
                        '<a id="clear-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-erase"></span></a>' +
                        '<a id="up-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-up"></span></a>' +
                        '<a id="down-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-down"></span></a>' +
                        '<a id="cut-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-scissors"></span></a>' +
                        '<a id="select-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-unchecked"></span></a>' +
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

                "<pre class='editor-wrapper' id='editor-wrapper-{ID}'>" +
                "<code class='code editor' contenteditable='true' id='editor-{ID}' spellcheck='false'></code>" +
                "</pre>" +

                "<div id='output-{ID}' class='well well-sm output hidden'></div>" +

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

    self.itemNode = document.getElementById('item-' + self.guid);
    self.stateNode = document.getElementById('state-' + self.guid);
    self.orderNode = document.getElementById('order-' + self.guid);

    self.topNode = document.getElementById('top-' + self.guid);

    // Wrapper Nodes
    self.editorWrapperNode = document.getElementById('editor-wrapper-' + self.guid);
    self.infoNode = document.getElementById('info-' + self.guid);

    // Controls
    self.controlStopNode = document.getElementById('stop-' + self.guid);
    self.controlSelectNode = document.getElementById('select-' + self.guid);
    self.controlToggleNode = document.getElementById('toggle-' + self.guid);
    self.controlClearNode = document.getElementById('clear-' + self.guid);

    self.editor = Editor(self.editorNode);

    self.focus = function() {
        self.editorNode.focus();
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
        return self.editor.node.innerText;
    }

    self.change_status = function(state) {
        self.state = state;
        self.stateNode.innerHTML = state;
    }

    self.change_kind = function(kind) {
        if (self.kind)
            self.editorNode.classList.remove(kind);
        self.kind = kind;
        self.editorNode.classList.add(kind);
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

    self.controlStopNode.addEventListener('click', function(e) {
        if (self.notebook.events.interrupt)
            self.notebook.events.interrupt(self);
    });

    self.controlSelectNode.addEventListener('click', function(e) {
        if (self.controlSelectNode.innerHTML.includes('-unchecked'))
            self.controlSelectNode.innerHTML = '<span class="glyphicon glyphicon-check"></span>';
        else
            self.controlSelectNode.innerHTML = '<span class="glyphicon glyphicon-unchecked"></span>';
    });

    self.controlClearNode.addEventListener('click', function(e) {
        self.clear();
    });

    self.controlToggleNode.addEventListener('click', function(e) {
        if (self.controlToggleNode.innerHTML.includes('resize-small'))
            self.controlToggleNode.innerHTML = '<span class="glyphicon glyphicon-resize-full"></span>';
        else
            self.controlToggleNode.innerHTML = '<span class="glyphicon glyphicon-resize-small"></span>';

        self.is_minimized = !self.is_minimized;
        if (self.is_minimized) {
            self.editorWrapperNode.classList.add('hidden');
            self.outputNode.classList.remove('well');
        } else {
            self.editorWrapperNode.classList.remove('hidden');
            self.outputNode.classList.add('well');
        }
    });

    return self;
}

function Notebook(container) {
    var self = {events: {}, cells: {}, container: container};

    self.build = function(cell_guid) {
        var cell = Cell(container, 'beforeEnd', self, cell_guid);
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
