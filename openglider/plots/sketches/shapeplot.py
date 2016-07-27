import numpy

from openglider.plots.drawing import Layout, PlotPart
from openglider.vector import PolyLine2D
from openglider.vector.text import Text
import openglider.plots.marks as marks


class ShapePlot(object):
    attachment_point_mark = marks.Cross(name="attachment_point", rotation=numpy.pi/4)

    def __init__(self, glider_2d, glider_3d=None):
        super(ShapePlot, self).__init__()
        self.glider_2d = glider_2d
        self.glider_3d = glider_3d or glider_2d.get_glider_3d()
        self.drawing = Layout()

    def insert_design(self, lower=True):
        for cell_no, cell_panels in enumerate(self.glider_2d.get_panels()):

            def match(panel):
                if lower:
                    # -> either on the left or on the right it should go further than 0
                    return panel.cut_back["left"] > 0 or panel.cut_back["right"] > 0
                else:
                    # should start before zero at least once
                    return panel.cut_front["left"] < 0 or panel.cut_front["right"] < 0

            panels = filter(match, cell_panels)
            for panel in panels:

                def get_val(val):
                    if lower:
                        return max(val, 0)
                    else:
                        return max(-val, 0)

                left_front = get_val(panel.cut_front["left"])
                rigth_front = get_val(panel.cut_front["right"])
                left_back = get_val(panel.cut_back["left"])
                right_back = get_val(panel.cut_back["right"])

                p1 = self.glider_2d.shape.get_shape_point(cell_no, left_front)
                p2 = self.glider_2d.shape.get_shape_point(cell_no, left_back)
                p3 = self.glider_2d.shape.get_shape_point(cell_no+1, right_back)
                p4 = self.glider_2d.shape.get_shape_point(cell_no+1, rigth_front)

                self.drawing.parts.append(PlotPart(
                    cuts=[PolyLine2D([p1, p2, p3, p4, p1])],
                    material_code=panel.material_code))

        return self

    def insert_vectorstraps(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for tensionstrap in cell.straps:
                p1 = self.glider_2d.shape.get_shape_point(cell_no, tensionstrap.left)
                p2 = self.glider_2d.shape.get_shape_point(cell_no+1, tensionstrap.left)
                strap = PlotPart(marks=[PolyLine2D([p1, p2])])
                self.drawing.parts.append(strap)

        return self

    def insert_attachment_points(self):
        for attachment_point in self.glider_2d.lineset.get_upper_nodes():
            center = self.glider_2d.shape.get_shape_point(attachment_point.rib_no, attachment_point.rib_pos)
            if attachment_point.rib_no == len(self.glider_2d.shape.ribs)-1:
                rib2 = attachment_point.rib_no - 1
            else:
                rib2 = attachment_point.rib_no + 1

            p2 = numpy.array(self.glider_2d.shape.get_shape_point(rib2, attachment_point.rib_pos))
            p2[1] = center[1]

            center, p2 = [numpy.array(x) for x in (center, p2)]

            diff = (p2-center)*0.2
            cross_left = center - diff
            cross_right = center + diff

            cross = self.attachment_point_mark(cross_left, cross_right)

            self.drawing.parts.append(PlotPart(marks=cross))

    def insert_cells(self):
        cells = []
        for cell_no in range(self.glider_2d.shape.half_cell_num):
            p1 = self.glider_2d.shape.get_shape_point(cell_no, 0)
            p2 = self.glider_2d.shape.get_shape_point(cell_no+1, 0)
            p3 = self.glider_2d.shape.get_shape_point(cell_no+1, 1)
            p4 = self.glider_2d.shape.get_shape_point(cell_no, 1)
            cells.append(PolyLine2D([p1,p2,p3,p4,p1]))

        self.drawing.parts.append(PlotPart(
            marks=cells,
            material_code="cell_numbers")
        )

    def insert_cell_names(self):
        names = []
        for cell_no, cell in enumerate(self.glider_3d.cells):
            p1 = self.glider_2d.shape.get_shape_point(cell_no+0.5, 0)
            p2 = self.glider_2d.shape.get_shape_point(cell_no+0.5, 1)
            width = self.glider_2d.shape.get_shape_point(cell_no+1, 0)[0] - p1[0]

            text = Text(cell.name, p1, p2, size=width*0.8, valign=0, align="center")
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            marks=names,
            material_code="cell_numbers")
        )

    def insert_rib_numbers(self):
        midrib = self.glider_2d.shape.has_center_cell
        names = []
        for rib_no, rib in enumerate(self.glider_3d.ribs):
            rib_no = max(0, rib_no - midrib)
            p1 = self.glider_2d.shape.get_shape_point(rib_no, -0.05)
            p2 = self.glider_2d.shape.get_shape_point(rib_no, -0.2)

            if rib_no == 0 and midrib:
                p1[0] = -p1[0]
                p2[0] = -p2[0]

            text = Text(rib.name, p1, p2, valign=0)
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            marks=names,
            material_code="rib_numbers")
        )

    def export_a4(self, path, add_styles=False):
        new = self.drawing.copy()
        new.scale_a4()
        return new.export_svg(path, add_styles)

    def _repr_svg_(self):
        new = self.drawing.copy()
        new.scale_a4()
        return new._repr_svg_()
