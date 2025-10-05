from imports import *
from mesh_renderer import MeshRenderer
from data import Data
import subprocess
import sys
import os

def deg_to_dms_str(value, is_lat=True, sec_prec=1):
    hemi = ('N' if value >= 0 else 'S') if is_lat else ('E' if value >= 0 else 'W')
    v = abs(float(value))
    d = int(v)
    m_float = (v - d) * 60.0
    m = int(m_float)
    s = (m_float - m) * 60.0
    s = round(s, sec_prec)
    if s >= 60.0:
        s = 0.0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    if sec_prec <= 0:
        return int(d)
    return int(d)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        self.win_w, self.win_h = 1280, 720
        pygame.display.set_mode((self.win_w, self.win_h), pygame.OPENGL | pygame.DOUBLEBUF)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)

        fbw, fbh = self.ctx.fbo.size
        self.ctx.viewport = (0, 0, fbw, fbh)

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True

        self.renderer = MeshRenderer(self.ctx, texture_path=r"Game\3D_Renderer\Assets\earth.jpg", fbw=fbw, fbh=fbh)

        self.yaw = 0.0
        self.pitch = 0.0
        self.distance = 2.5
        self.rotating = False
        self.last_mouse = None

        self.sphere_radius = 0.7
        self.model = matrix44.create_from_scale([self.sphere_radius]*3, dtype=np.float32)
        self.proj = matrix44.create_perspective_projection(60.0, fbw / fbh, 0.1, 100.0, dtype=np.float32)

    def view_matrix(self):
        cx = self.distance * np.cos(self.pitch) * np.cos(self.yaw)
        cy = self.distance * np.sin(self.pitch)
        cz = self.distance * np.cos(self.pitch) * np.sin(self.yaw)
        eye = np.array([cx, cy, cz], dtype=np.float32)
        target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return matrix44.create_look_at(eye, target, up, dtype=np.float32)

    def sync_viewport_projection(self):
        fbw, fbh = self.ctx.fbo.size
        self.ctx.viewport = (0, 0, fbw, fbh)
        self.proj = matrix44.create_perspective_projection(60.0, fbw / fbh, 0.1, 100.0, dtype=np.float32)
        if (fbw, fbh) != self.renderer.pick_size:
            self.renderer.resize_pick_fbo(fbw, fbh)

    def pick(self, mx, my):
        fbw, fbh = self.ctx.fbo.size
        px = int(mx * (fbw / self.win_w))
        py = int(my * (fbh / self.win_h))

        view = self.view_matrix()
        uv = self.renderer.pick_uv(self.model, view, self.proj, px, py)
        if uv is None:
            return None
        u, v = uv

        tw, th = self.renderer.tex_w, self.renderer.tex_h
        ix = int(np.floor(u * tw + 0.5)) % tw
        iy = int(np.clip(np.floor(v * th + 0.5), 0, th - 1))

        u_px = (ix + 0.5) / tw
        v_px = (iy + 0.5) / th
        lon_map = u_px * 360.0 - 180.0
        lat_map = 90.0 - v_px * 180.0

        lat_str = deg_to_dms_str(lat_map, is_lat=True, sec_prec=1)
        lon_str = deg_to_dms_str(lon_map, is_lat=False, sec_prec=1)
        return (lat_map, lon_map)  # Return floats for accuracy!

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_r:
                        self.yaw = 0.0
                        self.pitch = 0.0

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.rotating = True
                        self.last_mouse = event.pos
                    if event.button == 3:
                        gps_location = self.pick(*event.pos)
                        if gps_location is not None:
                            lat, lon = gps_location
                            print(f"Picked GPS Location: {lat}, {lon}")

                            # Fetch weather data synchronously
                            try:
                                Data.fetch_data(lat, lon)
                                print("Data fetched, launching main game...")

                                # Launch Game/main.py as subprocess
                                game_main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
                                subprocess.Popen([sys.executable, game_main_path])

                                self.running = False  # Close this renderer window
                            except Exception as e:
                                print(f"Error fetching data or launching game: {e}")

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.rotating = False
                    self.last_mouse = None

                if event.type == pygame.MOUSEMOTION and self.rotating:
                    x, y = event.pos
                    lx, ly = self.last_mouse if self.last_mouse else (x, y)
                    dx = x - lx
                    dy = y - ly
                    self.yaw += dx * 0.005
                    self.pitch += dy * 0.005
                    self.pitch = float(np.clip(self.pitch, -np.pi / 2 + 0.01, np.pi / 2 - 0.01))
                    self.last_mouse = (x, y)

            self.sync_viewport_projection()
            self.ctx.clear(0.05, 0.06, 0.08, 1.0, depth=1.0)
            view = self.view_matrix()
            self.renderer.draw(self.model, view, self.proj)
            pygame.display.flip()
            self.clock.tick(self.fps)

if __name__ == "__main__":
    Game().run()