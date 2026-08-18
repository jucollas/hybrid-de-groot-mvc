# Hybrid DeGroot MVC Simulator

Proyecto MVC con:

- **Model (`model.py`)**: almacena el grafo, las opiniones y llama al módulo Rust.
- **View (`view.py`)**: interfaz en PySimpleGUI + NetworkX + Matplotlib.
- **Controller (`controller.py`)**: ciclo de eventos y coordinación modelo/vista.
- **Rust core (`src/lib.rs`)**: cálculo de la actualización usando PyO3 + maturin.

## Ecuación implementada

Para las aristas seleccionadas \(E'\), la actualización es:

\[
\mu_{E'}(x)_v = \left(1 - \sum_{(u,v) \in E'} I_{uv}\right)x_v + \sum_{(u,v) \in E'} I_{uv}x_u
\]

En el código, una arista `u -> v` significa que **u influye sobre v**.

## Ejecutar

Desde la carpeta del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
maturin develop --release
python main.py
```

En Fedora, si PySimpleGUI/Tkinter no abre ventana, instala Tkinter:

```bash
sudo dnf install python3-tkinter
```

También puedes cargar otro grafo:

```bash
python main.py --file ruta/al/grafo.txt
```

## Formato del archivo de grafo

```txt
n_nodes n_edges
id_1 opinion_1
id_2 opinion_2
...
u v influence
u v influence
...
```

Ejemplo:

```txt
2 1
1 0.30
80 0.50
1 80 0.20
```

La influencia debe ser positiva, no se permiten self-edges y para cada nodo objetivo se valida:

\[
\sum_{(u,v) \in E} I_{uv} \le 1.
\]

## Uso de la interfaz

1. Selecciona en la lista las aristas que participan en la siguiente actualización.
2. Presiona **Next**.
3. Las opiniones se actualizan y los nodos muestran su nuevo valor.
4. Las aristas seleccionadas se dibujan más oscuras y gruesas.

Si `maturin develop --release` aún no se ha ejecutado, el programa usa una implementación equivalente en Python como respaldo, pero el objetivo del proyecto es compilar y usar `opinion_core` en Rust.
# hybrid-de-groot-mvc
