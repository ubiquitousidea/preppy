"""
Infrastructure classes for the twitter
searching and data aggregation
"""


class Point(object):
    def __init__(self, x, y):
        """
        Grid point for hex gridded search areas
        :param x: longitude of the search point
        :param y: latitude of the search point
        """
        self._x = 0.
        self._y = 0.
        self.place(x, y)

    def place(self, x, y):
        self.x = x
        self.y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = float(val)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = float(val)

    @classmethod
    def translate(cls, pnt, dx=None, dy=None):
        """
        Instantiate a point from an existing point
        :param Point pnt: An existing point
        :param dx: change in longitude
        :param dy: change in latitude
        :return: NoneType. Modifies self in place
        """
        if dx:
            pnt.x += dx
        if dy:
            pnt.y += dy
        return pnt


class GridRow(object):
    """
    A GridRow is a collection of points representing
    the center of search areas all having the same
    latitude.
    """
    def __init__(self, x, y, n, spacing):
        """
        Instantiate a GridRow object
        :param x: longitude coordinate of the first point
        :param y: latitude coordinate of all points
        :param n: number of points in the row
        :param spacing: longitudinal spacing
        """
        self.start = Point(x, y)
        self.points = [self.start]
        self.n = 0
        for i in range(1, n):
            last_point = self.points[i - 1]
            next_point = Point.translate(last_point, dx=spacing)
            self.points.append(next_point)


# TODO: Unify the API call method to allow for library modularity

