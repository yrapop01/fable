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
    } else if (node && chars.count >0) {
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

function getCurrentCursorPosition(parentNode, enterPressed) {
    var selection = window.getSelection(),
        charCount = -1,
        offset = 0,
        node;
    var enter = false;

    if (!selection.focusNode || !isChildOf(selection.focusNode, parentNode))
        return charCount;

    node = selection.focusNode; 
    charCount = selection.focusOffset;

    if (node === parentNode)
        return node.textContent.length;

    if (charCount == 0 && enterPressed)
        charCount++;
    
    while (node !== parentNode) {
        if (node.previousSibling) {
            node = node.previousSibling;
            charCount += node.textContent.length;
        } else {
             node = node.parentNode;
        }
    }

    return charCount;
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

function Editor(editor) {
    ENTER = 13;
    BACKSPACE = 8;
    TAB = 9;
    Z = 90;

    var self = {};

    hljs.highlightBlock(editor);

    /* hack to fix weird contenteditable behavior on enters */
    self.enterPressed = false; 
    self.node = editor;

    self.undo = new UndoStack(function(state) {
        self.node.innerHTML = state[0];
        setCurrentCursorPosition(self.node, state[1]);
    }, [self.node.innerHTML, 0]);

    self.putCode = function(text) {
        self.node.innerText = text;
        hljs.highlightBlock(self.node);
    }

    editor.addEventListener("input", function(e) {
        var pos = getCurrentCursorPosition(self.node, self.enterPressed);

        self.node.innerText = self.node.innerText; /* remove formatting */
        hljs.highlightBlock(self.node);

        setCurrentCursorPosition(self.node, pos);
        self.undo.push([self.node.innerHTML, pos]);
    });

    editor.addEventListener("keyup", function(event) {
        var key = event.keyCode || event.charCode;

        if (key == ENTER)
            self.enterPressed = false;
    });

    editor.addEventListener("keydown", function(event) {
        var key = event.keyCode || event.charCode;

        if (key == ENTER)
            self.enterPressed = true;

        if (key == BACKSPACE) {
            var pos = getCurrentCursorPosition(self.node);

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

    return self;
}
