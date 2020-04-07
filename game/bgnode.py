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
    color = vec4(texture2D(tex, texcoord).rgb, 1.0) * exposure_inv;
}
"""

def generate(parent=None):
    bgnp = p3d.NodePath(p3d.CardMaker('bgimg').generate())
    bgnp.set_shader(p3d.Shader.make(p3d.Shader.SL_GLSL, _BG_VERT, _BG_FRAG))
    bgnp.set_shader_input('exposure_inv', 1.0 / base.render_pipeline.exposure)
    bgnp.set_bin('background', 0)
    bgnp.set_depth_test(False)
    bgnp.set_depth_write(False)

    if parent is not None:
        bgnp.reparent_to(parent)

    return bgnp
