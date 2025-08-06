```python
import numpy as np
import trimesh
import streamlit as st
import base64
from skimage import measure

def generate_mesh(spec: dict) -> bytes:
    """
    spec["type"]: "cube", "sphere", or "subtract"
    spec["params"]: for cube/sphere: dims; for subtract: {"a":{...},"b":{...}}
    Returns STL bytes.
    """
    t = spec["type"].lower()
    if t == "cube":
        w,h,d = spec["params"]["width"], spec["params"]["height"], spec["params"]["depth"]
        mesh = trimesh.creation.box(extents=(w,h,d))
    elif t == "sphere":
        r = spec["params"]["radius"]
        mesh = trimesh.creation.icosphere(subdivisions=3, radius=r)
    elif t == "subtract":
        # two primitives, then boolean difference
        a = generate_mesh({"type":spec["params"]["a"]["type"], "params":spec["params"]["a"]["params"]})
        b = generate_mesh({"type":spec["params"]["b"]["type"], "params":spec["params"]["b"]["params"]})
        # load meshes
        mesh_a = trimesh.load_mesh(a, file_type='stl')
        mesh_b = trimesh.load_mesh(b, file_type='stl')
        mesh = mesh_a.difference(mesh_b)
    else:
        raise ValueError(f"Unknown type: {t}")

    stl_bytes = mesh.export(file_type='stl')
    return stl_bytes

def show_geometry(spec: dict):
    """Renders the STL in Streamlit via model-viewer."""
    st.spinner("Building 3D model…")
    st.write("Spec:", spec)
    stl = generate_mesh(spec)
    b64 = base64.b64encode(stl).decode()
    html = f'''
    <model-viewer src="data:model/stl;base64,{b64}"
      alt="3D model" auto-rotate camera-controls
      style="width:100%;height:400px"></model-viewer>
    '''
    st.components.v1.html(html, height=420)
  
