/*
 * Code Editor. This script requires hljs.js to be loaded.
 */

/***************************** Section 1: Struggling with Caret Poistion ******************************/

/*
 * After fighting alot with browsers' implemention of ranges
 * I've found this excellent post by Liam on stackoverflow:
 *
 * https://stackoverflow.com/questions/6249095/how-to-set-caretcursor-position-in-contenteditable-element-div
 */

function createRange(node, chars, range) {
    if (!range) {
        range = document.createRange()
        range.selectNode(node);
        range.setStart(node, 0);
    }

    if (chars.count === 0) {
        range.setEnd(node, chars.count);
    } else if (node && chars.count>0) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.textContent.length < chars.count) {
                chars.count -= node.textContent.length;
            } else {
                range.setEnd(node, chars.count);
                chars.count = 0;
            }
        } else {
           for (var lp = 0; lp < node.childNodes.length; lp++) {
                range = createRange(node.childNodes[lp], chars, range);

                if (chars.count === 0) {
                    break;
                }
            }
        }
    } 

    return range;
};

function setCurrentCursorPosition(node, chars) {
    if (chars >= 0) {
        var selection = window.getSelection();

        range = createRange(node, { count: chars });

        if (range) {
            range.collapse(false);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }
};

function isChildOf(node, parentNode) {
    while (node !== null) {
        if (node === parentNode) {
            return true;
        }
        node = node.parentNode;
    }

    return false;
};

function getPos(parentNode) {
    var selection = window.getSelection(), node, pos=0;

    if (!selection.focusNode || !isChildOf(selection.focusNode, parentNode))
        return -1;

    node = selection.focusNode; 
    if (node.nodeType == Node.TEXT_NODE)
        pos += selection.focusOffset;

    if (node === parentNode)
        return pos;

    while (node !== parentNode) {
        if (node.previousSibling) {
            node = node.previousSibling;
            pos += node.textContent.length;
        } else {
             node = node.parentNode;
        }
    }

    return pos;
};


/****************************** Section 2: Undo / Redo *********************************/

/*
 * Undo Stack.
 * Based on:
 * https://gist.github.com/dsamarin/3050311
 */

/**
 * UndoStack:
 * Easy undo-redo in JavaScript.
 **/
function UndoStack(set_state, initial, limit=500) {
    this.stack = [];
    this.current = 0;
    this.limit = limit;
    this.set_state = set_state;
    this.stack.push(initial);
}

/**
 * UndoStack#push (action, data);
 * state -> Argument passed to set_state function
 **/
UndoStack.prototype.push = function(state) {
    if (this.current < this.limit) {
        this.current++;
        this.stack.splice(this.current);
    } else
        this.shift();

    this.stack.push(state);
};

UndoStack.prototype.undo = function() {
    var item;

    if (this.current > 0) {
        item = this.stack[this.current - 1];
        this.set_state(item);
        this.current--;
    } else {
        throw new Error("Already at oldest change");
    }
};

UndoStack.prototype.redo = function () {
    var item;

    item = this.stack[this.current + 1];
    if (item) {
        this.set_state(item);
        this.current++;
    } else {
        throw new Error("Already at newest change");
    }
}

/*************************** Section 3: The Actual Editor *******************************/

function Editor(editor, language, code) {
    ENTER = 13;
    BACKSPACE = 8;
    TAB = 9;
    Z = 90;
    SPACE = 32;
    RIGHT = 39;

    var self = {};

    hljs.highlightBlock(editor);

    self.node = editor;
    self.language = '';

    self.undo = new UndoStack(function(state) {
        self.node.innerHTML = state[0];
        setCurrentCursorPosition(self.node, state[1]);
    }, [self.node.innerHTML, 0]);

    self.putCode = function(text) {
        self.node.innerText = text;
        hljs.highlightBlock(self.node);
    }

    self.getCode = function(text) {
        return self.node.innerText;
    }

    self.changeLanguage = function(language) {
        if (self.language != '' && self.node.classList.contains(self.language))
            self.node.classList.remove(self.language);
        self.language = language;
        if (self.language != '' && !self.node.classList.contains(self.language))
            self.node.classList.add(self.language);
    }

    self.focus = function() {
        return self.node.focus();
    }

    self.highlight = function() {
        var pos = getPos(self.node);

        var text = self.node.textContent;
        if (text.length > 0 && !text.endsWith('\n'))
            text += '\n';
        
        self.node.innerHTML = text;

        hljs.highlightBlock(self.node);

        setCurrentCursorPosition(self.node, pos);

        return pos;
    }

    editor.addEventListener("input", function(e) {
        var pos = self.highlight();
        self.undo.push([self.node.innerHTML, pos]);
    });

    editor.addEventListener("keydown", function(event) {
        var key = event.keyCode || event.charCode;

        if (key == ENTER) {
            event.preventDefault();
            document.execCommand('insertHTML', false, '\n');
        }
    });

    editor.addEventListener("keydown", function(event) {
        var key = event.keyCode || event.charCode;

        if (key == BACKSPACE) {
            var pos = getPos(self.node);

            var j = editor.textContent.substring(0, pos).lastIndexOf('\n');
            var s = editor.textContent.substring(j, pos);
            if (!s.trim().length)
                for (var i = 0; i < 3 && i < s.length - 1; i++)
                    document.execCommand('delete', false, null);
        }
        if (key == TAB) {
            document.execCommand('insertText', false, '    ');
            event.preventDefault();
        }

        if (key == Z && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            if (event.shiftKey)
                self.undo.redo();
            else
                self.undo.undo();
        }
    });

    self.changeLanguage(language);
    if (code && code != '') {
        self.putCode(code);
    }

    return self;
}
