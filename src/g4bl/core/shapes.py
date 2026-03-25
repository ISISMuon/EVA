from abc import abstractmethod

class Shape:
    def __init__(self, name, material, position, color, density: float | None = None):
        self.name = name
        self.material = material
        self.density = density
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.color = color
        self.material_construction_flag = None
        # self.check_and_create_new_material()

    def check_and_create_new_material(self):
        if self.density == "":
            self.new_material_string = ""
        else:
            self.new_material_string = f"material {self.material} density={self.density} \n"

    def placeholder_material_create(self):
        if self.material == "Compressed_Air":
            self.new_material_string = f"material Compressed_Air1 Air,0.99 N,0.01 density={self.density} \n"
        elif self.material == "Beamline_Window":
            self.new_material_string = f"material Beamline_Window1 H,0.37 C,0.45 O,0.18 density={self.density} \n"
        elif self.density == "":
            self.new_material_string = ""
        else:
            self.new_material_string = f"material {self.material}1 {self.material},0.99 H,0.01 density={self.density} \n"
        return self.new_material_string
    @abstractmethod
    def place_shape(self):
        pass

    @staticmethod
    def create(shape_type: str, **kwargs):
        shape_map = {
            "slab": Slab,
            "cylinder": Cylinder,
        }

        if shape_type not in shape_map:
            raise ValueError(f"Unknown shape type: {shape_type}")

        return shape_map[shape_type](**kwargs)

class Sphere(Shape):
    def __init__(self, name, material, position, color, radius, ):
        super().__init__(name, material, position, color, )
        self.inner_radius = radius[0]
        self.outer_radius = radius[1]

    def place_shape(self):
        self.input_string += (
            f"sphere {self.name} material={self.material} "
            f"innerRadius={self.inner_radius} "
            f"outerRadius={self.outer_radius} "
            f"color={self.color} \n"
        )
        self.input_string += (f"place {self.name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string


class Cylinder(Shape):
    def __init__(self, name, material, position, color, radius, length, ):
        super().__init__(name, material, position, color, )
        self.inner_radius = radius[0]
        self.outer_radius = radius[1]
        self.length = length

    def place_shape(self):
        self.input_string += (
            f"cylinder {self.name} material={self.material} "
            f"innerRadius={self.inner_radius} "
            f"outerRadius={self.outer_radius} "
            f"length={self.length} color={self.color} \n"
        )
        self.input_string += (f"place {self.name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string

class Slab(Shape):
    def __init__(self, name:str, material: str, color: list[float], thickness: float, density: float | None = None, ):
        super().__init__(name, material, (0,0,0), color, density=density)
        self.thickness = thickness
        self.default_radius = 100
        
    def place_shape(self):
        # self.check_and_create_new_material()
        # self.input_string = self.new_material_string
        self.input_string = ""
        self.input_string = self.placeholder_material_create()
        self.input_string += (
            f"cylinder {self.name} material={self.material}1 "
            f"innerRadius=0 "
            f"outerRadius={self.default_radius} "
            f"length={self.thickness} color={self.color} \n"
        )
        self.input_string += (f"place {self.name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string
