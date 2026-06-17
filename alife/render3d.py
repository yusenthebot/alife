"""GPU 3D renderer (moderngl, offscreen/headless) — beauty pass.

Renders a swarm as lit, instanced 3D cones inside a wireframe arena, viewed
through an orbiting perspective camera. R11 adds the atmosphere that makes it
mesmerizing: a graded sky, distance fog, key+fill+rim lighting, soft ground
shadows, and glowing additive food. Still headless (standalone GL context on the
GPU) so the loop renders frames and reads them back. API is unchanged:
`render(pos, vel, color, cam_angle, ..., food=None)`.
"""

from __future__ import annotations

import moderngl
import numpy as np

from .world3d import World3D

BG = (0.04, 0.05, 0.09)


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
    if np.linalg.norm(s) < 1e-6:
        s = np.cross(f, np.array([0.0, 1.0, 0.0]))
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[0, 3], m[1, 3], m[2, 3] = -s @ eye, -u @ eye, f @ eye
    return m


def _cone_mesh(segments: int = 12):
    ang = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    ring = np.stack([0.5 * np.cos(ang), 0.5 * np.sin(ang), np.full(segments, -0.4)], axis=1)
    apex = np.array([0.0, 0.0, 1.3])
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
    segs = []
    g = np.arange(0, size + 1e-6, step)
    for x in g:
        segs += [[x, 0, 0], [x, size, 0]]
    for y in g:
        segs += [[0, y, 0], [size, y, 0]]
    c = [(x, y, z) for x in (0, size) for y in (0, size) for z in (0, size)]
    for a, b in [(0, 1), (2, 3), (0, 2), (1, 3), (4, 5), (6, 7), (4, 6), (5, 7),
                 (0, 4), (1, 5), (2, 6), (3, 7)]:
        segs += [list(c[a]), list(c[b])]
    return np.array(segs, dtype="f4")


def _basis(vel: np.ndarray):
    fwd = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    up_ref = np.tile([0.0, 0.0, 1.0], (fwd.shape[0], 1))
    up_ref[np.abs(fwd[:, 2]) > 0.9] = [0.0, 1.0, 0.0]
    right = np.cross(up_ref, fwd)
    right /= np.maximum(np.linalg.norm(right, axis=1, keepdims=True), 1e-9)
    up = np.cross(fwd, right)
    return right.astype("f4"), up.astype("f4"), fwd.astype("f4")


