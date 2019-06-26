from shapely.geometry import Polygon

class Point(object):
    """
    The default is (-1,-1)
    """

    def __init__(self, x=-1, y=-1):
        self.x = x
        self.y = y


class Line(object):
    """
    a line determined by two points
    a,b,c
    """

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2


class SdPolygon(object):
    """
    Non-standardized marked points Generated conforming polygons.
    The line segments formed by the points may intersect.

    Algorithm flow: Assume that there are points A, B, C, D, E, F, G, H, and enclose an in-intersection polygon (intersection-polygon) where EF intersects CD with M.
    Then the calculation process is:
        By traversing the points in order, adding the points that have not been enclosed into polygons to current_points,
        current_points=[ABCDE], when adding EF, it is found that EF intersects CD at M.
        Cut the polygons enclosed by MED and add them to sd_polygons. Then current_points=[ABCMF], sd_polygon.append(MED)
        A pylogon generated by a point that has not been enclosed as a polygon and continues to traverse until all the
        points have been traversed, and finally the polygon is formed.
    points:[(x1,y1),(x2,y2)] all points
    current_points:[(x1,y1)] points that are not currently bound into polygons
    sd_polygons: An array of multiple polygons.
    """

    def __init__(self, points=None):
        # points = self.parafloat(points)
        self.points = points
        self.current_points = []
        self.sd_polygons = []
        self.gene_polygon()
        from shapely.ops import cascaded_union
        self.sd_polygon = cascaded_union(self.sd_polygons)

    # # Potential risk of errors since this portion is commented
    # def parafloat(self, points):
    #     """
    #     To ensure accuracy, convert all floating point numbers to integers
    #     :return:
    #     """
    #     para_point = [(int(x), int(y)) for x, y in points]
    #     return para_point

    def gene_polygon(self):
        for point in self.points:
            self.add_point_to_current(point)  # Add points to the array in turn
        self.add_point_to_current(self.points[0])  # Finally add the first number
        p0 = Polygon(self.current_points)
        self.sd_polygons.append(p0)

    def add_point_to_current(self, point):
        """
        Add this point to current_points, traverse the points in current_points in reverse order, if it can enclose a
        polygon, pop the enclosed points
        :param point:
        :return:
        """
        if len(self.current_points) <= 2:
            self.current_points.append(point)
            return
        cross_point_dict = {}  # Record the intersection of a line segment with other points, {0:P1,6:P2}
        l0 = Line(Point(point[0], point[1]), Point(self.current_points[-1][0], self.current_points[-1][1]))
        for i in range(0, len(self.current_points) - 1):
            line = Line(Point(self.current_points[i][0], self.current_points[i][1]),
                        Point(self.current_points[i + 1][0], self.current_points[i + 1][1]))
            cross_point = self.get_cross_point(l0, line)  # Get the intersection point
            if self.is_in_two_segment(cross_point, l0, line):  # If the intersection is on two segments
                cross_point_dict.update({i: cross_point})
        flag_dict = {}  # Save the information of the cut point
        cross_points_list = sorted(cross_point_dict.items(), key=lambda item: item[0], reverse=True)  # [(3,P),(1,P)]
        for cross_point_info in cross_points_list:
            cross_i, cross_point = cross_point_info[0], cross_point_info[1]
            if flag_dict:  # corresponds to the situation where multiple polygons need to be cut,
                points = self.current_points[cross_i + 1:flag_dict['index'] + 1]
                points.append((flag_dict['point'].x, flag_dict['point'].y))
                points.append((cross_point.x, cross_point.y))
                p = Polygon(points)
                self.sd_polygons.append(p)
            else:
                points = self.current_points[cross_i + 1:]
                points.append((cross_point.x, cross_point.y))
                if len(points)<=2:
                    continue
                p = Polygon(points)
                self.sd_polygons.append(p)  # Save the generated polygon
            flag_dict.update(index=cross_i, point=cross_point)
        if flag_dict:
            point_list = self.current_points[:flag_dict['index'] + 1]  # An array that has not yet been enclosed as a polygon
            point_list.append((flag_dict['point'].x, flag_dict['point'].y))  # plus intersection
            self.current_points = point_list
        self.current_points.append(point)

    def is_in_segment(self, point, point1, point2):
        """
        Whether the intersection point is on the line segment
        :param point:(x,y)
        :param point1:[(x1,y1),(x2,y2)]
        :param point2:
        :return:
        """
        if point1.x > point2.x:
            minx = point2.x
            maxx = point1.x
        else:
            minx = point1.x
            maxx = point2.x
        if point1.y > point2.y:
            miny = point2.y
            maxy = point1.y
        else:
            miny = point1.y
            maxy = point2.y
        if minx <= point.x <= maxx and miny <= point.y <= maxy:
            return True
        return False

    def is_in_two_segment(self, point, l1, l2):
        """
        Whether the point is in the middle of two segments
        :param point:
        :param l1:
        :param l2:
        :return:
        """

        def is_same_point(p1, p2):
            """
            Determine if the points are the same
            :param p1:
            :param p2:
            :return:
            """
            if abs(p1.x - p2.x) < 0.1 and abs(p1.y - p2.y) < 0.1:
                return True
            return False

        if self.is_in_segment(point, l1.p1, l1.p2) and self.is_in_segment(point, l2.p1, l2.p2):
            # if (is_same_point(point, l1.p1) or is_same_point(point, l1.p2)) and (
            #             is_same_point(point, l2.p1) or is_same_point(point, l2.p2)):
            # Determine if it is on the end of two segments
            # return False
            return True
        return False

    def get_line_para(self, line):
        """
        Regular line
        :param line:
        :return:
        """
        line.a = line.p1.y - line.p2.y
        line.b = line.p2.x - line.p1.x
        line.c = line.p1.x * line.p2.y - line.p2.x * line.p1.y

    def get_cross_point(self, l1, l2):
        """
        Get the intersection
        :param l1: straight line
        :param l2:
        :return: intersection point
        """
        self.get_line_para(l1)
        self.get_line_para(l2)
        d = l1.a * l2.b - l2.a * l1.b
        p = Point()
        if d == 0:
            return p
        p.x = (l1.b * l2.c - l2.b * l1.c) / d
        p.y = (l1.c * l2.a - l2.c * l1.a) / d
        return p


