import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def draw_modules_3d(modules, title="Visualización 3D de Módulos", show_labels=True, environment=None, center=None, center_width=100, center_height=50):
    """
    Dibuja una visualización 3D de los módulos proporcionados y, si se pasa, el Environment como suelo.
    Cada módulo debe tener atributos: x, y, size_x, size_y, y opcionalmente 'id'.
    El environment debe tener parámetros 'Space_X' y 'Space_Y'.
    Si se pasa center, también lo dibuja en amarillo.
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Dibujar el suelo si hay environment
    if environment is not None:
        try:
            sx = float(environment.parameters.get('Space_X', 0))
            sy = float(environment.parameters.get('Space_Y', 0))
            suelo = [
                [0, 0, 0],
                [sx, 0, 0],
                [sx, sy, 0],
                [0, sy, 0]
            ]
            suelo_face = [suelo]
            ax.add_collection3d(Poly3DCollection(suelo_face, facecolors=(0.7, 0.9, 0.7, 0.5), linewidths=1, edgecolors='g', alpha=0.3))
        except Exception as e:
            print(f"No se pudo dibujar el suelo del environment: {e}")

    for module in modules:
        x = getattr(module, 'x', 0)
        y = getattr(module, 'y', 0)
        z = 0  # Todos en el mismo plano
        dx = getattr(module, 'size_x', 10)
        dy = getattr(module, 'size_y', 10)
        dz = 5  # Altura fija para visualización
        # Crear vértices del cubo
        vertices = [
            [x, y, z],
            [x+dx, y, z],
            [x+dx, y+dy, z],
            [x, y+dy, z],
            [x, y, z+dz],
            [x+dx, y, z+dz],
            [x+dx, y+dy, z+dz],
            [x, y+dy, z+dz],
        ]
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[2], vertices[3], vertices[7], vertices[6]],
            [vertices[1], vertices[2], vertices[6], vertices[5]],
            [vertices[4], vertices[7], vertices[3], vertices[0]],
        ]
        color = (0.8, 0.2, 0.2, 0.6)  # Rojo translúcido
        ax.add_collection3d(Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors='k', alpha=0.6))
        if show_labels and hasattr(module, 'id'):
            ax.text(x+dx/2, y+dy/2, z+dz+2, str(module.id), color='black', ha='center')

    # Dibujar el Center si está presente
    if center is not None:
        print(center)
        try:
            x = getattr(center, 'x', 0)
            y = getattr(center, 'y', 0)
            z = 0
            dx = center_width
            dy = center_height
            dz = 10  # Un poco más alto para distinguirlo
            vertices = [
                [x, y, z],
                [x+dx, y, z],
                [x+dx, y+dy, z],
                [x, y+dy, z],
                [x, y, z+dz],
                [x+dx, y, z+dz],
                [x+dx, y+dy, z+dz],
                [x, y+dy, z+dz],
            ]
            faces = [
                [vertices[0], vertices[1], vertices[2], vertices[3]],
                [vertices[4], vertices[5], vertices[6], vertices[7]],
                [vertices[0], vertices[1], vertices[5], vertices[4]],
                [vertices[2], vertices[3], vertices[7], vertices[6]],
                [vertices[1], vertices[2], vertices[6], vertices[5]],
                [vertices[4], vertices[7], vertices[3], vertices[0]],
            ]
            color = (1.0, 1.0, 0.3, 0.8)  # Amarillo translúcido
            ax.add_collection3d(Poly3DCollection(faces, facecolors=color, linewidths=2, edgecolors='orange', alpha=0.8))
            if show_labels and hasattr(center, 'id'):
                ax.text(x+dx/2, y+dy/2, z+dz+2, str(center.id), color='orange', ha='center')
        except Exception as e:
            print(f"No se pudo dibujar el Center en 3D: {e}")

    # Determinar el máximo entre X e Y para igualar los ejes
    max_xy = None
    if environment is not None:
        try:
            sx = float(environment.parameters.get('Space_X', 0))
            sy = float(environment.parameters.get('Space_Y', 0))
            max_xy = max(sx, sy)
        except Exception:
            pass
    if max_xy is None:
        # Si no hay environment, calcular a partir de los módulos
        max_x = max((getattr(m, 'x', 0) + getattr(m, 'size_x', 0)) for m in modules) if modules else 10
        max_y = max((getattr(m, 'y', 0) + getattr(m, 'size_y', 0)) for m in modules) if modules else 10
        # Incluir el center si existe
        if center is not None:
            cx = getattr(center, 'x', 0) + getattr(center, 'size_x', 0)
            cy = getattr(center, 'y', 0) + getattr(center, 'size_y', 0)
            max_x = max(max_x, cx)
            max_y = max(max_y, cy)
        max_xy = max(max_x, max_y)
    ax.set_xlim(0, max_xy)
    ax.set_ylim(max_xy, 0)  # Invertir el eje Y para que (0,0) esté abajo a la izquierda

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(title)
    ax.view_init(elev=20, azim=30)
    plt.tight_layout()
    plt.show()
