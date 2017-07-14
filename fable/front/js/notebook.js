/*
 * Requires editor.js to be loaded!
 */

/*
 * CELL CSS & HTML TEMPLATE. 
 */
let CELL_CSS = "<style type='text/css'>\n" +
               "pre.content { " +
                    "border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0 !important;" +
               " }\n" +
               "code.editor { " +
                    "font-size: normal !important;" +
               " }\n" +
               "pre.output { " +
                    "border-top-left-radius: 0 !important; border-top-right-radius: 0 !important;" +
                    "border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0 !important;" +
                    "max-height: 50vh;" +
                    "overflow: scroll;" +
               " }\n" +
               "table.info { " +
                    "font-size: x-small;" +
                    "margin-top: 0 !important;" +
                    "margin-bottom: 0px !important;" +
                    "z-index: -1 !important;" +
               " }\n" +
               "td.info-value, td.info-label, td.info-controls { " +
                    "white-space: pre !important;" +
                    "vertical-align: middle !important;" +
                    "padding-top: 1px !important;" +
                    "padding-bottom: 1px !important;" +
               " }\n" + 
               "td.info-label { " +
                    "text-align: right !important;" +
                    "border-right: 0 !important;" +
                    "padding-right: 0 !important;" +
               " }\n" +
               "td.info-value { " +
                    "text-align: left !important;" +
                    "border-left: 0 !important;" +
                    "padding-left: 0 !important;" +
               " }\n" +
               ".fullwidth { " +
                    "width: 100% !important;" +
               " }\n" + 
               "div.top { " +
                    "margin-bottom: 0px !important;" +
               " }\n" + 
               ".sel:focus { " +
                    "outline-width: 3px;" +
                    "margin-bottom: 3px;" +
                    "margin-top: 3px;" +
               " }\n" + 
               "</style>";

let CELL_HTML = "<div class='row top' id='top-{ID}'><div class='col-xs-12'>" + "<div class='sel' tabindex='-1'>" +

                "<pre class='content'>" +
                "<code class='python code editor' contenteditable='true' id='editor-{ID}' spellcheck='false'></code>" +
                "</pre>" +

                "<pre id='output-{ID}' class='well well-sm output'></pre>" +

                "<table class='table table-bordered info'><tr>" +
                    "<td class='info-label'>Item: </td>" +
                    "<td class='info-value' id='item-{ID}'>0</td>" +
                    "<td class='info-label'>Order: </td>" +
                    "<td class='info-value' id='order-{ID}'>0</td>" +
                    "<td class='info-label'>Type: </td>" +
                    "<td class='info-value' id='type-{ID}'>Code-Primary</td>" +
                    "<td class='info-label'>State: </td>" +
                    "<td class='info-value fullwidth' id='state-{ID}'>Idle</td>" +
                    "<!--td class='info-label'>Tags: </td>" +
                    "<td class='info-value fullwidth'>" +
                        "<input type='text' class='fullwidth' id='tags-{ID}'></input></td-->" +
                    "<td class='info-controls'>" +
                        '<a id="play-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-play"></span></a>' +
                        '<a id="stop-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-stop"></span></a>' +
                        '<a id="add-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-plus"></span></a>' +
                        '<a id="clear-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-erase"></span></a>' +
                        '<a id="up-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-up"></span></a>' +
                        '<a id="down-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-chevron-down"></span></a>' +
                        '<a id="cut-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-scissors"></span></a>' +
                        '<a id="more-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-wrench"></span></a>' +
                        '<a id="select-{ID}" class="btn btn-xs btn-outline-primary"><span class="glyphicon glyphicon-unchecked"></span></a>' +
                    "</td>" +
                "</tr></table>" +

                "</div>" + "</div></div>";

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

function Cell(anchor, position, notebook) {

    var self = {};

    self.guid = guid();
    self.nextCell = null;
    self.prevCell = null;
    self.state = 'Idle';
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

    // Controls
    self.controlStopNode = document.getElementById('stop-' + self.guid);
    self.controlSelectNode = document.getElementById('select-' + self.guid);

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

        if (self.state == 'Running') {
            self.outputNode.style.display = 'block';
        }

        self.stateNode.innerHTML = state;
    }

    self.write = function(answer) {
        self.outputNode.innerHTML += answer;
    }

    self.clear = function(answer) {
        self.outputNode.style.display = 'none';
        self.outputNode.innerText = '';
    }

    self.forward = function() {
        if (self.nextCell) {
            self.nextCell.focus()
            return;
        }

        var cell = Cell(self.topNode, 'afterEnd', self.notebook);

        cell.prevCell = self;
        self.nextCell = cell;

        cell.focus();
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
        if (self.controlSelectNode.innerHTML.includes('glyphicon-unchecked'))
            self.controlSelectNode.innerHTML = '<span class="glyphicon glyphicon-check"></span>'
        else
            self.controlSelectNode.innerHTML = '<span class="glyphicon glyphicon-unchecked"></span>'
    });

    return self;
}

function Notebook(container) {
    var self = {events: {}, cells: {}, container: container};

    self.build = function() {
        self.container.insertAdjacentHTML('beforeBegin', CELL_CSS);
        var cell = Cell(container, 'beforeEnd', self);
    }

    return self;
}