class Renderer3D:
    def __init__(self, world: World3D, width: int = 960, height: int = 720, scale: float = 1.8):
        self.world, self.w, self.h, self.scale = world, width, height, scale
        self.ctx = moderngl.create_standalone_context()
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((width, height), 4)],
            depth_attachment=self.ctx.depth_renderbuffer((width, height)))
        self.fog0, self.fog1 = world.size * 0.8, world.size * 3.2

        self.sky = self.ctx.program(
            vertex_shader="""#version 330
            in vec2 xy; out float vy;
            void main(){ gl_Position = vec4(xy,0.9999,1.0); vy = xy.y*0.5+0.5; }""",
            fragment_shader="""#version 330
            in float vy; out vec4 f;
            void main(){ vec3 top=vec3(0.02,0.03,0.07); vec3 bot=vec3(0.07,0.08,0.13);
                         f = vec4(mix(bot,top,vy),1.0); }""")
        self.sky_vbo = self.ctx.buffer(np.array([-1, -1, 3, -1, -1, 3], dtype="f4").tobytes())
        self.sky_vao = self.ctx.vertex_array(self.sky, [(self.sky_vbo, "2f", "xy")])

        self.prog = self.ctx.program(
            vertex_shader="""#version 330
            in vec3 in_pos; in vec3 in_norm;
            in vec3 off; in vec3 right; in vec3 up; in vec3 fwd; in vec3 color;
            uniform mat4 vp; uniform float scale;
            out vec3 v_norm; out vec3 v_color; out vec3 v_world;
            void main(){
              vec3 p = off + scale*(right*in_pos.x + up*in_pos.y + fwd*in_pos.z);
              gl_Position = vp*vec4(p,1.0);
              v_norm = right*in_norm.x + up*in_norm.y + fwd*in_norm.z;
              v_color = color; v_world = p;
            }""",
            fragment_shader="""#version 330
            in vec3 v_norm; in vec3 v_color; in vec3 v_world; out vec4 f_color;
            uniform vec3 light; uniform vec3 eye; uniform vec3 fogc; uniform float fog0; uniform float fog1;
            void main(){
              vec3 n = normalize(v_norm);
              vec3 vd = normalize(eye - v_world);
              float key = max(dot(n, normalize(light)), 0.0);
              float fill = max(dot(n, normalize(vec3(-0.4,-0.3,0.3))), 0.0)*0.3;
              float rim = pow(1.0-max(dot(n,vd),0.0), 3.0);
              vec3 col = v_color*(0.28 + 0.72*key + fill) + v_color*rim*0.7;
              float fog = clamp((length(v_world-eye)-fog0)/(fog1-fog0), 0.0, 1.0);
              f_color = vec4(mix(col, fogc, fog*0.8), 1.0);
            }""")

        self.line_prog = self.ctx.program(
            vertex_shader="""#version 330
            in vec3 in_pos; uniform mat4 vp; uniform vec3 eye; out float fogf;
            uniform float fog0; uniform float fog1;
            void main(){ gl_Position=vp*vec4(in_pos,1.0);
                         fogf = clamp((length(in_pos-eye)-fog0)/(fog1-fog0),0.0,1.0); }""",
            fragment_shader="""#version 330
            in float fogf; out vec4 f; uniform vec3 color; uniform vec3 fogc;
            void main(){ f = vec4(mix(color,fogc,fogf*0.9),1.0); }""")

        self.point_prog = self.ctx.program(
            vertex_shader="""#version 330
            in vec3 in_pos; uniform mat4 vp; uniform float psize;
            void main(){ gl_Position=vp*vec4(in_pos,1.0); gl_PointSize=psize; }""",
            fragment_shader="""#version 330
            out vec4 f; uniform vec3 color; uniform float alpha;
            void main(){ float r = length(gl_PointCoord-vec2(0.5))*2.0;
                         if(r>1.0) discard; f = vec4(color, (1.0-r)*(1.0-r)*alpha); }""")
        self.food_vbo = self.ctx.buffer(reserve=4 * 3 * 40000, dynamic=True)
        self.food_vao = self.ctx.vertex_array(self.point_prog, [(self.food_vbo, "3f", "in_pos")])
        self.shadow_vbo = self.ctx.buffer(reserve=4 * 3 * 200000, dynamic=True)
        self.shadow_vao = self.ctx.vertex_array(self.point_prog, [(self.shadow_vbo, "3f", "in_pos")])

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

    def render(self, pos, vel, color, cam_angle, cam_elev=0.45, radius_mult=1.6, food=None):
        s = self.world.size
        center = self.world.center
        radius = s * radius_mult
        eye = center + np.array([radius * np.cos(cam_angle), radius * np.sin(cam_angle), s * cam_elev])
        vp = perspective(45.0, self.w / self.h, 1.0, s * 6) @ look_at(eye, center, np.array([0.0, 0.0, 1.0]))
        vp_bytes = vp.T.astype("f4").tobytes()
        eye_f = tuple(float(x) for x in eye)

        self.fbo.use()
        self.ctx.clear(*BG, 1.0, depth=1.0)
        # sky gradient (no depth)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.sky_vao.render(mode=moderngl.TRIANGLES, vertices=3)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # arena lines (fogged)
        self.line_prog["vp"].write(vp_bytes)
        self.line_prog["eye"].value = eye_f
        self.line_prog["fogc"].value = BG
        self.line_prog["fog0"].value = self.fog0
        self.line_prog["fog1"].value = self.fog1
        self.line_prog["color"].value = (0.18, 0.22, 0.32)
        self.line_vao.render(mode=moderngl.LINES, vertices=self.n_lines)

        # soft ground shadows (project to z=0), normal blended
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.depth_mask = False
        ground = pos.copy().astype("f4"); ground[:, 2] = 0.2
        self.shadow_vbo.write(ground.tobytes())
        self.point_prog["vp"].write(vp_bytes)
        self.point_prog["color"].value = (0.0, 0.0, 0.0)
        self.point_prog["alpha"].value = 0.35
        self.point_prog["psize"].value = 7.0
        self.shadow_vao.render(mode=moderngl.POINTS, vertices=pos.shape[0])
        self.ctx.depth_mask = True
        self.ctx.disable(moderngl.BLEND)

        # creatures (opaque, lit, fogged)
        right, up, fwd = _basis(vel)
        inst = np.hstack([pos.astype("f4"), right, up, fwd, color.astype("f4")])
        self.inst_vbo.write(inst.astype("f4").tobytes())
        self.prog["vp"].write(vp_bytes)
        self.prog["scale"].value = self.scale
        self.prog["light"].value = (0.4, 0.5, 0.85)
        self.prog["eye"].value = eye_f
        self.prog["fogc"].value = BG
        self.prog["fog0"].value = self.fog0
        self.prog["fog1"].value = self.fog1
        self.vao.render(mode=moderngl.TRIANGLES, vertices=self.n_mesh, instances=pos.shape[0])

        # glowing food (additive)
        if food is not None and food.shape[0]:
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE
            self.ctx.depth_mask = False
            self.food_vbo.write(food.astype("f4").tobytes())
            self.point_prog["vp"].write(vp_bytes)
            self.point_prog["color"].value = (0.4, 1.0, 0.55)
            for size, a in ((16.0, 0.25), (7.0, 0.9)):       # halo + core glow
                self.point_prog["psize"].value = size
                self.point_prog["alpha"].value = a
                self.food_vao.render(mode=moderngl.POINTS, vertices=food.shape[0])
            self.ctx.depth_mask = True
            self.ctx.disable(moderngl.BLEND)

        return np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(self.h, self.w, 3)[::-1].copy()
