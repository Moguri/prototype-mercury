import panda3d.core as p3d

class CommonLighting:
    def __init__(self, rendernp, targetpos=None, scene=None, calc_shadow_bounds=True):
        self.rendernp = rendernp

        targetpos = targetpos or p3d.LVector3(0, 0, 0)

        # Lights
        self.key_light = p3d.DirectionalLight('sun')
        self.key_light.color_temperature = 6000
        self.key_lightnp = rendernp.attach_new_node(self.key_light)
        self.key_lightnp.set_pos(targetpos + (0, -15, 15))
        self.key_lightnp.look_at(targetpos)
        base.render.set_light(self.key_lightnp)

        self.fill_light = p3d.DirectionalLight('fill light')
        self.fill_light.color_temperature = 4800
        self.fill_light.color = self.fill_light.color * 0.5
        self.fill_lightnp = rendernp.attach_new_node(self.fill_light)
        self.fill_lightnp.set_pos(targetpos + (-20, 0, 10))
        self.fill_lightnp.look_at(targetpos)
        base.render.set_light(self.fill_lightnp)

        self.back_light = p3d.DirectionalLight('fill light')
        self.back_light.color_temperature = 4800
        self.back_light.color = self.back_light.color * 0.25
        self.back_lightnp = rendernp.attach_new_node(self.back_light)
        self.back_lightnp.set_pos(20, 20, 0)
        self.back_lightnp.look_at(targetpos)
        base.render.set_light(self.back_lightnp)

        # Shadows
        self.key_light.set_shadow_caster(True, 512, 512)
        if calc_shadow_bounds:
            self.recalc_bounds(scene)


    def recalc_bounds(self, scene=None):
        scene = scene or self.rendernp
        light_lens = self.key_light.get_lens()
        bounds = scene.get_tight_bounds(self.key_lightnp)
        if bounds:
            bmin, bmax = bounds
            light_lens.set_film_offset((bmin.xz + bmax.xz) * 0.5)
            light_lens.set_film_size(bmax.xz - bmin.xz)
            light_lens.set_near_far(bmin.y, bmax.y)
        else:
            scene.ls()
            print('Warning: Unable to calculate scene bounds for optimized shadows')
            light_lens.set_film_size(100, 100)
