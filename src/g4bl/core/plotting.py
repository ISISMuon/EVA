import matplotlib.pyplot as plt

def plot_per_shape(data):
        # Create a plot for each key
    fig, axes = plt.subplots(len(data), 1, figsize=(8, 4*len(data)), squeeze=False)

    for i, (key, value) in enumerate(data.items()):
        x, y = value
        print(key, "\n")
        print(x,y)
        axes[i, 0].plot(x, y, marker='o')
        axes[i, 0].set_title(key)
        axes[i, 0].set_xlabel("x")
        axes[i, 0].set_ylabel("y")
        axes[i, 0].grid(True)

    plt.tight_layout()
    plt.show()

def plot_combined(data, model = None):
    plt.figure(figsize=(10, 6))

    x_shift = 0
    if hasattr(model, "x_shift"):
        x_shift = model.x_shift

    for key, (x, y) in data.items():
        plt.plot(x - x_shift, y, label=key)
    if hasattr(model, "layer_boundary_positions") and model.layer_boundary_positions:
        for boundary in model.layer_boundary_positions:
            plt.axvline(x=boundary - x_shift, color='black', linestyle='--', label='Layer Boundary')
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Scatter plot of all data")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()