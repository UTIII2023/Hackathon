from imports import *

class MeshRenderer:
    def __init__(self, ctx, texture_path, fbw, fbh):
        self.ctx = ctx

        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec3 in_pos;
                in vec3 in_norm;
                in vec2 in_uv;
                uniform mat4 uProj;
                uniform mat4 uView;
                uniform mat4 uModel;
                out vec3 v_norm;
                out vec2 v_uv;
                void main() {
                    gl_Position = uProj * uView * uModel * vec4(in_pos, 1.0);
                    v_norm = mat3(uModel) * in_norm;
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                in vec3 v_norm;
                in vec2 v_uv;
                uniform sampler2D uTex;
                out vec4 f_color;
                void main() {
                    vec3 N = normalize(v_norm);
                    vec3 L = normalize(vec3(0.7, 1.0, 0.5));
                    float lit = max(dot(N, L), 0.25);
                    vec3 tex = texture(uTex, v_uv).rgb;
                    f_color = vec4(tex * lit, 1.0);
                }
            """
        )

        self.pick_prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec3 in_pos;
                in vec2 in_uv;
                uniform mat4 uProj;
                uniform mat4 uView;
                uniform mat4 uModel;
                out vec2 v_uv;
                void main() {
                    gl_Position = uProj * uView * uModel * vec4(in_pos, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                in vec2 v_uv;
                out vec4 out_color;
                void main() {
                    out_color = vec4(v_uv, 0.0, 1.0);
                }
            """
        )

        self.texture = self.load_texture(texture_path)
        self.vbo, self.pick_vbo, self.ibo, self.render_vao, self.pick_vao, self.index_count = self.build_uv_sphere(lat=64, lon=128)

        self.create_pick_fbo(fbw, fbh)

    def create_pick_fbo(self, fbw, fbh):
        self.pick_w, self.pick_h = fbw, fbh
        # 32-bit float texture with 3 channels to store (u, v, padding)
        self.pick_tex = self.ctx.texture((fbw, fbh), 3, dtype='f4')
        self.pick_depth = self.ctx.depth_renderbuffer((fbw, fbh))
        self.pick_fbo = self.ctx.framebuffer(color_attachments=[self.pick_tex], depth_attachment=self.pick_depth)
        self.pick_size = (fbw, fbh)

    def resize_pick_fbo(self, fbw, fbh):
        self.pick_tex.release()
        self.pick_depth.release()
        self.pick_fbo.release()
        self.create_pick_fbo(fbw, fbh)

    def load_texture(self, path):
        img = Image.open(path).convert("RGB")
        self.tex_w, self.tex_h = img.size
        self.tex_np = np.array(img, dtype=np.uint8)
        tex = self.ctx.texture(img.size, 3, img.tobytes())
        tex.build_mipmaps()
        tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        tex.repeat_x = True
        tex.repeat_y = True
        return tex

    def uv_to_pixel(self, u, v):
        x = int(np.clip(u * (self.tex_w - 1), 0, self.tex_w - 1))
        y = int(np.clip(v * (self.tex_h - 1), 0, self.tex_h - 1))
        return x, y

    def pixel_to_uv(self, ix, iy):
        u = (ix + 0.5) / self.tex_w
        v = (iy + 0.5) / self.tex_h
        return float(u % 1.0), float(v % 1.0)

    def uv_to_latlon(self, u, v):
        lon = u * 360.0 - 180.0
        lat = 90.0 - v * 180.0
        return lat, lon

    def pixel_to_latlon(self, ix, iy):
        u, v = self.pixel_to_uv(ix, iy)
        return self.uv_to_latlon(u, v)

    def texel_from_uv(self, u, v):
        x, y = self.uv_to_pixel(u, v)
        rgb = tuple(int(c) for c in self.tex_np[y, x])
        return x, y, rgb

    def build_uv_sphere(self, lat=32, lon=64):
        verts = []
        pick_verts = []
        inds = []
        for i in range(lat + 1):
            v = i / lat
            phi = (v - 0.5) * np.pi
            cphi = np.cos(phi)
            sphi = np.sin(phi)
            for j in range(lon + 1):
                u = j / lon
                th = u * 2.0 * np.pi
                cth = np.cos(th)
                sth = np.sin(th)
                x = cphi * cth
                y = sphi
                z = cphi * sth
                nx, ny, nz = x, y, z
                uu = u
                vv = 1.0 - v
                verts.extend([x, y, z, nx, ny, nz, uu, vv])
                pick_verts.extend([x, y, z, uu, vv])

        for i in range(lat):
            for j in range(lon):
                i0 = i * (lon + 1) + j
                i1 = i0 + 1
                i2 = i0 + (lon + 1)
                i3 = i2 + 1
                inds.extend([i0, i1, i2, i1, i3, i2])

        vbo = self.ctx.buffer(np.array(verts, dtype=np.float32).tobytes())
        pick_vbo = self.ctx.buffer(np.array(pick_verts, dtype=np.float32).tobytes())
        ibo = self.ctx.buffer(np.array(inds, dtype=np.uint32).tobytes())

        render_vao = self.ctx.vertex_array(
            self.prog,
            [(vbo, "3f 3f 2f", "in_pos", "in_norm", "in_uv")],
            index_buffer=ibo,
            index_element_size=4
        )
        pick_vao = self.ctx.vertex_array(
            self.pick_prog,
            [(pick_vbo, "3f 2f", "in_pos", "in_uv")],
            index_buffer=ibo,
            index_element_size=4
        )
        return vbo, pick_vbo, ibo, render_vao, pick_vao, len(inds)

    def draw(self, model, view, proj):
        self.prog["uProj"].write(proj.astype(np.float32).tobytes())
        self.prog["uView"].write(view.astype(np.float32).tobytes())
        self.prog["uModel"].write(model.astype(np.float32).tobytes())
        self.texture.use(location=0)
        self.prog["uTex"].value = 0
        self.render_vao.render(moderngl.TRIANGLES)

    def pick_uv(self, model, view, proj, px, py):
        self.pick_fbo.use()
        self.ctx.viewport = (0, 0, self.pick_w, self.pick_h)
        self.ctx.clear(0.0, 0.0, 0.0, 0.0, depth=1.0)

        self.pick_prog["uProj"].write(proj.astype(np.float32).tobytes())
        self.pick_prog["uView"].write(view.astype(np.float32).tobytes())
        self.pick_prog["uModel"].write(model.astype(np.float32).tobytes())
        self.pick_vao.render(moderngl.TRIANGLES)

        rx = int(np.clip(px, 0, self.pick_w - 1))
        ry = int(np.clip(self.pick_h - 1 - py, 0, self.pick_h - 1))

        data = self.pick_fbo.read(components=3, dtype='f4', viewport=(rx, ry, 1, 1))
        uv = np.frombuffer(data, dtype=np.float32)

        self.ctx.screen.use()
        if uv.size < 2:
            return None
        u = float(np.clip(uv[0], 0.0, 1.0))
        v = float(np.clip(uv[1], 0.0, 1.0))
        return u, v