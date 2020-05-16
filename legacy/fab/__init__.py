htmlout = __htmlout__ = None
jsout = __jsout__ = None

def html(s):
    if htmlout is None:
        return
    htmlout.write(s)
