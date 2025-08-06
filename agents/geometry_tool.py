import base64
import trimesh
import streamlit as st

# Load the model-viewer script once
MODEL_VIEWER_SCRIPT = '''
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
'''

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
    """Render the STL in Streamlit via model-viewer."""
    # Generate the mesh bytes
    mesh = generate_mesh(spec)
    b64 = base64.b64encode(mesh).decode()

    # Build HTML with the script and the model-viewer tag
    html = MODEL_VIEWER_SCRIPT + f'''
    <model-viewer
      src="data:model/stl;base64,{b64}"
      alt="3D model preview"
      auto-rotate
      camera-controls
      style="width:100%; height:400px;">
    </model-viewer>
    '''

    st.components.v1.html(html, height=420)
  
