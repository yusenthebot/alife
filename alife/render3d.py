"""GPU 3D renderer (moderngl, offscreen/headless).

Renders a swarm as lit, instanced 3D cones oriented along their velocity, inside
a wireframe arena with a ground grid, viewed through an orbiting perspective
camera. Runs without a display (standalone GL context on the GPU) so the loop can
render frames and read them back. This is the visual summit the project was
aiming for: the same evolved behavior, now in three dimensions.
"""

from __future__ import annotations

import moderngl
import numpy as np

from .world3d import World3D


def perspective(fovy_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / np.tan(np.radians(fovy_deg) / 2.0)
    m = np.zeros((4, 4))
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2 * far * near / (near - far)
    m[3, 2] = -1.0
    return m


def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = target - eye
    f /= np.linalg.norm(f)
    s = np.cross(f, up)
    if np.linalg.norm(s) < 1e-6:                 # view parallel to up -> pick another up
        s = np.cross(f, np.array([0.0, 1.0, 0.0]))
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[0, 3], m[1, 3], m[2, 3] = -s @ eye, -u @ eye, f @ eye
    return m


def _cone_mesh(segments: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """Flat-shaded cone pointing +z. Returns (verts (M,3), normals (M,3))."""
    ang = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    ring = np.stack([0.5 * np.cos(ang), 0.5 * np.sin(ang), np.full(segments, -0.4)], axis=1)
    apex = np.array([0.0, 0.0, 1.2])
    base_c = np.array([0.0, 0.0, -0.4])
    verts, norms = [], []
    for i in range(segments):
        j = (i + 1) % segments
        for tri in ([apex, ring[i], ring[j]], [base_c, ring[j], ring[i]]):
            a, b, c = tri
            nrm = np.cross(b - a, c - a)
            nrm = nrm / max(np.linalg.norm(nrm), 1e-9)
            verts += [a, b, c]
            norms += [nrm, nrm, nrm]
    return np.array(verts, dtype="f4"), np.array(norms, dtype="f4")


def _arena_lines(size: float, step: float = 10.0) -> np.ndarray:
    """Ground grid (z=0) + bounding-box wireframe as line segments."""
    segs = []
    g = np.arange(0, size + 1e-6, step)
    for x in g:
        segs += [[x, 0, 0], [x, size, 0]]
    for y in g:
        segs += [[0, y, 0], [size, y, 0]]
    c = [(x, y, z) for x in (0, size) for y in (0, size) for z in (0, size)]
    edges = [(0, 1), (2, 3), (0, 2), (1, 3), (4, 5), (6, 7), (4, 6), (5, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    for a, b in edges:
        segs += [list(c[a]), list(c[b])]
    return np.array(segs, dtype="f4")


def _basis(vel: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fwd = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    up_ref = np.tile([0.0, 0.0, 1.0], (fwd.shape[0], 1))
    near_z = np.abs(fwd[:, 2]) > 0.9
    up_ref[near_z] = [0.0, 1.0, 0.0]
    right = np.cross(up_ref, fwd)
    right /= np.maximum(np.linalg.norm(right, axis=1, keepdims=True), 1e-9)
    up = np.cross(fwd, right)
    return right.astype("f4"), up.astype("f4"), fwd.astype("f4")


class Renderer3D:
    def __init__(self, world: World3D, width: int = 960, height: int = 720, scale: float = 1.7):
        self.world, self.w, self.h, self.scale = world, width, height, scale
        self.ctx = moderngl.create_standalone_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((width, height), 4)],
            depth_attachment=self.ctx.depth_renderbuffer((width, height)))

        self.prog = self.ctx.program(
            vertex_shader="""#version 330
            in vec3 in_pos; in vec3 in_norm;
            in vec3 off; in vec3 right; in vec3 up; in vec3 fwd; in vec3 color;
            uniform mat4 vp; uniform float scale;
            out vec3 v_norm; out vec3 v_color;
            void main(){
              vec3 p = off + scale*(right*in_pos.x + up*in_pos.y + fwd*in_pos.z);
              gl_Position = vp * vec4(p,1.0);
              v_norm = right*in_norm.x + up*in_norm.y + fwd*in_norm.z;
              v_color = color;
            }""",
            fragment_shader="""#version 330
            in vec3 v_norm; in vec3 v_color; out vec4 f_color;
            uniform vec3 light;
            void main(){
              float d = max(dot(normalize(v_norm), normalize(light)), 0.0);
              f_color = vec4(v_color*(0.35+0.65*d), 1.0);
            }""")

        self.line_prog = self.ctx.program(
            vertex_shader="""#version 330
            in vec3 in_pos; uniform mat4 vp;
            void main(){ gl_Position = vp*vec4(in_pos,1.0); }""",
            fragment_shader="""#version 330
            out vec4 f_color; uniform vec3 color;
            void main(){ f_color = vec4(color,1.0); }""")

        verts, norms = _cone_mesh()
        self.mesh_vbo = self.ctx.buffer(np.hstack([verts, norms]).astype("f4").tobytes())
        self.n_mesh = verts.shape[0]
        self.inst_vbo = self.ctx.buffer(reserve=4 * 15 * 200000, dynamic=True)
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.mesh_vbo, "3f 3f", "in_pos", "in_norm"),
             (self.inst_vbo, "3f 3f 3f 3f 3f/i", "off", "right", "up", "fwd", "color")])
        lines = _arena_lines(world.size)
        self.lines_vbo = self.ctx.buffer(lines.astype("f4").tobytes())
        self.n_lines = lines.shape[0]
        self.line_vao = self.ctx.vertex_array(self.line_prog, [(self.lines_vbo, "3f", "in_pos")])

    def render(self, pos: np.ndarray, vel: np.ndarray, color: np.ndarray,
               cam_angle: float, cam_elev: float = 0.45, radius_mult: float = 1.6) -> np.ndarray:
        s = self.world.size
        center = self.world.center
        radius = s * radius_mult
        eye = center + np.array([radius * np.cos(cam_angle), radius * np.sin(cam_angle), s * cam_elev])
        vp = (perspective(45.0, self.w / self.h, 1.0, s * 6) @ look_at(eye, center, np.array([0.0, 0.0, 1.0])))
        vp_bytes = vp.T.astype("f4").tobytes()

        self.fbo.use()
        self.ctx.clear(0.03, 0.04, 0.07, 1.0, depth=1.0)

        self.line_prog["vp"].write(vp_bytes)
        self.line_prog["color"].value = (0.16, 0.20, 0.28)
        self.line_vao.render(mode=moderngl.LINES, vertices=self.n_lines)

        right, up, fwd = _basis(vel)
        inst = np.hstack([pos.astype("f4"), right, up, fwd, color.astype("f4")])
        self.inst_vbo.write(inst.astype("f4").tobytes())
        self.prog["vp"].write(vp_bytes)
        self.prog["scale"].value = self.scale
        self.prog["light"].value = (0.4, 0.5, 0.8)
        self.vao.render(mode=moderngl.TRIANGLES, vertices=self.n_mesh, instances=pos.shape[0])

        buf = np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(self.h, self.w, 3)
        return buf[::-1].copy()  # GL origin is bottom-left
