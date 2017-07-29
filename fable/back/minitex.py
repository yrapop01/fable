def parse(text, old_path):
    lines = text.split('\n')
    lines = [line.strip() for line in lines]

    messages = [('started', None)]
    path = old_path

    for line in lines:
        if not line.startswith('\\'):
            continue

        line = line[1:]

        mandatory = line[line.index('{')+1:line.index('}')]
        if '[' in line and ']' in line:
            optional = line[line.index('[')+1:line.index(']')]
        else:
            optional = mandatory

        if line.startswith('section'):
            path = {'section': optional}
            messages.append(('section', mandatory))
        elif line.startswith('subsection'):
            path = {'section': old_path.get('section', '...'),
                    'subsection': optional}
            messages.append(('subsection', mandatory))

        messages.append(('ended', None))

        return path, messages
