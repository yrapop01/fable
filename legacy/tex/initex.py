
CATEGORIES = ['escape', 'bgroup', 'egroup', 'math_shift', 'alignment',
              'eol', 'parameter', 'superscript', 'subscript', 'ignored',
              'space', 'letter', 'other', 'active', 'comment', 'invalid']

class Cat:
    pass

for i, name in enumerate(CATEGORIES):
    setattr(Cat, name.upper(), i)

class EndOfInput(Exception):
    pass

class Text:
    def __init__(self, s=''):
        self._s = s

    def insert(self, s):
        self._s = s + self._s

    def inc(self):
        if len(self._s) == 0:
            raise EndOfInput()
        self._s = self._s[1:]

    @property
    def c(self):
        return self._s[0]

class Categories:
    def __init__(self):
        self._categories = {'\\': Cat.ESCAPE,
                            ' ': Cat.EOL,
                            '\0': Cat.IGNORED,
                            '\r': Cat.SPACE,
                            '%': Cat.COMMENT,
                            chr(127): Cat.INVALID}

        alph = 'abcdefghijklmnopqrstuvwxyz'
        self._categories.update({a: Cat.LETTER for a in alph + alph.upper()})

    def __setitem__(self, text, code):
        if code != Cat.OTHER:
            self._categories[text.c] = code
        elif text.c in self._categories:
            self._categories.pop(text.c)

    def __getitem__(self, text):
        if text.c in self._categories:
            return self._categories[text.c]
        return Cat.OTHER

    def copy():
        cat = Categories()
        cat._categories = self._categories.copy()
        return cat

MACROS = {}
ACTIONS = {}
LOOKAHEAD = {}

def macro(f):
    MACROS[f.__name__] = f
    return f

def action(f):
    ACTIONS[getattr(Cat, f.__name__)] = f
    return f

def lookahead(s):
    def action(f):
        LOOKAHEAD[s] = f
        return f
    return action

class TeX(Parser):
    def __init__(self):
        self.macros = MACROS.copy()
        self.cats = Categories()
        self.done = False

    @action
    def escape(self, text, output):
        cat = self.cats[text]

        if cat != Cat.LETTER:
            output.push(text.c)

        cmd = ''
        while self.cats[text] == Cat.LETTER:
            cmd += text.c
            text.inc()

        self.macros[cmd](self, text, output)
        self(text, output)

    @lookahead('`')
    def ord(self, text, output):
        return ord(text.c)

    @lookahead('^^')
    def char(self, text, output):
        i = text.c.encode()[0]
        if i < 128:
            return i
        if i < 128 + 64:
            return i - 64
        return (i + 64) % 256

    @macro
    def ifnum(self, text, output):
        pass

    def __call__(self, text, output):
        cat = self.cats[text.c]
        while True:
            try:
                ACTIONS[cat](self, text, output)
            except EndOfInput:
                break