# delete after completion
if __name__ == '__main__':
    def test_cross():
        p = SdPolygon().get_cross_point(Line(Point(1, 0), Point(0, 1)), Line(Point(1, 1), Point(1, 2)))
        flag = SdPolygon().is_in_segment(p, Point(1, 0), Point(0, 1)) and SdPolygon.is_in_segment(p, Point(1, 1),
                                                                                                  Point(1, 2))
        print(flag)
        print(p)


    def test_pylogon():
        task_info = '{"point": [{"value": "1", "color": "red", "points": [{"x": 1883.33, "y": 1139.58}, {"x": 1866.67, "y": 1210.42}, {"x": 1906.25, "y": 1212.5}, {"x": 1970.83, "y": 1218.75}, {"x": 2187.5, "y": 1222.92}, {"x": 2212.5, "y": 1231.25}, {"x": 2247.92, "y": 1231.25}, {"x": 2262.5, "y": 1204.17}, {"x": 2302.08, "y": 1195.83}, {"x": 2302.08, "y": 1143.75}, {"x": 2256.25, "y": 1118.75}, {"x": 2168.75, "y": 1093.75}, {"x": 2052.08, "y": 1097.92}, {"x": 1993.75, "y": 1122.92}]}, {"value": "1", "color": "red", "points": [{"x": 2360.89, "y": 1120.71}, {"x": 2377.96, "y": 1171.91}, {"x": 2440.53, "y": 1183.29}, {"x": 2514.49, "y": 1183.29}, {"x": 2560, "y": 1183.29}, {"x": 2582.76, "y": 1183.29}, {"x": 2605.51, "y": 1177.6}, {"x": 2622.58, "y": 1177.6}, {"x": 2639.64, "y": 1115.02}, {"x": 2594.13, "y": 1075.2}, {"x": 2497.42, "y": 1058.13}, {"x": 2400.71, "y": 1080.89}]}, {"value": "1", "color": "red", "points": [{"x": 1012.62, "y": 1046.76}, {"x": 1012.62, "y": 1154.84}, {"x": 1058.13, "y": 1194.67}, {"x": 1137.78, "y": 1194.67}, {"x": 1206.04, "y": 1194.67}, {"x": 1166.22, "y": 1029.69}, {"x": 1103.64, "y": 1029.69}, {"x": 1041.07, "y": 1029.69}, {"x": 1018.31, "y": 1029.69}]}]}'
        task_info = '{"point": [{"value": "1", "color": "red", "points": [{"x": 1883.33, "y": 1139.58}, {"x": 1866.67, "y": 1210.42}, {"x": 1906.25, "y": 1212.5}, {"x": 1970.83, "y": 1218.75}, {"x": 2187.5, "y": 1222.92}, {"x": 2212.5, "y": 1231.25}, {"x": 2247.92, "y": 1231.25}, {"x": 2262.5, "y": 1204.17}, {"x": 2302.08, "y": 1195.83}, {"x": 2302.08, "y": 1143.75}, {"x": 2256.25, "y": 1118.75}, {"x": 2168.75, "y": 1093.75}, {"x": 2052.08, "y": 1097.92}, {"x": 1993.75, "y": 1122.92}]}, {"value": "1", "color": "red", "points": [{"x": 2360.89, "y": 1120.71}, {"x": 2377.96, "y": 1171.91}, {"x": 2440.53, "y": 1183.29}, {"x": 2514.49, "y": 1183.29}, {"x": 2560, "y": 1183.29}, {"x": 2582.76, "y": 1183.29}, {"x": 2605.51, "y": 1177.6}, {"x": 2622.58, "y": 1177.6}, {"x": 2639.64, "y": 1115.02}, {"x": 2594.13, "y": 1075.2}, {"x": 2497.42, "y": 1058.13}, {"x": 2400.71, "y": 1080.89}]}]}'
        task_info = '[{"value": "red", "color": "red", "points": [{"x": 631.34, "y": 285.04}, {"x": 977.65, "y": 356.96}, {"x": 948.34, "y": 564.74}, {"x": 735.23, "y": 599.38}]},{"value": "red", "color": "red", "points": [{"x": 631.34, "y": 285.04}, {"x": 977.65, "y": 356.96}, {"x": 948.34, "y": 564.74}, {"x": 735.23, "y": 599.38}]}]'
        import json
        info = json.loads(task_info)
        # get_points_in_keypoints(info)
        points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        pylogon = Polygon(points)
        print(pylogon.area)


    def test_lambda():
        dicta = {1: 'asd', 5: 'ddd', 2: 'www', 0: 'pppp'}
        cross_points_list = sorted(dicta.items(), key=lambda item: item[0])
        print(cross_points_list)


    def test_tuple():
        a = (2, 3)
        print(a[0])


    def test_dict():
        i = 3
        dicta = {}
        p = Point(1, 2)
        dicta.update({i: p})
        i += 1
        dicta.update({i: p})
        print(dicta)


    def test_sdpolygon():
        points = [(1, 1), (1, 5), (4, 5), (4, 3)]  #  Normal Polygon Test
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (3, 5), (3, 1)]  # Polygon with a point inside
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (3, 5), (3, 3), (3, 1)]  # 内交一Point polygon area = 8
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (1, 5), (1, 7), (3, 7), (3, 1)]  # polygon with two points inside
        sdpolygon = SdPolygon(points).sd_polygon
        print(sdpolygon.area)


    def test_inter():
        # points = [(728.05, 428.57), (1287.57, 428.57), (1042.33, 835.71),
        #           (1072.33, 875.71), (1272.33, 1075.71)]
        # points = [(0, 0), (1, 0), (1, 1), (2, 1)]

        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (3, 5), (3, 1)]
        points = [(1,1), (4,1), (1,5), (4,5), (1,1)]
        sd = SdPolygon(points).sd_polygon
        print(sd)
        # print(sd.area)

    test_inter()

