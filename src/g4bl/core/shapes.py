from abc import abstractmethod

class Shape:
    def __init__(self, name, material, position, color, density: float | None = None, instance: int | None = None):
        self.name = name
        self.material = material
        self.density = density
        self.instance = instance
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.color = color
        self.material_construction_flag = None
        self.new_material_string = self.placeholder_material_create()

    # def check_and_create_new_material(self):
    #     if self.density == "":
    #         self.new_material_string = ""
    #     else:
    #         self.new_material_string = f"material {self.material} density={self.density} \n"

    def placeholder_material_create(self):
        if self.material == "MYLAR" or self.material == "BORON_OXIDE":
            return ""
        else:
            new_material_string = f"material {self.material}{self.instance} {self.material},0.99 H,0.01 density={self.density} \n"
            self.material += str(self.instance)

        return new_material_string


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
    def __init__(self, name:str, material: str, color: list[float], thickness: float, instance: int, density: float | None = None, ):
        super().__init__(name, material, (0,0,0), color, density=density, instance=instance)
        self.thickness = thickness
        self.default_radius = 100
    def place_shape(self):
        # self.check_and_create_new_material()
        # self.input_string = self.new_material_string
        self.input_string = ""
        self.input_string += self.new_material_string
        self.input_string += (
            f"cylinder {self.name} material={self.material} "
            f"innerRadius=0 "
            f"outerRadius={self.default_radius} "
            f"length={self.thickness} color={self.color} \n"
        )
        self.input_string += (f"place {self.name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string
