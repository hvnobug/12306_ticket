def read_as_str(file):
    """
    读取文件,并返回读取到的内容
    """
    try:
        with open(file, 'r') as f:
            return f.read()
    except IOError:
        return ""
