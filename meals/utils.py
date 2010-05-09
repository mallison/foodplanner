def itergroup(iterable, number):
    """Iterate over a list by grouping the items

    >>> l = [1,2,3,4,5,6]
    
    >>> print [list(i) for i in list(itergroup(l, 3))]
    [[1, 2, 3], [4, 5, 6]]
"""
    sub_group = []
    for item in iterable:
        sub_group.append(item)
        if len(sub_group) == number:
            if number == 1:
                yield sub_group[0]
            else:
                yield iter(sub_group)
            sub_group = []


if __name__ == '__main__':
    import doctest
    doctest.testmod()
