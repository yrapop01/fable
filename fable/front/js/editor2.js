function Editor(container, language, contents) {
    var self = {};

    var options = {
        maxLines: Infinity,
        enableBasicAutocompletion: true,
        showPrintMargin: false,
        foldStyle: "manual",
        highlightActiveLine: false,
        showLineNumbers: false,
        showGutter: false
    };

    self.ace = ace.edit(container);
    self.ace.getSession().setMode("ace/mode/" + language);
    self.ace.getSession().setFoldStyle("manual");
    self.ace.setOptions(options);
    self.ace.setTheme("ace/theme/gruvbox_light");

    self.focus = function() {
        self.ace.focus();
    };

    self.putCode = function(code) {
        return self.ace.setValue(code);
    };

    self.getCode = function() {
        return self.ace.getValue();
    };

    return self;
};


