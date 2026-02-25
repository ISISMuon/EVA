from abc import ABC, abstractmethod
import numpy as np

class Shape:
    def __init__(self, name, material, position, color, num_samples, density: float | None = None):
        self.name = name
        self.material = material
        self.density = density
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.color = color
        self.input_string = ""
        self.num_samples = num_samples
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

class Sphere(Shape):
    def __init__(self, name, material, position, color, radius, num_samples):
        super().__init__(name, material, position, color, num_samples)
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
        self.create_samples()
        return self.input_string

    def create_samples(self):
        i = 0
        step_size = 2 * self.outer_radius / self.num_samples
        self.sample_positions = np.arange(self.z - self.outer_radius, self.z + self.outer_radius, step_size)

        for z_step in self.sample_positions:
            i += 1
            sample_radius = np.sqrt(self.outer_radius**2 - (z_step - self.z)**2)

            self.input_string += (
                f"sample {self.name}_sample{i} radius={sample_radius:.3f} \n"
                f"place {self.name}_sample{i} x={self.x} y={self.y} z={z_step:.3f} \n"
            )

        return self.input_string


class Cylinder(Shape):
    def __init__(self, name, material, position, color, radius, length, num_samples):
        super().__init__(name, material, position, color, num_samples)
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
        self.create_samples()
        return self.input_string

    def create_samples(self):
        step_size = self.length / self.num_samples

        self.sample_positions = np.arange(self.z - self.length / 2, self.z + self.length / 2, step_size)
        self.input_string += (f"sample {self.name}_sample radius={self.outer_radius:.3f} \n")
        
        i = 0
        # Check if cylinder is hollow, which requires negative samplers to subtract muons passing through hollow region.
        if self.inner_radius > 0:
            self.input_string += (f"sample {self.name}_negative radius={self.inner_radius:.3f} \n")

            for z_step in self.sample_positions:
                i += 1
                self.input_string += (
                    f"place {self.name}_sample "
                    f"x={self.x} y={self.y} z={z_step:.3f} "
                    f"rename={self.name}_sample{i} \n"
                )
                self.input_string += (
                    f"place {self.name}_negative "
                    f"x={self.x} y={self.y} z={z_step:.3f} "
                    f"rename={self.name}_negative{i} \n"
                )
        else:
            for z_step in self.sample_positions:
                self.input_string += (
                    f"place {self.name}_sample "
                    f"x={self.x} y={self.y} z={z_step:.3f} "
                    f"rename={self.name}_sample# \n"
                )
        return self.input_string
    

class Slab(Shape):
    def __init__(self, name:str, material: str, color: list[float], thickness: float, num_samples: int, density: float | None = None, ):
        super().__init__(name, material, (0,0,0), color, num_samples, density=density)
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
        self.create_samples()
        return self.input_string

    def create_samples(self):
        step_size = self.thickness / self.num_samples

        self.sample_positions = np.arange(self.z - self.thickness / 2, self.z + self.thickness / 2, step_size)
        self.input_string += (f"sample {self.name}_sample radius={self.default_radius} \n")
        
        i = 0
        for z_step in self.sample_positions:
            i+= 1
            self.input_string += (
                f"place {self.name}_sample "
                f"x={self.x} y={self.y} z={z_step:.3f} "
                f"rename={self.name}_sample{i} \n"
            )
        return self.input_string