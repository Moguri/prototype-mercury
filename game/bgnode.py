import panda3d.core as p3d

_BG_VERT = """
#version 130

out vec2 texcoord;

const vec4 positions[4] = vec4[4](
    vec4(-1, -1, 0, 1),
    vec4( 1, -1, 0, 1),
    vec4(-1,  1, 0, 1),
    vec4( 1,  1, 0, 1)
);

const vec2 texcoords[4] = vec2[4](
    vec2(0, 0),
    vec2(1, 0),
    vec2(0, 1),
    vec2(1, 1)
);

void main() {
    gl_Position = positions[gl_VertexID];
    texcoord = texcoords[gl_VertexID];
}
"""

_BG_FRAG = """
#version 130

uniform sampler2D tex;
uniform float exposure_inv;
in vec2 texcoord;

out vec4 color;

void main() {
    vec4 texcolor = texture2D(tex, texcoord);
    color = vec4(texcolor.rgb * exposure_inv, texcolor.a);
}
"""

def generate(parent=None, texture=None, foreground=False):
    bgnp = p3d.NodePath(p3d.CardMaker('bgimg').generate())
    bgnp.set_shader(p3d.Shader.make(p3d.Shader.SL_GLSL, _BG_VERT, _BG_FRAG))
    bgnp.set_shader_input('exposure_inv', 1.0 / base.render_pipeline.exposure)
    bgnp.set_bin('fixed' if foreground else 'background', 0)
    bgnp.set_depth_test(False)
    bgnp.set_depth_write(False)
    bgnp.node().set_bounds(p3d.OmniBoundingVolume())
    bgnp.node().set_final(True)

    if parent is not None:
        bgnp.reparent_to(parent)

    if texture is not None:
        suffix = 'fg' if foreground else 'bg'
        tex = base.loader.load_texture(f'backgrounds/{texture}{suffix}.png')
        if tex.num_components == 4:
            bgnp.set_transparency(p3d.TransparencyAttrib.M_alpha)
            tex.set_format(p3d.Texture.F_srgb_alpha)
        else:
            tex.set_format(p3d.Texture.F_srgb)
    else:
        tex = p3d.Texture()
    bgnp.set_shader_input('tex', tex)

    return bgnp
