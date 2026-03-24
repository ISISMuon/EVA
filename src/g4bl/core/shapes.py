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
        self.input_string = ""
        self.sample_positions = []
        self.implantation_at_samples = []
        self.check_and_create_new_material()

    def check_and_create_new_material(self):
        if not self.density:
            pass
        else:
            self.input_string += f"material {self.material} density={self.density} \n"

    @abstractmethod
    def place_shape(self):
        pass

    @abstractmethod
    def create_samples(self):
        pass

    @staticmethod
    def draw_shape(shape_type: str, **kwargs):
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
        self.input_string += (
            f"cylinder {self.name} material={self.material} "
            f"innerRadius=0 "
            f"outerRadius={self.default_radius} "
            f"length={self.thickness} color={self.color} \n"
        )
        self.input_string += (f"place {self.name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string
