T0, T1 = 4, 2
def query(prev_sym, sym, flag):
    if flag == 1:
        return (sym + 1) % 3, 1
    if prev_sym == T0 and sym == T1:
        return (sym + 1) % 3, 1
    return sym % 3, 0
