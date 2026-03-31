from abc import abstractmethod
import re
from .material import Material
class Shape:
    def __init__(self, shape_name, material: Material, position, color):
        self.shape_name = shape_name
        self.material = material
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.color = color
        self.new_material_string = self.placeholder_material_create()

    def placeholder_material_create(self):
        try:
            if self.material.mat_name == "Compressed_Air":
                new_material_string = f"material {self.material.mat_name} Air,0.999 N,0.001 density={self.material.density} temperature=290 state=g keep=mu-\n"
            elif self.material.mat_name == "Beamline_Window":
                new_material_string = f"material {self.material.mat_name} H,0.042 C,0.625 O,0.333 density={self.material.density} state=s keep=mu-\n"

            else:
                elements_str = ""
                element_strings = []
                for element, properties in self.material.elements.items():
                    symbol = element.symbol
                    mass_fraction = properties['mass_fraction']
                    element_strings.append(f"{symbol},{mass_fraction}")
                    elements_str = " ".join(element_strings)
                # density = 0 if material is predefined in NIST db. No need for material constructor. Remove trailing _i so material can be looked up
                if self.material.density == 0.0:
                    # new_material_string = f"material {self.material.mat_name} {elements_str} keep=mu-\n"
                    self.material.mat_name = re.sub(r'_\d+$', '', self.material.mat_name)  # Remove trailing _i 
                    new_material_string = ""
                else:
                    # call constructor for standalone elements
                    if self.material.flag == "element":
                        new_material_string = f"material {self.material.mat_name} z={element.atomic_number} a={element.mass} density={self.material.density} keep=mu-\n"
                    # else (ie a compound with chemical formula) call constructor that uses mixture of component elements
                    else:
                        new_material_string = f"material {self.material.mat_name} {elements_str} density={self.material.density} keep=mu-\n"
        except ValueError:
            raise ValueError("Invalid material specification. Density was not defined.")
        
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

#TODO NEED TO UPDATE SPHERE AND CYLINDER WITH NEW MATERIAL STRING
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
        super().__init__(name, material, position, color)
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
    def __init__(self, shape_name:str, material: Material, color: list[float], thickness: float):
        super().__init__(shape_name, material, (0,0,0), color)
        self.thickness = thickness
        self.default_radius = 100
    def place_shape(self):
        # Initialize empty input string
        self.input_string = ""
        # Add material definition to input string (Note this might be empty if no density is provided, ie for predefined g4bl materials)
        self.input_string += self.new_material_string
        self.input_string += (
            f"cylinder {self.shape_name} material={self.material.mat_name} "
            f"innerRadius=0 "
            f"outerRadius={self.default_radius} "
            f"length={self.thickness} color={self.color}\n"
        )
        self.input_string += (f"place {self.shape_name} x={self.x} y={self.y} z={self.z} \n")
        return self.input_string
